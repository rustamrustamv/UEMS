from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class GradeBase(BaseModel):
    enrollment_id: UUID
    assignment_name: constr(min_length=1, max_length=255)
    assignment_type: str
    score: Decimal = Field(ge=0, le=100)
    max_score: Decimal = Field(gt=0)
    weight: Optional[Decimal] = Field(None, ge=0, le=1)
    comments: Optional[str] = None


class GradeCreate(GradeBase):
    pass


class GradeUpdate(BaseModel):
    score: Optional[Decimal] = Field(None, ge=0, le=100)
    max_score: Optional[Decimal] = Field(None, gt=0)
    weight: Optional[Decimal] = Field(None, ge=0, le=1)
    comments: Optional[str] = None


class GradeResponse(GradeBase):
    id: UUID
    graded_at: datetime
    graded_by: Optional[UUID] = None

    class Config:
        from_attributes = True
