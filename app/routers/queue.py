# app/routers/queues.py
import uuid, traceback
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.queue import QueueService
from app.schemas.queue import (
    QueueCreateSchema,
    QueueUpdateSchema,
    QueueResponseSchema,
)
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log

router = APIRouter(prefix="/queues", tags=["Queues"])


@router.get(
    "",
    response_model=List[QueueResponseSchema],
    status_code=status.HTTP_200_OK,
)
async def get_queues(db: AsyncSession = Depends(get_async_db)):
    """List all queue entries."""
    try:
        return await QueueService(db).list_queues()
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list queues: {e}",
        )


@router.get(
    "/{queue_id}",
    response_model=QueueResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_queue(
    queue_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a single queue entry by ID."""
    try:
        return await QueueService(db).get_queue(queue_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get queue: {e}",
        )


@router.post(
    "",
    response_model=QueueResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_queue(
    payload: QueueCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new queue entry."""
    try:
        return await QueueService(db).create_queue(payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to create queue: {e}",
        )


@router.patch(
    "/{queue_id}",
    response_model=QueueResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_queue(
    queue_id: uuid.UUID,
    payload: QueueUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    """Update an existing queue entry."""
    try:
        return await QueueService(db).update_queue(queue_id, payload)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to update queue: {e}",
        )
