from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class EnrollmentBase(BaseModel):
    user_id: UUID
    course_id: UUID


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    grade_final: Optional[Decimal] = Field(None, ge=0, le=100)


class EnrollmentResponse(EnrollmentBase):
    id: UUID
    status: str
    enrolled_at: datetime
    dropped_at: Optional[datetime] = None
    grade_final: Optional[Decimal] = None

    class Config:
        from_attributes = True


class EnrollmentWithCourse(EnrollmentResponse):
    course_code: str
    course_name: str
    teacher_name: Optional[str] = None
