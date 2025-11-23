from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    capacity = Column(Integer, nullable=False)
    enrolled_count = Column(Integer, default=0, nullable=False)
    credits = Column(Integer, nullable=False)
    semester = Column(String(20), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    schedule = Column(JSONB, nullable=False)  # {"monday": ["09:00-11:00"], "wednesday": ["14:00-16:00"]}
    room = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Constraints
    __table_args__ = (
        CheckConstraint('capacity > 0', name='check_capacity_positive'),
        CheckConstraint('enrolled_count >= 0', name='check_enrolled_count_nonnegative'),
        CheckConstraint('enrolled_count <= capacity', name='check_enrollment_capacity'),
        CheckConstraint('credits > 0', name='check_credits_positive'),
    )

    # Relationships
    teacher = relationship("User", back_populates="taught_courses", foreign_keys=[teacher_id])
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course {self.code} - {self.name}>"
