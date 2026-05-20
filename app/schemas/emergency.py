from datetime import datetime
from pydantic import BaseModel, Field

from app.models.emergency import EmergencyType, EmergencyStatus


class EmergencyCreate(BaseModel):
    type: EmergencyType
    address: str = Field(..., min_length=3, max_length=500)
    description: str | None = Field(None, max_length=1000)


class EmergencyStatusUpdate(BaseModel):
    status: EmergencyStatus
    dispatcher_note: str | None = Field(None, max_length=1000)


class EmergencyPublic(BaseModel):
    id: int
    user_id: int
    type: EmergencyType
    status: EmergencyStatus
    address: str
    description: str | None
    dispatcher_note: str | None
    dispatcher_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmergencyWithUser(EmergencyPublic):
    """Расширенный ответ для диспетчера — с данными пользователя."""
    user_name: str
    user_phone: str
    user_village: str | None
    user_region: str | None

    model_config = {"from_attributes": True}
