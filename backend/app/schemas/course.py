from pydantic import BaseModel, constr, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


class CourseBase(BaseModel):
    code: constr(min_length=3, max_length=20)
    name: constr(min_length=5, max_length=255)
    description: Optional[str] = None
    capacity: int = Field(gt=0, le=500)
    credits: int = Field(gt=0, le=6)
    semester: str = Field(pattern=r'^(fall|spring|summer)$')
    year: int = Field(ge=2024, le=2030)
    schedule: Dict[str, List[str]]
    room: Optional[str] = None

    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v):
        allowed_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
        if not all(day.lower() in allowed_days for day in v.keys()):
            raise ValueError('Invalid day in schedule')
        # Validate time slots format (basic check)
        for day, slots in v.items():
            if not isinstance(slots, list):
                raise ValueError(f'Time slots for {day} must be a list')
            for slot in slots:
                if not isinstance(slot, str) or '-' not in slot:
                    raise ValueError(f'Invalid time slot format: {slot}. Expected format: HH:MM-HH:MM')
        return v


class CourseCreate(CourseBase):
    teacher_id: Optional[UUID] = None


class CourseUpdate(BaseModel):
    name: Optional[constr(min_length=5, max_length=255)] = None
    description: Optional[str] = None
    teacher_id: Optional[UUID] = None
    capacity: Optional[int] = Field(None, gt=0, le=500)
    schedule: Optional[Dict[str, List[str]]] = None
    room: Optional[str] = None
    is_active: Optional[bool] = None


class CourseResponse(CourseBase):
    id: UUID
    teacher_id: Optional[UUID] = None
    enrolled_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ScheduleValidationRequest(BaseModel):
    user_id: UUID
    new_course_schedule: Dict[str, List[str]]
    semester: str
    year: int


class ScheduleValidationResponse(BaseModel):
    has_conflict: bool
    conflicting_courses: List[str] = []
