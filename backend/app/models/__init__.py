"""
SQLAlchemy models for UEMS.
Import all models here to ensure they are registered with SQLAlchemy.
"""

from app.models.user import User, UserRole
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import Grade, AssignmentType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.payment import Payment, PaymentHistory, PaymentStatus, PaymentType

__all__ = [
    "User",
    "UserRole",
    "Course",
    "Enrollment",
    "EnrollmentStatus",
    "Grade",
    "AssignmentType",
    "Attendance",
    "AttendanceStatus",
    "Payment",
    "PaymentHistory",
    "PaymentStatus",
    "PaymentType",
]
