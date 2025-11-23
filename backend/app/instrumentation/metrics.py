"""
Prometheus metrics for UEMS application.
All custom business metrics are defined here.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# =============================================================================
# User Activity Metrics
# =============================================================================

active_users_gauge = Gauge(
    'uems_active_users_total',
    'Number of active users in the system',
    ['role']  # admin, teacher, student
)

user_logins_total = Counter(
    'uems_user_logins_total',
    'Total number of successful user logins',
    ['role']
)

user_login_failures_total = Counter(
    'uems_user_login_failures_total',
    'Total number of failed login attempts',
    ['reason']  # invalid_credentials, account_inactive, rate_limited
)

# =============================================================================
# Course Enrollment Metrics
# =============================================================================

enrollments_total = Counter(
    'uems_enrollments_total',
    'Total number of course enrollments',
    ['status']  # enrolled, dropped, completed
)

enrollment_capacity_gauge = Gauge(
    'uems_course_capacity_utilization',
    'Course capacity utilization percentage',
    ['course_code']
)

enrollment_conflicts_total = Counter(
    'uems_enrollment_conflicts_total',
    'Total number of schedule conflict rejections'
)

# =============================================================================
# Payment Metrics
# =============================================================================

payments_total = Counter(
    'uems_payments_total',
    'Total number of payment transactions',
    ['status', 'payment_type']  # status: succeeded, failed, refunded
)

payments_amount_total = Counter(
    'uems_payments_amount_usd_total',
    'Total payment amount in USD',
    ['payment_type']
)

payment_processing_duration = Histogram(
    'uems_payment_processing_duration_seconds',
    'Time taken to process payment transactions',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

stripe_webhook_events_total = Counter(
    'uems_stripe_webhook_events_total',
    'Total number of Stripe webhook events received',
    ['event_type', 'status']  # status: processed, failed, duplicate
)

# =============================================================================
# Database Metrics
# =============================================================================

database_query_duration = Histogram(
    'uems_database_query_duration_seconds',
    'Database query execution time',
    ['operation', 'table'],  # operation: select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

database_connections_gauge = Gauge(
    'uems_database_connections',
    'Number of active database connections',
    ['state']  # idle, active
)

# =============================================================================
# Error Tracking
# =============================================================================

application_errors_total = Counter(
    'uems_application_errors_total',
    'Total number of application errors',
    ['error_type', 'severity']  # error_type: validation, database, external_api, internal
)

# =============================================================================
# API Rate Limiting
# =============================================================================

rate_limit_exceeded_total = Counter(
    'uems_rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['endpoint', 'user_role']
)

# =============================================================================
# Application Info
# =============================================================================

app_info = Info(
    'uems_application',
    'UEMS application metadata'
)

# Set application metadata
app_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'build_date': '2025-01-15'
})
