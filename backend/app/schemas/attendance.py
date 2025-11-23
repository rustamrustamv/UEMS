from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class AttendanceBase(BaseModel):
    enrollment_id: UUID
    date: date
    status: str
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: UUID
    marked_at: datetime
    marked_by: Optional[UUID] = None

    class Config:
        from_attributes = True
