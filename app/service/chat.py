# app/service/chat.py
import uuid
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.models.chat import ChatHistoryModel
from app.schemas.chat import ChatRequestSchema
from app.core.database import get_async_db
from app.core.config import get_chat_response
from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import List

SYSTEM_PROMPT = (
    "You are a professional medical assistant. "
    "You must *only* answer medical questions, and refuse any non-medical request."
)


class ChatService:
    def __init__(self, db: AsyncSession = Depends(get_async_db)):
        self.db = db

    async def send(
        self, payload: ChatRequestSchema, conversation_id: uuid.UUID | None, user_id: uuid.UUID
    ) -> Tuple[str, uuid.UUID]:
        # 1️⃣ Create a new ID if none given
        if conversation_id is None:
            conversation_id = uuid.uuid4()

        # 2️⃣ Load prior rounds
        result = await self.db.execute(
            select(ChatHistoryModel)
            .where(ChatHistoryModel.conversation_id == conversation_id)
            .order_by(ChatHistoryModel.created_at)
        )
        past = result.scalars().all()

        # 3️⃣ Build messages, starting with your static system prompt
        messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for row in past:
            messages.append({"role": "user", "content": row.prompt})
            messages.append({"role": "assistant", "content": row.response})

        # 4️⃣ Append each incoming payload message as a user message
        for m in payload.messages:
            messages.append({"role": "user", "content": m.content})

        # 5️⃣ Call OpenAI
        reply = await get_chat_response(messages)

        # 6️⃣ Persist this round
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
            select(ChatHistoryModel.id)
            .where(
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
            delete(ChatHistoryModel)
            .where(
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
            result.append({
                "conversation_id": convo_id,
                "messages": [
                    {"prompt": m.prompt, "response": m.response, "created_at": m.created_at}
                    for m in msgs
                ]
            })

        # sort threads by last message time desc
        result.sort(key=lambda t: t["messages"][-1]["created_at"], reverse=True)
        return result