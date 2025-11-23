from sqlalchemy import Column, Date, ForeignKey, DateTime, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(AttendanceStatus), nullable=False, index=True)
    marked_at = Column(DateTime, default=datetime.utcnow)
    marked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('enrollment_id', 'date', name='unique_enrollment_date'),
    )

    # Relationships
    enrollment = relationship("Enrollment", back_populates="attendance_records")
    marked_by_user = relationship("User", back_populates="marked_attendance", foreign_keys=[marked_by])

    def __repr__(self):
        return f"<Attendance enrollment={self.enrollment_id} date={self.date} status={self.status}>"
