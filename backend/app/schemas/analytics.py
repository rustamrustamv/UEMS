from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime


class ActiveUsersMetric(BaseModel):
    admin: int
    teacher: int
    student: int
    total: int


class EnrollmentTrends(BaseModel):
    enrolled: int
    dropped: int
    completed: int
    pending: int


class PaymentMetrics(BaseModel):
    total_succeeded: int
    total_failed: int
    total_pending: int
    total_amount_usd: float
    recent_payments: List[Dict[str, Any]]


class DashboardResponse(BaseModel):
    active_users: ActiveUsersMetric
    enrollment_trends: EnrollmentTrends
    payment_metrics: PaymentMetrics
    total_courses: int
    total_active_courses: int
    timestamp: datetime


class PerformanceStats(BaseModel):
    average_grade: float
    total_assignments: int
    completion_rate: float
