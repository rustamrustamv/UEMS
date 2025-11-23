from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLEnum, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class AssignmentType(str, enum.Enum):
    HOMEWORK = "homework"
    QUIZ = "quiz"
    MIDTERM = "midterm"
    FINAL = "final"
    PROJECT = "project"


class Grade(Base):
    __tablename__ = "grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_name = Column(String(255), nullable=False)
    assignment_type = Column(SQLEnum(AssignmentType), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    max_score = Column(Numeric(5, 2), nullable=False)
    weight = Column(Numeric(3, 2), nullable=True)  # 0.0 to 1.0
    graded_at = Column(DateTime, default=datetime.utcnow)
    graded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    comments = Column(Text, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='check_score_range'),
        CheckConstraint('max_score > 0', name='check_max_score_positive'),
        CheckConstraint('weight IS NULL OR (weight >= 0 AND weight <= 1)', name='check_weight_range'),
    )

    # Relationships
    enrollment = relationship("Enrollment", back_populates="grades")
    graded_by_user = relationship("User", back_populates="marked_grades", foreign_keys=[graded_by])

    def __repr__(self):
        return f"<Grade {self.assignment_name} - {self.score}/{self.max_score}>"
