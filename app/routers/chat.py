# app/api/chat.py
from uuid import UUID as UUIDType
from fastapi import APIRouter, Depends, Query, status
from app.schemas.chat import ChatRequestSchema, ChatResponseSchema, ConversationDetailResponse
import traceback
from typing import List
import uuid
from sqlalchemy import select, func
from typing import List, Tuple
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatHistoryResponse
from app.core.database import get_async_db
from app.exc import LoggedHTTPException, raise_with_log
from app.service.chat import ChatService
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def chat_endpoint(
    payload: ChatRequestSchema,
    conversation_id: UUIDType | None = Query(None),
    user_id: UUIDType = Query(...),
    service: ChatService = Depends(ChatService),
):
    reply, convo_id = await service.send(payload, conversation_id, user_id)
    return ChatResponseSchema(reply=reply, conversation_id=convo_id)
@router.get(
    "/conversations",
    response_model=List[ConversationDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def list_conversation_threads(
    user_id: UUIDType = Query(..., description="Your user UUID"),
    service: ChatService = Depends(ChatService),
):
    """
    One thread per conversation (all prompt/response pairs),
    sorted by most recent message.
    """
    try:
        threads = await service.list_conversation_threads(user_id)
        return [ConversationDetailResponse(**t) for t in threads]
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list conversation threads: {e}. {traceback.format_exc()}",
        )



@router.get(
    "/{conversation_id}",
    response_model=List[ChatHistoryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_chat(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await ChatService(db).get(user_id, conversation_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get conversation: {e}. {traceback.format_exc()}",
        )

@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
):
    try:
        await ChatService(db).delete(user_id, conversation_id)
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to delete conversation: {e}. {traceback.format_exc()}",
        )