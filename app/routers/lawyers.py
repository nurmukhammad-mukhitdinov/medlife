import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.lawyers import LawyerCreate, LawyerUpdate, LawyerOut
from app.service.lawyers import LawyerCrudService


router = APIRouter(prefix="/lawyers", tags=["Lawyers"])


@router.post("", response_model=LawyerOut, status_code=status.HTTP_201_CREATED)
async def create_lawyer(payload: LawyerCreate, db: AsyncSession = Depends(get_async_db)):
    return await LawyerCrudService(db).create(payload)


@router.get("/{lawyer_id}", response_model=LawyerOut, status_code=status.HTTP_200_OK)
async def get_lawyer(lawyer_id: uuid.UUID, db: AsyncSession = Depends(get_async_db)):
    return await LawyerCrudService(db).get(lawyer_id)


@router.put("/{lawyer_id}", response_model=LawyerOut, status_code=status.HTTP_200_OK)
async def update_lawyer(lawyer_id: uuid.UUID, payload: LawyerUpdate, db: AsyncSession = Depends(get_async_db)):
    return await LawyerCrudService(db).update(lawyer_id, payload)


@router.delete("/{lawyer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lawyer(lawyer_id: uuid.UUID, db: AsyncSession = Depends(get_async_db)):
    await LawyerCrudService(db).delete(lawyer_id)
