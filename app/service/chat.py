# app/service/chat.py
import uuid
from typing import List, Tuple

from fastapi import Depends
from app.models.chat import ChatHistoryModel
from app.schemas.chat import ChatRequestSchema
from app.core.database import get_async_db
from app.core.config import get_chat_response
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from sqlalchemy import nullslast

import re

from app.models.hospitals import HospitalModel
from app.models.doctors import DoctorModel
from app.models.locations import RegionModel, DistrictModel

SYSTEM_PROMPT = (
    "You are a professional medical assistant. "
    "You must *only* answer medical questions, and refuse any non-medical request."
)
STYLE_PROMPT = (
    "Respond in the user's language using one concise, natural paragraph. "
    "Do not use line breaks, bullet points, or the '@' character. "
    "When recommending a doctor, clearly state their specialty and full name, "
    "and mention the hospital naturally in the sentence, without using separate labels "
    "like 'Kasalxona:' or 'Manzil:'. "
    "Make the recommendation feel like friendly advice rather than a data list."
)


class ChatService:
    def __init__(self, db: AsyncSession = Depends(get_async_db)):
        self.db = db

    async def _build_directory_context(
        self,
        max_doctors: int = 200,
        max_chars: int = 2200,
    ) -> str:
        """
        A compact, token-friendly directory of doctors with hospital, district, region, rating.
        """
        stmt = (
            select(
                DoctorModel.first_name,
                DoctorModel.last_name,
                DoctorModel.professional,
                HospitalModel.name.label("hospital_name"),
                DistrictModel.name.label("district_name"),
                RegionModel.name.label("region_name"),
                DoctorModel.reyting,
            )
            .join(HospitalModel, DoctorModel.hospital_id == HospitalModel.id)
            .join(DistrictModel, HospitalModel.district_id == DistrictModel.id)
            .join(RegionModel, HospitalModel.region_id == RegionModel.id)
            .order_by(
                RegionModel.name.asc(),
                DistrictModel.name.asc(),
                nullslast(DoctorModel.reyting.desc()),
                DoctorModel.last_name.asc(),
                DoctorModel.first_name.asc(),
            )
            .limit(max_doctors)
        )

        res = await self.db.execute(stmt)
        rows = res.fetchall()

        if not rows:
            return (
                "Local directory: none found. If no local matches exist, recommend a general practitioner."
            )

        # keep simple lines; the model will cite from these
        lines: List[str] = []
        for fn, ln, spec, hosp, district, region, rating in rows:
            spec = spec or "Pediatriya"  # default if missing
            rating_str = f", reyting {rating:.1f}" if isinstance(rating, (int, float)) and rating is not None else ""
            # No '@' anywhere. Include district and region.
            lines.append(
                f"Dr. {fn} {ln}, {spec}, {hosp}, {district} tumani, {region} viloyati{rating_str}."
            )

        out = "Local doctors and hospitals (use when recommending a specialist): " + " ".join(lines)
        if len(out) > max_chars:
            out = out[: max_chars - 20].rstrip() + " …"
        return (
            out
            + " Guidance: pick the most relevant specialist for the user’s symptoms; if unclear, suggest pediatriya/terapevt."
        )

    @staticmethod
    def _normalize_text(s: str) -> str:
        """
        Remove '@', collapse whitespace/newlines to single spaces, trim.
        """
        s = s.replace("@", " ")
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    async def send(
        self,
        payload: ChatRequestSchema,
        conversation_id: uuid.UUID | None,
        user_id: uuid.UUID,
    ) -> Tuple[str, uuid.UUID]:
        if conversation_id is None:
            conversation_id = uuid.uuid4()

        result = await self.db.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.conversation_id == conversation_id)
            .order_by(ChatHistoryModel.created_at)
        )
        past = result.scalars().all()

        directory_context = await self._build_directory_context()
        messages: List[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": STYLE_PROMPT},      # ✅ enforce flat paragraph & no '@'
            {"role": "system", "content": directory_context}, # ✅ add directory w/ district & region
        ]

        for row in past:
            messages.append({"role": "user", "content": row.prompt})
            messages.append({"role": "assistant", "content": row.response})

        for m in payload.messages:
            messages.append({"role": "user", "content": m.content})

        raw_reply = await get_chat_response(messages)
        reply = self._normalize_text(raw_reply)   # ✅ sanitize just in case

        new_row = ChatHistoryModel(
            user_id=user_id,
            conversation_id=conversation_id,
            prompt=payload.messages[-1].content,
            response=reply,
        )
        self.db.add(new_row)
        await self.db.commit()
        return reply, conversation_id


    async def list(self, user_id: uuid.UUID) -> List[ChatHistoryModel]:
        result = await self.db.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.user_id == user_id)
            .order_by(ChatHistoryModel.created_at)
        )
        return result.scalars().all()

    async def get(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> List[ChatHistoryModel]:
        result = await self.db.execute(
            select(ChatHistoryModel)
            .where(
                ChatHistoryModel.user_id == user_id,
                ChatHistoryModel.conversation_id == conversation_id,
            )
            .order_by(ChatHistoryModel.created_at)
        )
        rows = result.scalars().all()
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        return rows

    async def delete(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> None:
        # ensure it exists
        result = await self.db.execute(
            select(ChatHistoryModel.id).where(
                ChatHistoryModel.user_id == user_id,
                ChatHistoryModel.conversation_id == conversation_id,
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # delete all rows in that convo
        await self.db.execute(
            delete(ChatHistoryModel).where(
                ChatHistoryModel.user_id == user_id,
                ChatHistoryModel.conversation_id == conversation_id,
            )
        )
        await self.db.commit()

    async def list_conversation_threads(self, user_id: uuid.UUID) -> List[dict]:
        """
        Return a list of dicts:
          {
            "conversation_id": UUID,
            "messages": [
              {"prompt": str, "response": str, "created_at": datetime}, ...
            ]
          }
        Ordered by the last message timestamp descending.
        """
        res = await self.db.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.user_id == user_id)
            .order_by(ChatHistoryModel.created_at)
        )
        rows = res.scalars().all()

        # group by conversation_id
        threads: dict[uuid.UUID, list[ChatHistoryModel]] = {}
        for r in rows:
            threads.setdefault(r.conversation_id, []).append(r)

        result = []
        for convo_id, msgs in threads.items():
            # msgs already in ascending created_at
            result.append(
                {
                    "conversation_id": convo_id,
                    "messages": [
                        {
                            "prompt": m.prompt,
                            "response": m.response,
                            "created_at": m.created_at,
                        }
                        for m in msgs
                    ],
                }
            )

        # sort threads by last message time desc
        result.sort(key=lambda t: t["messages"][-1]["created_at"], reverse=True)
        return result
