from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


DEFAULT_WORKING_HOURS = {
    "monday": "09:00-16:00",
    "tuesday": "09:00-16:00",
    "wednesday": "09:00-16:00",
    "thursday": "09:00-16:00",
    "friday": "09:00-16:00",
    "saturday": "09:00-12:00",
    "sunday": None
}
