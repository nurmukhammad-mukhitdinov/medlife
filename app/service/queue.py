# app/services/queue_service.py
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.queue import QueueModel
from app.schemas.queue import QueueCreateSchema, QueueUpdateSchema
from app.exc import LoggedHTTPException


class QueueService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_queues(self) -> list[QueueModel]:
        stmt = select(QueueModel).options(
            selectinload(QueueModel.hospital),
            selectinload(QueueModel.doctor),
            selectinload(QueueModel.user),
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_queue(self, queue_id: uuid.UUID) -> QueueModel:
        stmt = (
            select(QueueModel)
            .where(QueueModel.id == queue_id)
            .options(
                selectinload(QueueModel.hospital),
                selectinload(QueueModel.doctor),
                selectinload(QueueModel.user),
            )
        )
        res = await self.db.execute(stmt)
        queue = res.scalars().first()
        if not queue:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Queue entry not found")
        return queue

    async def create_queue(self, payload: QueueCreateSchema) -> QueueModel:
        q = QueueModel(
            hospital_id=payload.hospital_id,
            user_id=payload.user_id,
            doctor_id=payload.doctor_id,
            position=payload.position,
        )
        self.db.add(q)
        await self.db.flush()
        return await self.get_queue(q.id)

    async def update_queue(
        self, queue_id: uuid.UUID, payload: QueueUpdateSchema
    ) -> QueueModel:
        q = await self.get_queue(queue_id)
        if payload.hospital_id is not None:
            q.hospital_id = payload.hospital_id
        if payload.user_id is not None:
            q.user_id = payload.user_id
        if payload.doctor_id is not None:
            q.doctor_id = payload.doctor_id
        if payload.position is not None:
            q.position = payload.position
        if payload.status is not None:
            q.status = payload.status
        if payload.called_at is not None:
            q.called_at = payload.called_at
        if payload.served_at is not None:
            q.served_at = payload.served_at
        await self.db.flush()
        return await self.get_queue(queue_id)

    async def delete_queue(self, queue_id: uuid.UUID) -> None:
        q = await self.get_queue(queue_id)
        await self.db.delete(q)
        await self.db.flush()
