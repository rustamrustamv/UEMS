"""
Analytics and reporting endpoints for Admin dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.auth import require_role
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.analytics import (
    DashboardResponse, ActiveUsersMetric, EnrollmentTrends,
    PaymentMetrics
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Get real-time analytics for Admin dashboard.
    Includes: active users, enrollment trends, payment metrics, course stats.
    """
    # 1. Active Users Count by Role
    users_result = await db.execute(
        select(User.role, func.count(User.id))
        .where(User.is_active == True)
        .group_by(User.role)
    )
    role_counts = {role.value: count for role, count in users_result.all()}

    active_users = ActiveUsersMetric(
        admin=role_counts.get('admin', 0),
        teacher=role_counts.get('teacher', 0),
        student=role_counts.get('student', 0),
        total=sum(role_counts.values())
    )

    # 2. Enrollment Trends
    enrollments_result = await db.execute(
        select(Enrollment.status, func.count(Enrollment.id))
        .group_by(Enrollment.status)
    )
    enrollment_counts = {status.value: count for status, count in enrollments_result.all()}

    enrollment_trends = EnrollmentTrends(
        enrolled=enrollment_counts.get('enrolled', 0),
        dropped=enrollment_counts.get('dropped', 0),
        completed=enrollment_counts.get('completed', 0),
        pending=enrollment_counts.get('pending', 0)
    )

    # 3. Payment Metrics
    payments_result = await db.execute(
        select(Payment.status, func.count(Payment.id))
        .group_by(Payment.status)
    )
    payment_status_counts = {status.value: count for status, count in payments_result.all()}

    # Total amount from succeeded payments
    amount_result = await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.SUCCEEDED)
    )
    total_amount = amount_result.scalar() or 0

    # Recent payments (last 10)
    recent_payments_result = await db.execute(
        select(Payment)
        .order_by(Payment.created_at.desc())
        .limit(10)
    )
    recent_payments_raw = recent_payments_result.scalars().all()
    recent_payments = [
        {
            'id': str(p.id),
            'amount': float(p.amount),
            'status': p.status.value,
            'payment_type': p.payment_type.value,
            'created_at': p.created_at.isoformat()
        }
        for p in recent_payments_raw
    ]

    payment_metrics = PaymentMetrics(
        total_succeeded=payment_status_counts.get('succeeded', 0),
        total_failed=payment_status_counts.get('failed', 0),
        total_pending=payment_status_counts.get('pending', 0),
        total_amount_usd=float(total_amount),
        recent_payments=recent_payments
    )

    # 4. Course Statistics
    total_courses_result = await db.execute(select(func.count(Course.id)))
    total_courses = total_courses_result.scalar() or 0

    active_courses_result = await db.execute(
        select(func.count(Course.id)).where(Course.is_active == True)
    )
    total_active_courses = active_courses_result.scalar() or 0

    # Compile dashboard response
    dashboard = DashboardResponse(
        active_users=active_users,
        enrollment_trends=enrollment_trends,
        payment_metrics=payment_metrics,
        total_courses=total_courses,
        total_active_courses=total_active_courses,
        timestamp=datetime.utcnow()
    )

    logger.info(
        "Dashboard analytics retrieved",
        extra={
            'event': 'dashboard_analytics_retrieved',
            'user_id': str(current_user.id)
        }
    )

    return dashboard
