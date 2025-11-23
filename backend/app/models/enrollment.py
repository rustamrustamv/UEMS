from sqlalchemy import Column, ForeignKey, DateTime, Enum as SQLEnum, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class EnrollmentStatus(str, enum.Enum):
    PENDING = "pending"
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(EnrollmentStatus), nullable=False, index=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    dropped_at = Column(DateTime, nullable=True)
    grade_final = Column(Numeric(5, 2), nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='unique_user_course'),
        CheckConstraint('grade_final >= 0 AND grade_final <= 100', name='check_grade_range'),
    )

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    grades = relationship("Grade", back_populates="enrollment", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="enrollment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Enrollment user={self.user_id} course={self.course_id} status={self.status}>"
