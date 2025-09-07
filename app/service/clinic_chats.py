import uuid
from datetime import datetime
from typing import List, Optional, Dict, Set, Any

from fastapi import HTTPException, status
from starlette.websockets import WebSocket  # type only
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hospitals import HospitalModel
from app.models.users import UserModel
from app.models.clinic_chats import ClinicChatModel, ClinicChatMessageModel


# Role → name mapping
ROLE_MAP: Dict[uuid.UUID, str] = {
    uuid.UUID("8497eb6c-0eea-40e7-8467-f8e393f56811"): "user",
    uuid.UUID("8497eb6c-0eea-40e7-8467-f8e393f56822"): "hospital_admin",
    uuid.UUID("8497eb6c-0eea-40e7-8467-f8e393f56833"): "super_admin",
    uuid.UUID("8497eb6c-0eea-40e7-8467-f8e393f56844"): "doctor",
}


class _ConnectionManager:
    """
    Very small in-memory room manager.
    Rooms are keyed by thread_id (UUID) -> set[WebSocket]
    """
    def __init__(self) -> None:
        self.rooms: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect(self, thread_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(thread_id, set()).add(websocket)

    def disconnect(self, thread_id: uuid.UUID, websocket: WebSocket) -> None:
        try:
            conns = self.rooms.get(thread_id)
            if conns and websocket in conns:
                conns.remove(websocket)
            if conns is not None and len(conns) == 0:
                self.rooms.pop(thread_id, None)
        except Exception:
            # Ignore disconnect errors
            pass

    async def broadcast(self, thread_id: uuid.UUID, data: Any) -> None:
        conns = self.rooms.get(thread_id)
        if not conns:
            return
        dead: List[WebSocket] = []
        for ws in list(conns):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(thread_id, ws)


class ClinicChatService:
    """
    Handles DB and also owns a singleton ConnectionManager for WS broadcasts.
    """
    _manager = _ConnectionManager()

    @classmethod
    def manager(cls) -> _ConnectionManager:
        return cls._manager

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- helpers ----------
    async def _ensure_hospital(self, hospital_id: uuid.UUID) -> HospitalModel:
        hospital = await self.db.get(HospitalModel, hospital_id)
        if not hospital:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Hospital not found")
        return hospital

    @staticmethod
    def _is_hospital_admin_for(current_user: UserModel, hospital: HospitalModel) -> bool:
        if not current_user or not hospital or not hospital.admin_id:
            return False
        if current_user.role_id not in ROLE_MAP:  # role not recognized
            return False
        return str(hospital.admin_id) == str(current_user.id)

    def _get_sender_role(self, current_user: UserModel) -> str:
        """Map role_id to human-readable sender_type string."""
        return ROLE_MAP.get(current_user.role_id, "unknown")

    async def _get_or_create_thread(
        self, *, hospital_id: uuid.UUID, user_id: uuid.UUID
    ) -> ClinicChatModel:
        stmt = (
            select(ClinicChatModel)
            .where(
                ClinicChatModel.hospital_id == hospital_id,
                ClinicChatModel.user_id == user_id,
            )
            .options(selectinload(ClinicChatModel.messages))
        )
        res = await self.db.execute(stmt)
        thread = res.scalars().first()
        if thread:
            return thread

        thread = ClinicChatModel(
            hospital_id=hospital_id,
            user_id=user_id,
            modified_at=datetime.utcnow(),
        )
        self.db.add(thread)
        await self.db.flush()
        await self.db.refresh(thread)
        return thread

    @staticmethod
    def _serialize_message(m: ClinicChatMessageModel) -> dict:
        return {
            "id": str(m.id),
            "sender_type": m.sender_type,
            "text": m.text,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }

    # ---------- reads ----------
    async def list_threads_for_user(self, *, user: UserModel) -> List[ClinicChatModel]:
        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.user_id == user.id)
            .options(selectinload(ClinicChatModel.messages))
            .order_by(ClinicChatModel.modified_at.desc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def list_threads_for_hospital_admin(
        self, *, current_user: UserModel
    ) -> List[ClinicChatModel]:
        stmt_h = select(HospitalModel).where(HospitalModel.admin_id == current_user.id)
        hospital = (await self.db.execute(stmt_h)).scalars().first()
        if not hospital:
            return []

        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.hospital_id == hospital.id)
            .options(selectinload(ClinicChatModel.messages))
            .order_by(ClinicChatModel.modified_at.desc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def get_thread(
        self, *, hospital_id: uuid.UUID, user_id: uuid.UUID
    ) -> ClinicChatModel:
        stmt = (
            select(ClinicChatModel)
            .where(
                ClinicChatModel.hospital_id == hospital_id,
                ClinicChatModel.user_id == user_id,
            )
            .options(selectinload(ClinicChatModel.messages))
        )
        res = await self.db.execute(stmt)
        thread = res.scalars().first()
        if not thread:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
        return thread

    async def get_thread_by_id(self, *, thread_id: uuid.UUID) -> ClinicChatModel:
        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.id == thread_id)
            .options(selectinload(ClinicChatModel.messages))
        )
        res = await self.db.execute(stmt)
        thread = res.scalars().first()
        if not thread:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
        return thread

    # ---------- writes ----------
    async def send_message_as_user(
        self,
        *,
        hospital_id: uuid.UUID,
        current_user: UserModel,
        text: str,
        thread_id: Optional[uuid.UUID] = None,
    ) -> ClinicChatModel:
        if thread_id:
            thread = await self.get_thread_by_id(thread_id=thread_id)
            if str(thread.user_id) != str(current_user.id):
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Thread doesn't belong to the current user")
            if str(thread.hospital_id) != str(hospital_id):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Thread does not belong to the provided hospital")
        else:
            await self._ensure_hospital(hospital_id)
            thread = await self._get_or_create_thread(hospital_id=hospital_id, user_id=current_user.id)

        msg = ClinicChatMessageModel(
            thread_id=thread.id,
            sender_type=self._get_sender_role(current_user),
            text=text,
            created_at=datetime.utcnow(),
        )
        self.db.add(msg)
        thread.modified_at = datetime.utcnow()
        await self.db.flush()

        await self._manager.broadcast(
            thread.id,
            {
                "event": "message.created",
                "thread_id": str(thread.id),
                "message": self._serialize_message(msg),
            },
        )

        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.id == thread.id)
            .options(selectinload(ClinicChatModel.messages))
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def send_message_as_hospital(
        self, *, hospital_id: uuid.UUID, user_id: uuid.UUID, current_user: UserModel, text: str
    ) -> ClinicChatModel:
        hospital = await self._ensure_hospital(hospital_id)
        if not self._is_hospital_admin_for(current_user, hospital):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not hospital admin for this hospital")

        stmt = (
            select(ClinicChatModel)
            .where(
                ClinicChatModel.hospital_id == hospital.id,
                ClinicChatModel.user_id == user_id,
            )
            .options(selectinload(ClinicChatModel.messages))
        )
        res = await self.db.execute(stmt)
        thread = res.scalars().first()
        if not thread:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found (hospital cannot start the chat)")

        msg = ClinicChatMessageModel(
            thread_id=thread.id,
            sender_type=self._get_sender_role(current_user),
            text=text,
            created_at=datetime.utcnow(),
        )
        self.db.add(msg)
        thread.modified_at = datetime.utcnow()
        await self.db.flush()

        await self._manager.broadcast(
            thread.id,
            {
                "event": "message.created",
                "thread_id": str(thread.id),
                "message": self._serialize_message(msg),
            },
        )

        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.id == thread.id)
            .options(selectinload(ClinicChatModel.messages))
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def send_message_as_hospital_by_thread(
        self, *, thread_id: uuid.UUID, current_user: UserModel, text: str
    ) -> ClinicChatModel:
        thread = await self.get_thread_by_id(thread_id=thread_id)
        hospital = await self._ensure_hospital(thread.hospital_id)
        if not self._is_hospital_admin_for(current_user, hospital):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not hospital admin for this hospital")

        msg = ClinicChatMessageModel(
            thread_id=thread.id,
            sender_type=self._get_sender_role(current_user),
            text=text,
            created_at=datetime.utcnow(),
        )
        self.db.add(msg)
        thread.modified_at = datetime.utcnow()
        await self.db.flush()

        await self._manager.broadcast(
            thread.id,
            {
                "event": "message.created",
                "thread_id": str(thread.id),
                "message": self._serialize_message(msg),
            },
        )

        stmt = (
            select(ClinicChatModel)
            .where(ClinicChatModel.id == thread.id)
            .options(selectinload(ClinicChatModel.messages))
        )
        return (await self.db.execute(stmt)).scalars().first()
