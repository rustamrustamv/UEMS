"""
Pydantic schemas for request/response validation.
"""

from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    TokenRefreshRequest, TokenResponse
)
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    ScheduleValidationRequest, ScheduleValidationResponse
)
from app.schemas.enrollment import (
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse, EnrollmentWithCourse
)
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse
from app.schemas.payment import (
    PaymentCreate, PaymentResponse, PaymentIntentResponse,
    PaymentHistoryResponse, RefundRequest
)
from app.schemas.analytics import (
    DashboardResponse, ActiveUsersMetric, EnrollmentTrends,
    PaymentMetrics, PerformanceStats
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "LoginRequest", "LoginResponse",
    "TokenRefreshRequest", "TokenResponse",
    "CourseCreate", "CourseUpdate", "CourseResponse",
    "ScheduleValidationRequest", "ScheduleValidationResponse",
    "EnrollmentCreate", "EnrollmentUpdate", "EnrollmentResponse", "EnrollmentWithCourse",
    "GradeCreate", "GradeUpdate", "GradeResponse",
    "AttendanceCreate", "AttendanceUpdate", "AttendanceResponse",
    "PaymentCreate", "PaymentResponse", "PaymentIntentResponse",
    "PaymentHistoryResponse", "RefundRequest",
    "DashboardResponse", "ActiveUsersMetric", "EnrollmentTrends",
    "PaymentMetrics", "PerformanceStats"
]
