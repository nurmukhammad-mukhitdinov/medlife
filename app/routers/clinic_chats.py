import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.security import get_current_user, get_current_user_ws
from app.exc import LoggedHTTPException, raise_with_log
from app.models.users import UserModel
from app.schemas.clinic_chats import (
    ClinicChatLite,
    ClinicChatMessageCreate,
    ClinicChatMessageResponse,
    ClinicChatResponse,
)
from app.service.clinic_chats import ClinicChatService

router = APIRouter(prefix="/clinic-chats", tags=["Clinic Chats"])
ws_router = APIRouter(prefix="/clinic-chats", tags=["Clinic Chats"])


# --------- list threads ----------
@router.get(
    "/threads/me",
    response_model=List[ClinicChatLite],
    status_code=status.HTTP_200_OK,
)
async def my_clinic_chat_threads(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        threads = await ClinicChatService(db).list_threads_for_user(user=current_user)
        resp: List[ClinicChatLite] = []
        for t in threads:
            # robust "last" selection (in case relation isn’t ordered)
            last = max(t.messages, key=lambda m: m.created_at) if t.messages else None
            resp.append(
                ClinicChatLite(
                    id=t.id,
                    hospital_id=t.hospital_id,
                    user_id=t.user_id,
                    last_message=(
                        ClinicChatMessageResponse(
                            id=last.id,
                            sender_type=last.sender_type,
                            text=last.text,
                            created_at=last.created_at,
                        )
                        if last
                        else None
                    ),
                )
            )
        return resp
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list my clinic chat threads: {e}",
        )


@router.get(
    "/threads/hospital",
    response_model=List[ClinicChatLite],
    status_code=status.HTTP_200_OK,
)
async def hospital_clinic_chat_threads_for_admin(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    For the logged-in hospital admin: list threads for the hospital they manage.
    """
    try:
        threads = await ClinicChatService(db).list_threads_for_hospital_admin(
            current_user=current_user
        )
        resp: List[ClinicChatLite] = []
        for t in threads:
            last = max(t.messages, key=lambda m: m.created_at) if t.messages else None
            resp.append(
                ClinicChatLite(
                    id=t.id,
                    hospital_id=t.hospital_id,
                    user_id=t.user_id,
                    last_message=(
                        ClinicChatMessageResponse(
                            id=last.id,
                            sender_type=last.sender_type,
                            text=last.text,
                            created_at=last.created_at,
                        )
                        if last
                        else None
                    ),
                )
            )
        return resp
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to list hospital clinic chat threads: {e}",
        )


# --------- get a single thread ----------
@router.get(
    "/threads/{hospital_id}/{user_id}",
    response_model=ClinicChatResponse,
    status_code=status.HTTP_200_OK,
)
async def get_clinic_chat_thread(
    hospital_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get the full thread (messages) for a specific hospital<->user pair.
    Access:
      - the user themselves, or
      - the hospital admin of that hospital
    """
    try:
        svc = ClinicChatService(db)
        thread = await svc.get_thread(hospital_id=hospital_id, user_id=user_id)

        # Access control in router to be explicit
        hospital = await svc._ensure_hospital(hospital_id)
        is_user = str(current_user.id) == str(user_id)
        is_admin = svc._is_hospital_admin_for(current_user, hospital)
        if not (is_user or is_admin):
            raise_with_log(status.HTTP_403_FORBIDDEN, "Not allowed to view this thread")

        return ClinicChatResponse(
            id=thread.id,
            hospital_id=thread.hospital_id,
            user_id=thread.user_id,
            messages=[
                ClinicChatMessageResponse(
                    id=m.id,
                    sender_type=m.sender_type,
                    text=m.text,
                    created_at=m.created_at,
                )
                for m in thread.messages
            ],
        )
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to get clinic chat thread: {e}",
        )


# --------- user sends (optional thread_id) ----------
@router.post(
    "/{hospital_id}/send",
    response_model=ClinicChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message_as_user_to_clinic(
    hospital_id: uuid.UUID,
    payload: ClinicChatMessageCreate,
    thread_id: Optional[uuid.UUID] = Query(
        None,
        description=(
            "Optional existing thread id. If provided, message will be appended to this thread. "
            "Otherwise, a thread for (hospital_id, current user) will be created or reused."
        ),
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    User sends a message to a hospital (clinic).
    """
    try:
        thread = await ClinicChatService(db).send_message_as_user(
            hospital_id=hospital_id,
            current_user=current_user,
            text=payload.text,
            thread_id=thread_id,
        )
        return ClinicChatResponse(
            id=thread.id,
            hospital_id=thread.hospital_id,
            user_id=thread.user_id,
            messages=[
                ClinicChatMessageResponse(
                    id=m.id,
                    sender_type=m.sender_type,
                    text=m.text,
                    created_at=m.created_at,
                )
                for m in thread.messages
            ],
        )
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to send clinic chat message: {e}",
        )


# --------- hospital replies by thread_id ----------
@router.post(
    "/threads/{thread_id}/reply",
    response_model=ClinicChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reply_as_clinic_to_thread(
    thread_id: uuid.UUID,
    payload: ClinicChatMessageCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Hospital admin replies to an EXISTING thread using its ID.
    """
    try:
        thread = await ClinicChatService(db).send_message_as_hospital_by_thread(
            thread_id=thread_id,
            current_user=current_user,
            text=payload.text,
        )
        return ClinicChatResponse(
            id=thread.id,
            hospital_id=thread.hospital_id,
            user_id=thread.user_id,
            messages=[
                ClinicChatMessageResponse(
                    id=m.id,
                    sender_type=m.sender_type,
                    text=m.text,
                    created_at=m.created_at,
                )
                for m in thread.messages
            ],
        )
    except LoggedHTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise_with_log(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Failed to reply to clinic chat thread: {e}",
        )


# --------- WebSocket endpoint ----------
@ws_router.websocket("/ws/threads/{thread_id}")
async def clinic_chat_thread_ws(
    websocket: WebSocket,
    thread_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user_ws),  # WS-friendly auth
):
    """
    Connect client to a specific thread room.
    Authorization:
      - the user must be either the owner of the thread OR the hospital admin of that thread's hospital.
    """
    svc = ClinicChatService(db)
    try:
        tid = uuid.UUID(thread_id)
    except ValueError:
        await websocket.close(code=1008)
        return

    # Authorize
    thread = await svc.get_thread_by_id(thread_id=tid)
    hospital = await svc._ensure_hospital(thread.hospital_id)
    is_user = str(current_user.id) == str(thread.user_id)
    is_admin = ClinicChatService._is_hospital_admin_for(current_user, hospital)
    if not (is_user or is_admin):
        await websocket.close(code=1008)
        return

    manager = ClinicChatService.manager()
    await manager.connect(tid, websocket)

    try:
        await websocket.send_json({"event": "connected", "thread_id": thread_id})
        # Keep alive; handle optional pings if you want:
        while True:
            _ = await websocket.receive_text()
            # Optionally:
            # if _ == "ping":
            #     await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(tid, websocket)
    except Exception:
        manager.disconnect(tid, websocket)
        try:
            await websocket.close()
        except Exception:
            pass
