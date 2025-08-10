from datetime import datetime, timedelta
import uuid
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models import DoctorModel, QueueModel
from sqlalchemy.ext.asyncio import AsyncSession


class DoctorBookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_working_hours(self, doctor_id: uuid.UUID):
        doctor = await self.db.get(DoctorModel, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        return doctor.working_hours or {}

    async def get_available_slots(self, doctor_id: uuid.UUID, date_str: str):
        doctor = await self.db.get(DoctorModel, doctor_id)
        if not doctor or not doctor.working_hours:
            raise HTTPException(
                status_code=404, detail="Doctor not found or no working hours set"
            )

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_name = date_obj.strftime("%A").lower()
        hours_str = doctor.working_hours.get(day_name)
        if not hours_str:
            return {"date": date_str, "slots": []}

        start_str, end_str = hours_str.split("-")
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()

        # Get booked slots from DB
        booked_query = await self.db.execute(
            select(QueueModel).filter(
                QueueModel.doctor_id == doctor_id,
                QueueModel.appointment_date == date_obj,
            )
        )
        booked_times = {
            (q.appointment_start.time(), q.appointment_end.time())
            for q in booked_query.scalars().all()
        }

        # Generate 30-min slots
        slots = []
        current = datetime.combine(date_obj, start_time)
        end_dt = datetime.combine(date_obj, end_time)
        while current < end_dt:
            next_time = current + timedelta(minutes=30)
            status_val = (
                "booked"
                if (current.time(), next_time.time()) in booked_times
                else "free"
            )
            slots.append(
                {
                    "start": current.strftime("%H:%M"),
                    "end": next_time.strftime("%H:%M"),
                    "status": status_val,
                }
            )
            current = next_time

        return {"date": date_str, "slots": slots}

    async def book_slot(self, doctor_id: uuid.UUID, data):
        doctor = await self.db.get(DoctorModel, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        date_obj = data.date
        start_dt = datetime.combine(
            date_obj, datetime.strptime(data.start_time, "%H:%M").time()
        )
        end_dt = datetime.combine(
            date_obj, datetime.strptime(data.end_time, "%H:%M").time()
        )

        # Check if slot is booked
        existing_booking = await self.db.execute(
            select(QueueModel).filter(
                QueueModel.doctor_id == doctor_id,
                QueueModel.appointment_date == date_obj,
                QueueModel.appointment_start == start_dt,
                QueueModel.appointment_end == end_dt,
            )
        )
        if existing_booking.scalars().first():
            raise HTTPException(status_code=400, detail="Slot already booked")

        # Create booking
        booking = QueueModel(
            hospital_id=doctor.hospital_id,
            doctor_id=doctor_id,
            user_id=data.user_id,
            appointment_date=date_obj,
            appointment_start=start_dt,
            appointment_end=end_dt,
            status="waiting",
        )
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def update_booking(self, booking_id: uuid.UUID, data):
        booking = await self.db.get(QueueModel, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if data.date or data.start_time or data.end_time:
            date_obj = data.date or booking.appointment_date
            start_time_obj = (
                datetime.strptime(data.start_time, "%H:%M").time()
                if data.start_time
                else booking.appointment_start.time()
            )
            end_time_obj = (
                datetime.strptime(data.end_time, "%H:%M").time()
                if data.end_time
                else booking.appointment_end.time()
            )
            booking.appointment_date = date_obj
            booking.appointment_start = datetime.combine(date_obj, start_time_obj)
            booking.appointment_end = datetime.combine(date_obj, end_time_obj)

        if data.status:
            booking.status = data.status

        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    async def delete_booking(self, booking_id: uuid.UUID):
        booking = await self.db.get(QueueModel, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        await self.db.delete(booking)
        await self.db.commit()
        return {"detail": "Booking deleted"}

    async def get_all_bookings(self):
        result = await self.db.execute(select(QueueModel))
        return result.scalars().all()

    async def get_bookings_for_doctor(self, doctor_id: uuid.UUID):
        result = await self.db.execute(
            select(QueueModel).filter(QueueModel.doctor_id == doctor_id)
        )
        return result.scalars().all()
