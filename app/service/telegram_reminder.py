import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- your project imports ---
from app.core.database import get_async_db
from app.models.users import UserModel
from app.models.medicine_reminder import MedicineReminderModel

# ---------------- CONFIG ----------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN env var is required")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
scheduler.start()

# ---------------- SERVICE ----------------
class MedicineReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_reminder(self, user_id: uuid.UUID, medicine_name: str, remind_time):
        reminder = MedicineReminderModel(
            user_id=user_id,
            medicine_name=medicine_name,
            remind_time=remind_time,
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def list_reminders(self, user_id: uuid.UUID):
        res = await self.db.execute(
            select(MedicineReminderModel).where(MedicineReminderModel.user_id == user_id)
        )
        return res.scalars().all()

# ---------------- KEYBOARDS ----------------
def make_main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Eslatma qo‘shish")
    kb.button(text="📋 Eslatmalarim")
    kb.button(text="🚪 Chiqish")
    kb.adjust(1, 1, 1)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False)

def make_contact_keyboard() -> ReplyKeyboardMarkup:
    # Works in private chats only
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="📱 Kontaktni ulashish", request_contact=True))
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)

MAIN_KB = make_main_keyboard()

# ---------------- STATE (in-memory) ----------------
# Maps Telegram user -> UserModel.id (string UUID)
user_sessions: Dict[int, str] = {}
# login flow state per user
login_state: Dict[int, Dict] = {}
#  structure:
#  { telegram_user_id: {"step": "await_contact" | "await_password", "phone": "+998..."} }

# ---------------- HELPERS ----------------
async def verify_login(phone: str, password: str) -> Optional[UserModel]:
    async for db in get_async_db():
        stmt = select(UserModel).where(UserModel.phone_number == phone)
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user and pwd_context.verify(password, user.hashed_password):
            return user
        return None

# ---------------- HANDLERS ----------------
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # ask for contact first
    login_state[message.from_user.id] = {"step": "await_contact"}
    await message.answer(
        "👋 Assalomu alaykum!\n\nIltimos, pastdagi tugma orqali telefon raqamingizni ulashing:",
        reply_markup=make_contact_keyboard()
    )

@dp.message(Command("menu"))
async def show_menu(message: types.Message):
    await message.answer("📎 Menu", reply_markup=MAIN_KB)

@dp.message(Command("login"))
async def login_start(message: types.Message):
    # allow /login to restart the flow
    login_state[message.from_user.id] = {"step": "await_contact"}
    await message.answer(
        "📱 Telefon raqamingizni ulashing:",
        reply_markup=make_contact_keyboard()
    )

# === 1) CONTACT HANDLER (fires when user taps “Share contact”) ===
# Note: Telegram sends a Contact payload; in aiogram v3 you can filter by F.contact
@dp.message(F.contact)
async def got_contact(message: types.Message):
    state = login_state.get(message.from_user.id)
    if not state or state.get("step") != "await_contact":
        # ignore stray contacts
        await message.answer("ℹ️ Iltimos, /login buyrug‘idan foydalaning.")
        return

    # Only works in private chats per Telegram docs; this carries the user's phone.  :contentReference[oaicite:3]{index=3}
    contact: types.Contact = message.contact
    # choose the best phone source
    phone = contact.phone_number

    # move to password step
    login_state[message.from_user.id] = {"step": "await_password", "phone": phone}
    await message.answer("🔑 Endi parolingizni yuboring:", reply_markup=ReplyKeyboardRemove())

# === 2) SPECIFIC BUTTON HANDLERS (placed BEFORE the catch-all F.text) ===
@dp.message(F.text == "➕ Eslatma qo‘shish")
async def add_reminder_step(message: types.Message):
    if message.from_user.id not in user_sessions:
        await message.answer("❌ Iltimos, avval /login orqali tizimga kiring.")
        return
    await message.answer("⌚ Shakl: `08:30 Paratsetamol`\n\nSoat + dori nomini yuboring.", parse_mode="Markdown")

@dp.message(F.text == "📋 Eslatmalarim")
async def list_reminders(message: types.Message):
    if message.from_user.id not in user_sessions:
        await message.answer("❌ Iltimos, avval /login orqali tizimga kiring.")
        return
    tg_uid = message.from_user.id
    try:
        user_id = uuid.UUID(user_sessions[tg_uid])
    except Exception:
        await message.answer("⚠️ Sessiya xatosi. /login qayta urinib ko‘ring.")
        return

    async for db in get_async_db():
        service = MedicineReminderService(db)
        reminders = await service.list_reminders(user_id)

    if not reminders:
        await message.answer("ℹ️ Sizda hech qanday eslatma yo‘q.", reply_markup=MAIN_KB)
        return

    def fmt_time(t) -> str:
        return getattr(t, "strftime", lambda *_: str(t))("%H:%M")

    text_lines = [f"⏰ {fmt_time(r.remind_time)} – {r.medicine_name}" for r in reminders]
    await message.answer("📋 Eslatmalaringiz:\n\n" + "\n".join(text_lines), reply_markup=MAIN_KB)

@dp.message(F.text == "🚪 Chiqish")
async def logout_cmd(message: types.Message):
    user_sessions.pop(message.from_user.id, None)
    login_state.pop(message.from_user.id, None)
    await message.answer("🚪 Tizimdan chiqdingiz.", reply_markup=ReplyKeyboardRemove())

# === 3) SAVE REMINDER (specific pattern) ===
@dp.message(F.text.regexp(r"^\d{2}:\d{2}\s+.+$"))
async def save_reminder(message: types.Message):
    if message.from_user.id not in user_sessions:
        await message.answer("❌ Iltimos, avval /login orqali tizimga kiring.", reply_markup=MAIN_KB)
        return

    tg_uid = message.from_user.id
    try:
        user_id = uuid.UUID(user_sessions[tg_uid])
    except Exception:
        await message.answer("⚠️ Sessiya xatosi. /login qayta urinib ko‘ring.")
        return

    try:
        time_str, medicine_name = message.text.split(maxsplit=1)
        remind_time = datetime.strptime(time_str, "%H:%M").time()

        async for db in get_async_db():
            service = MedicineReminderService(db)
            await service.add_reminder(
                user_id=user_id,
                medicine_name=medicine_name,
                remind_time=remind_time,
            )

        async def send_reminder(chat_id: int, text: str):
            await bot.send_message(chat_id, f"⏰ Eslatma: {text} ichish vaqti keldi!")

        scheduler.add_job(
            send_reminder,
            "cron",
            args=[message.chat.id, medicine_name],
            hour=remind_time.hour,
            minute=remind_time.minute,
        )

        await message.answer(f"✅ {time_str} uchun eslatma qo‘shildi: {medicine_name}", reply_markup=MAIN_KB)
    except Exception:
        await message.answer("❌ Foydalanish: 08:30 Paratsetamol", reply_markup=MAIN_KB)

# === 4) PASSWORD HANDLER (catch-all text BUT ONLY DURING password step) ===
@dp.message(F.text.func(lambda _t: True))
async def maybe_password(message: types.Message):
    """This runs only when we explicitly are in 'await_password' step."""
    state = login_state.get(message.from_user.id)
    if not state or state.get("step") != "await_password":
        # Not our case; do nothing and let user press buttons/commands.
        return

    phone = state["phone"]
    password = message.text
    user = await verify_login(phone, password)
    login_state.pop(message.from_user.id, None)

    if user:
        user_sessions[message.from_user.id] = str(user.id)
        await message.answer("✅ Muvaffaqiyatli kirdingiz!", reply_markup=MAIN_KB)
    else:
        await message.answer("❌ Telefon raqam yoki parol noto‘g‘ri!", reply_markup=MAIN_KB)

# --- runner ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
