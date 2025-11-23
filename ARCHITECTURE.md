# University Education Management System (UEMS) - Architecture Document

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [API Structure](#api-structure)
5. [Instrumentation & Observability Strategy](#instrumentation--observability-strategy)
6. [Security & RBAC](#security--rbac)
7. [Integration Points](#integration-points)
8. [Deployment Architecture](#deployment-architecture)

---

## 1. System Overview

The University Education Management System (UEMS) is a production-grade, full-stack application designed to manage university operations including course management, student enrollment, grading, attendance tracking, and financial transactions.

### Core Capabilities
- **Role-Based Access Control**: Admin, Teacher, and Student roles with distinct permissions
- **Course Management**: Create courses, assign teachers, enforce enrollment caps, schedule conflict detection
- **Academic Operations**: Grade management, attendance tracking, enrollment workflows
- **Financial Integration**: Stripe-powered payment processing with webhook handling
- **Observability**: Comprehensive metrics, structured logging, and real-time monitoring

### Design Principles
- **Production-Ready**: Structured logging, metrics exposure, error handling
- **Cloud-Native**: Containerized, Kubernetes-ready, horizontally scalable
- **Observable**: Every critical path instrumented for monitoring and debugging
- **Secure**: JWT authentication, RBAC enforcement, input validation

---

## 2. Technology Stack

### Backend
- **Framework**: FastAPI 0.104+ (async support, automatic OpenAPI docs)
- **ORM**: SQLAlchemy 2.0+ with async support
- **Database**: PostgreSQL 15+ (running in Kubernetes)
- **Authentication**: JWT tokens with role-based claims
- **Validation**: Pydantic v2 for request/response validation

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS 3+
- **State Management**: React Query for server state, Context API for auth
- **HTTP Client**: Axios with interceptors for auth headers

### Infrastructure
- **Cloud Provider**: Microsoft Azure
- **Container Orchestration**: Azure Kubernetes Service (AKS)
- **Container Registry**: Azure Container Registry (ACR)
- **IaC**: Terraform
- **CI/CD**: GitLab CI

### Observability Stack
- **Metrics**: Prometheus (scraped from `/metrics` endpoint)
- **Visualization**: Grafana
- **Instrumentation**: prometheus-fastapi-instrumentator
- **Logging**: Structured JSON logs to stdout (captured by Kubernetes)

---

## 3. Database Schema

### Entity Relationship Overview

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   users     │────────▶│  courses    │◀────────│enrollments  │
│             │         │             │         │             │
│ - id (PK)   │         │ - id (PK)   │         │ - id (PK)   │
│ - email     │         │ - code      │         │ - user_id   │
│ - password  │         │ - name      │         │ - course_id │
│ - role      │         │ - teacher_id│         │ - status    │
│ - full_name │         │ - capacity  │         └─────────────┘
└─────────────┘         │ - schedule  │
                        └─────────────┘
                               │
                               │
                        ┌──────▼──────┐         ┌─────────────┐
                        │  grades     │         │ attendance  │
                        │             │         │             │
                        │ - id (PK)   │         │ - id (PK)   │
                        │ - enrollment│         │ - enrollment│
                        │ - assignment│         │ - date      │
                        │ - score     │         │ - status    │
                        └─────────────┘         └─────────────┘

┌─────────────┐         ┌─────────────────┐
│  payments   │────────▶│ payment_history │
│             │         │                 │
│ - id (PK)   │         │ - id (PK)       │
│ - user_id   │         │ - payment_id    │
│ - amount    │         │ - status        │
│ - stripe_id │         │ - timestamp     │
│ - status    │         │ - webhook_data  │
└─────────────┘         └─────────────────┘
```

### Detailed Schema

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    full_name VARCHAR(255) NOT NULL,
    student_id VARCHAR(50) UNIQUE,  -- Only for students
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_student_id ON users(student_id) WHERE student_id IS NOT NULL;
```

#### courses
```sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id UUID REFERENCES users(id) ON DELETE SET NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    enrolled_count INTEGER DEFAULT 0 CHECK (enrolled_count >= 0),
    credits INTEGER NOT NULL CHECK (credits > 0),
    semester VARCHAR(20) NOT NULL,
    year INTEGER NOT NULL,
    schedule JSONB NOT NULL,  -- {"monday": ["09:00-11:00"], "wednesday": ["14:00-16:00"]}
    room VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT check_enrollment_capacity CHECK (enrolled_count <= capacity)
);

CREATE INDEX idx_courses_teacher ON courses(teacher_id);
CREATE INDEX idx_courses_semester_year ON courses(semester, year);
CREATE INDEX idx_courses_code ON courses(code);
```

#### enrollments
```sql
CREATE TABLE enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'enrolled', 'dropped', 'completed')),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dropped_at TIMESTAMP,
    grade_final DECIMAL(5,2) CHECK (grade_final >= 0 AND grade_final <= 100),
    UNIQUE(user_id, course_id)
);

CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_course ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);
```

#### grades
```sql
CREATE TABLE grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    assignment_name VARCHAR(255) NOT NULL,
    assignment_type VARCHAR(50) NOT NULL CHECK (assignment_type IN ('homework', 'quiz', 'midterm', 'final', 'project')),
    score DECIMAL(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    max_score DECIMAL(5,2) NOT NULL CHECK (max_score > 0),
    weight DECIMAL(3,2) CHECK (weight >= 0 AND weight <= 1),
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graded_by UUID REFERENCES users(id),
    comments TEXT
);

CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);
CREATE INDEX idx_grades_type ON grades(assignment_type);
```

#### attendance
```sql
CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    marked_by UUID REFERENCES users(id),
    notes TEXT,
    UNIQUE(enrollment_id, date)
);

CREATE INDEX idx_attendance_enrollment ON attendance(enrollment_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_attendance_status ON attendance(status);
```

#### payments
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'USD',
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'refunded')),
    payment_type VARCHAR(50) NOT NULL CHECK (payment_type IN ('tuition', 'fees', 'books', 'other')),
    semester VARCHAR(20),
    year INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB  -- Store additional Stripe metadata
);

CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_stripe_intent ON payments(stripe_payment_intent_id);
CREATE INDEX idx_payments_semester_year ON payments(semester, year);
```

#### payment_history
```sql
CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    webhook_event_id VARCHAR(255),
    webhook_data JSONB,  -- Full webhook payload for audit
    notes TEXT
);

CREATE INDEX idx_payment_history_payment ON payment_history(payment_id);
CREATE INDEX idx_payment_history_timestamp ON payment_history(timestamp);
CREATE INDEX idx_payment_history_webhook ON payment_history(webhook_event_id);
```

---

## 4. API Structure

### Base URL
- Development: `http://localhost:8000/api/v1`
- Production: `https://uems.yourdomain.com/api/v1`

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login and receive JWT | No |
| POST | `/auth/refresh` | Refresh access token | Yes (Refresh Token) |
| GET | `/auth/me` | Get current user info | Yes |
| POST | `/auth/logout` | Invalidate refresh token | Yes |

### User Management (Admin Only)

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/users` | List all users (paginated) | Admin |
| GET | `/users/{id}` | Get user details | Admin, Self |
| POST | `/users` | Create new user | Admin |
| PUT | `/users/{id}` | Update user | Admin, Self (limited) |
| DELETE | `/users/{id}` | Deactivate user | Admin |
| GET | `/users/{id}/enrollments` | Get user's enrollments | Admin, Teacher, Self |

### Course Management

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/courses` | List courses (filtered by semester) | All (authenticated) |
| GET | `/courses/{id}` | Get course details | All (authenticated) |
| POST | `/courses` | Create course | Admin |
| PUT | `/courses/{id}` | Update course | Admin, Assigned Teacher |
| DELETE | `/courses/{id}` | Deactivate course | Admin |
| GET | `/courses/{id}/enrollments` | List enrolled students | Admin, Assigned Teacher |
| POST | `/courses/{id}/enroll` | Enroll student | Student (self), Admin |
| DELETE | `/courses/{id}/enroll/{enrollment_id}` | Drop course | Student (self), Admin |
| POST | `/courses/validate-schedule` | Check schedule conflicts | All (authenticated) |

### Grades Management

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/grades/enrollment/{enrollment_id}` | Get all grades for enrollment | Teacher, Student (self), Admin |
| POST | `/grades` | Create grade entry | Teacher (own courses), Admin |
| PUT | `/grades/{id}` | Update grade | Teacher (own courses), Admin |
| DELETE | `/grades/{id}` | Delete grade | Admin |
| GET | `/grades/course/{course_id}` | Get all grades for course | Teacher (own courses), Admin |

### Attendance Management

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/attendance/enrollment/{enrollment_id}` | Get attendance records | Teacher, Student (self), Admin |
| POST | `/attendance` | Mark attendance | Teacher (own courses), Admin |
| PUT | `/attendance/{id}` | Update attendance | Teacher (own courses), Admin |
| GET | `/attendance/course/{course_id}` | Get course attendance | Teacher (own courses), Admin |

### Payment Management

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/payments` | List payments (filtered by user) | Student (self), Admin |
| GET | `/payments/{id}` | Get payment details | Student (self), Admin |
| POST | `/payments/create-intent` | Create Stripe PaymentIntent | Student (self), Admin |
| POST | `/payments/webhook` | Stripe webhook handler | No Auth (Stripe signature) |
| GET | `/payments/{id}/history` | Get payment status history | Student (self), Admin |
| POST | `/payments/{id}/refund` | Initiate refund | Admin |

### Analytics & Reporting (Admin)

| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/analytics/dashboard` | Real-time system metrics | Admin |
| GET | `/analytics/enrollments` | Enrollment trends | Admin |
| GET | `/analytics/revenue` | Revenue analytics | Admin |
| GET | `/analytics/performance` | Academic performance stats | Admin, Teacher (own courses) |

### Health & Monitoring

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Basic health check | No |
| GET | `/health/ready` | Readiness probe (DB connection) | No |
| GET | `/health/live` | Liveness probe | No |
| GET | `/metrics` | Prometheus metrics | No |

---

## 5. Instrumentation & Observability Strategy

This section is **critical** for achieving production-grade observability. Every metric, log, and trace must be intentional and actionable.

### 5.1 Metrics Exposure

#### Primary Instrumentation Library
**prometheus-fastapi-instrumentator** provides automatic HTTP metrics:

```python
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

**Automatic Metrics Provided:**
1. `http_requests_total` - Counter of total HTTP requests
   - Labels: `method`, `handler`, `status`
2. `http_request_duration_seconds` - Histogram of request latencies
   - Labels: `method`, `handler`
   - Buckets: 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0
3. `http_requests_inprogress` - Gauge of active requests
   - Labels: `method`, `handler`

#### Custom Business Metrics

**File**: `backend/app/instrumentation/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, Info

# User Activity Metrics
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

# Course Enrollment Metrics
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

# Payment Metrics
payments_total = Counter(
    'uems_payments_total',
    'Total number of payment transactions',
    ['status', 'payment_type']  # succeeded, failed, refunded
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
    ['event_type', 'status']  # processed, failed, duplicate
)

# Database Metrics
database_query_duration = Histogram(
    'uems_database_query_duration_seconds',
    'Database query execution time',
    ['operation', 'table'],  # select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

database_connections_gauge = Gauge(
    'uems_database_connections',
    'Number of active database connections',
    ['state']  # idle, active
)

# Error Tracking
application_errors_total = Counter(
    'uems_application_errors_total',
    'Total number of application errors',
    ['error_type', 'severity']  # validation, database, external_api, internal
)

# API Rate Limiting
rate_limit_exceeded_total = Counter(
    'uems_rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['endpoint', 'user_role']
)

# Application Info
app_info = Info(
    'uems_application',
    'UEMS application metadata'
)
app_info.info({
    'version': '1.0.0',
    'environment': 'production',
    'build_date': '2025-01-15'
})
```

### 5.2 Structured Logging Strategy

**All logs MUST be in JSON format** for easier parsing by log aggregation systems.

#### Log Configuration

**File**: `backend/app/core/logging_config.py`

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Add trace context if available (for distributed tracing)
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
```

#### Logging Standards

**Log Levels:**
- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: Successful operations, state changes
- **WARNING**: Unexpected but recoverable situations
- **ERROR**: Error events that still allow the application to continue
- **CRITICAL**: Severe errors causing application failure

**Required Fields in All Logs:**
```json
{
    "timestamp": 1705334400.123,
    "level": "INFO",
    "logger": "app.api.courses",
    "module": "courses",
    "function": "create_course",
    "line": 45,
    "message": "Course created successfully",
    "trace_id": "abc123...",
    "request_id": "req-456...",
    "user_id": "uuid-789...",
    "context": {
        "course_code": "CS101",
        "teacher_id": "uuid-111...",
        "capacity": 30
    }
}
```

#### Context Injection via Middleware

**File**: `backend/app/middleware/logging_middleware.py`

```python
import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract user_id from JWT if available
        user_id = getattr(request.state, 'user_id', None)

        # Create log context
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host
        }

        start_time = time.time()

        logger.info(
            "Request started",
            extra={**extra, 'event': 'request_started'}
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                "Request completed",
                extra={
                    **extra,
                    'event': 'request_completed',
                    'status_code': response.status_code,
                    'duration_seconds': duration
                }
            )

            response.headers['X-Request-ID'] = request_id
            return response

        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    **extra,
                    'event': 'request_failed',
                    'error_type': type(exc).__name__,
                    'error_message': str(exc),
                    'duration_seconds': duration
                },
                exc_info=True
            )
            raise
```

### 5.3 Key Observability Scenarios

#### Scenario 1: Track Request Latency

**Goal**: Measure the 95th percentile latency for all API endpoints.

**Implementation**:
1. `prometheus-fastapi-instrumentator` automatically records `http_request_duration_seconds` histogram
2. In Grafana, query:
   ```promql
   histogram_quantile(0.95,
     sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler)
   )
   ```
3. Create alerts for endpoints exceeding 1s at p95

**Logging**:
```python
logger.info(
    "Database query executed",
    extra={
        'event': 'db_query',
        'operation': 'select',
        'table': 'courses',
        'duration_ms': 45.3,
        'rows_returned': 10
    }
)
```

#### Scenario 2: Track Error Rates

**Goal**: Monitor error rates by endpoint and error type, alert when error rate > 1%.

**Implementation**:
1. Use `http_requests_total{status=~"5.."}` for HTTP errors
2. Increment `application_errors_total` for business logic errors
3. Grafana query:
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[5m])) by (handler)
   /
   sum(rate(http_requests_total[5m])) by (handler)
   * 100
   ```

**Logging**:
```python
from app.instrumentation.metrics import application_errors_total

try:
    # Business logic
    enrollment = create_enrollment(user_id, course_id)
except EnrollmentCapacityError as e:
    application_errors_total.labels(
        error_type='enrollment_capacity',
        severity='warning'
    ).inc()
    logger.warning(
        "Enrollment rejected - course full",
        extra={
            'event': 'enrollment_rejected',
            'reason': 'capacity_exceeded',
            'course_id': course_id,
            'user_id': user_id,
            'current_capacity': e.current_count,
            'max_capacity': e.max_capacity
        }
    )
    raise
```

#### Scenario 3: Track Active Users

**Goal**: Display real-time count of active users by role on Admin Analytics dashboard.

**Implementation**:
1. Update `active_users_gauge` on login (increment) and logout/token expiry (decrement)
2. Run periodic cleanup job to sync with database
3. Expose via `/analytics/dashboard` endpoint
4. Frontend polls this endpoint every 30 seconds

**Code Example**:
```python
from app.instrumentation.metrics import active_users_gauge, user_logins_total

@router.post("/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.email, credentials.password)

    # Update metrics
    user_logins_total.labels(role=user.role).inc()
    active_users_gauge.labels(role=user.role).inc()

    logger.info(
        "User logged in",
        extra={
            'event': 'user_login',
            'user_id': str(user.id),
            'role': user.role,
            'ip_address': request.client.host
        }
    )

    # Create JWT with expiry tracking
    access_token = create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}
```

**Periodic Cleanup Job** (runs every 5 minutes):
```python
import asyncio
from sqlalchemy import select, func
from app.models import User

async def sync_active_users_metric():
    """Sync active users gauge with database truth"""
    async with db.session() as session:
        result = await session.execute(
            select(User.role, func.count(User.id))
            .where(User.is_active == True)
            .group_by(User.role)
        )

        role_counts = {role: count for role, count in result}

        for role in ['admin', 'teacher', 'student']:
            count = role_counts.get(role, 0)
            active_users_gauge.labels(role=role).set(count)

        logger.info(
            "Active users metric synchronized",
            extra={'event': 'metric_sync', 'role_counts': role_counts}
        )
```

### 5.4 Monitoring Dashboard Requirements

The Grafana dashboard (Phase 5) will visualize these metrics:

**Panel 1: Request Latency**
- Graph: p50, p95, p99 latency over time (per endpoint)
- Query: `histogram_quantile` on `http_request_duration_seconds`

**Panel 2: Error Rate**
- Graph: Error rate % by endpoint (5-minute window)
- Alert: Error rate > 1% for 5 minutes

**Panel 3: Active Users**
- Gauge: Current active users by role
- Query: `uems_active_users_total`

**Panel 4: Throughput**
- Graph: Requests per second by endpoint
- Query: `rate(http_requests_total[1m])`

**Panel 5: Payment Success Rate**
- Pie chart: Payment statuses (succeeded, failed, pending)
- Query: `uems_payments_total`

**Panel 6: Enrollment Trends**
- Graph: Enrollments over time by status
- Query: `rate(uems_enrollments_total[1h])`

**Panel 7: Database Performance**
- Graph: Query duration p95 by table
- Query: `histogram_quantile(0.95, uems_database_query_duration_seconds_bucket)`

**Panel 8: System Health**
- Status: Database connection pool status
- Status: Stripe API health (via synthetic checks)

---

## 6. Security & RBAC

### 6.1 Authentication Flow

1. **User Login**: POST `/auth/login` with email/password
2. **Credential Validation**: bcrypt password verification
3. **JWT Generation**: Create access token (15min TTL) and refresh token (7 days TTL)
4. **Token Response**: Return both tokens to client
5. **Subsequent Requests**: Client includes `Authorization: Bearer <access_token>`
6. **Token Refresh**: When access token expires, use refresh token to get new access token

### 6.2 JWT Payload Structure

```json
{
  "sub": "user-uuid-here",
  "email": "student@example.com",
  "role": "student",
  "full_name": "John Doe",
  "exp": 1705334400,
  "iat": 1705333500,
  "jti": "unique-token-id"
}
```

### 6.3 Role-Based Access Control

**Permission Matrix:**

| Resource | Admin | Teacher | Student |
|----------|-------|---------|---------|
| Users (all) | CRUD | Read (limited) | Read (self) |
| Courses | CRUD | RU (assigned) | Read (all) |
| Enrollments | CRUD | Read (own courses) | CRD (self) |
| Grades | CRUD | CRU (own courses) | Read (self) |
| Attendance | CRUD | CRU (own courses) | Read (self) |
| Payments | CRUD | None | CR (self) |
| Analytics | Read (all) | Read (own courses) | None |

**Implementation**: Dependency injection in FastAPI

```python
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user

async def require_role(allowed_roles: list[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Usage in routes
@router.get("/analytics/dashboard")
async def get_dashboard(
    current_user = Depends(require_role(["admin"]))
):
    ...
```

### 6.4 Input Validation

All endpoints use Pydantic v2 models for validation:

```python
from pydantic import BaseModel, EmailStr, constr, field_validator
from typing import Literal

class CourseCreate(BaseModel):
    code: constr(min_length=3, max_length=20, pattern=r'^[A-Z]{2,4}\d{3}$')
    name: constr(min_length=5, max_length=255)
    capacity: int = Field(gt=0, le=500)
    credits: int = Field(gt=0, le=6)
    semester: Literal['fall', 'spring', 'summer']
    year: int = Field(ge=2024, le=2030)
    schedule: dict  # Validated separately

    @field_validator('schedule')
    def validate_schedule(cls, v):
        allowed_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday'}
        if not all(day in allowed_days for day in v.keys()):
            raise ValueError('Invalid day in schedule')
        # Additional time slot validation...
        return v
```

---

## 7. Integration Points

### 7.1 Stripe Payment Integration

**Test Mode Configuration**:
- API Keys: Use test keys (`sk_test_...`, `pk_test_...`)
- Test Cards: `4242 4242 4242 4242` (success), `4000 0000 0000 9995` (decline)

**Payment Flow**:

1. **Client Initiates Payment**:
   ```javascript
   POST /api/v1/payments/create-intent
   {
     "amount": 5000.00,
     "payment_type": "tuition",
     "semester": "spring",
     "year": 2025
   }
   ```

2. **Backend Creates PaymentIntent**:
   ```python
   import stripe
   from app.instrumentation.metrics import payment_processing_duration

   @router.post("/payments/create-intent")
   async def create_payment_intent(
       payment_data: PaymentCreate,
       current_user = Depends(get_current_user)
   ):
       with payment_processing_duration.time():
           # Create payment record in DB
           payment = Payment(
               user_id=current_user.id,
               amount=payment_data.amount,
               status='pending',
               payment_type=payment_data.payment_type
           )
           db.add(payment)
           await db.commit()

           # Create Stripe PaymentIntent
           intent = stripe.PaymentIntent.create(
               amount=int(payment_data.amount * 100),  # Convert to cents
               currency='usd',
               metadata={
                   'payment_id': str(payment.id),
                   'user_id': str(current_user.id),
                   'payment_type': payment_data.payment_type
               }
           )

           # Update payment record
           payment.stripe_payment_intent_id = intent.id
           await db.commit()

           logger.info(
               "Payment intent created",
               extra={
                   'event': 'payment_intent_created',
                   'payment_id': str(payment.id),
                   'amount': payment_data.amount,
                   'stripe_intent_id': intent.id
               }
           )

           return {
               'client_secret': intent.client_secret,
               'payment_id': str(payment.id)
           }
   ```

3. **Client Confirms Payment** (using Stripe.js):
   ```javascript
   const {error} = await stripe.confirmCardPayment(clientSecret, {
     payment_method: {card: cardElement}
   });
   ```

4. **Stripe Sends Webhook**:
   ```python
   @router.post("/payments/webhook")
   async def stripe_webhook(request: Request):
       payload = await request.body()
       sig_header = request.headers.get('stripe-signature')

       try:
           event = stripe.Webhook.construct_event(
               payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
           )
       except ValueError:
           stripe_webhook_events_total.labels(
               event_type='unknown',
               status='failed'
           ).inc()
           raise HTTPException(status_code=400)

       # Handle the event
       if event['type'] == 'payment_intent.succeeded':
           payment_intent = event['data']['object']
           await handle_payment_success(payment_intent)
           stripe_webhook_events_total.labels(
               event_type='payment_intent.succeeded',
               status='processed'
           ).inc()

       elif event['type'] == 'payment_intent.payment_failed':
           payment_intent = event['data']['object']
           await handle_payment_failure(payment_intent)
           stripe_webhook_events_total.labels(
               event_type='payment_intent.payment_failed',
               status='processed'
           ).inc()

       return {'status': 'success'}
   ```

5. **Update Payment Status**:
   ```python
   async def handle_payment_success(payment_intent):
       payment_id = payment_intent['metadata']['payment_id']

       async with db.session() as session:
           payment = await session.get(Payment, payment_id)
           payment.status = 'succeeded'
           payment.updated_at = datetime.utcnow()

           # Create history record
           history = PaymentHistory(
               payment_id=payment_id,
               status='succeeded',
               webhook_event_id=payment_intent['id'],
               webhook_data=payment_intent
           )
           session.add(history)
           await session.commit()

           # Update metrics
           payments_total.labels(
               status='succeeded',
               payment_type=payment.payment_type
           ).inc()
           payments_amount_total.labels(
               payment_type=payment.payment_type
           ).inc(float(payment.amount))

           logger.info(
               "Payment succeeded",
               extra={
                   'event': 'payment_succeeded',
                   'payment_id': payment_id,
                   'amount': float(payment.amount),
                   'stripe_intent_id': payment_intent['id']
               }
           )
   ```

---

## 8. Deployment Architecture

### 8.1 Azure Resources (Terraform-Managed)

```
Azure Subscription
│
├── Resource Group: rg-uems-prod
│   ├── AKS Cluster: aks-uems-prod
│   │   ├── Node Pool: default (2-4 nodes, Standard_B2s)
│   │   └── Networking: Azure CNI
│   │
│   └── Container Registry: acruemsprod
│       ├── Repository: uems-backend
│       └── Repository: uems-frontend
```

### 8.2 Kubernetes Architecture

```
Namespace: uems-prod
│
├── Deployment: backend
│   ├── Replicas: 2
│   ├── Container: uems-backend:latest
│   ├── Resources: requests(cpu: 200m, memory: 512Mi), limits(cpu: 1000m, memory: 1Gi)
│   ├── Env: DATABASE_URL, STRIPE_API_KEY, JWT_SECRET
│   └── Probes: liveness(/health/live), readiness(/health/ready)
│
├── Deployment: frontend
│   ├── Replicas: 2
│   ├── Container: uems-frontend:latest
│   └── Resources: requests(cpu: 100m, memory: 256Mi)
│
├── Deployment: postgres
│   ├── Replicas: 1 (StatefulSet in production)
│   ├── Container: postgres:15-alpine
│   ├── PVC: postgres-data (10Gi)
│   └── Env: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
│
├── Service: backend-service (ClusterIP, port 8000)
├── Service: frontend-service (ClusterIP, port 3000)
├── Service: postgres-service (ClusterIP, port 5432)
│
└── Ingress: uems-ingress
    ├── Host: uems.yourdomain.com
    ├── TLS: Cert-Manager (Let's Encrypt)
    ├── Rules:
    │   ├── / → frontend-service:3000
    │   └── /api/v1 → backend-service:8000

Namespace: monitoring
│
├── Prometheus (via Helm: kube-prometheus-stack)
│   ├── Scrape Configs: backend /metrics endpoint
│   └── Storage: 50Gi PVC
│
└── Grafana
    ├── Datasource: Prometheus
    └── Dashboards: UEMS Custom Dashboard (imported from JSON)
```

### 8.3 CI/CD Pipeline Flow

```
GitLab Repository Push
│
├── Stage: Lint & Test
│   ├── Backend: pytest, ruff, mypy
│   └── Frontend: npm test, eslint
│
├── Stage: Build Docker Images
│   ├── docker build backend → acr.azurecr.io/uems-backend:${CI_COMMIT_SHA}
│   └── docker build frontend → acr.azurecr.io/uems-frontend:${CI_COMMIT_SHA}
│
├── Stage: Push to ACR
│   └── docker push (with service principal auth)
│
└── Stage: Deploy (manual trigger)
    ├── kubectl set image deployment/backend ...
    ├── kubectl set image deployment/frontend ...
    └── kubectl rollout status
```

---

## Next Steps

With this architecture document complete, we are ready to proceed to **Phase 2: Application Code Development**.

**Phase 2 will deliver**:
1. FastAPI backend with all endpoints, instrumentation, and Stripe integration
2. SQLAlchemy models matching the schema above
3. `seed.py` script to populate the database with realistic test data
4. Next.js frontend with authentication, course enrollment UI, and Admin Analytics dashboard
5. Dockerfiles optimized for production

**Key Files to be Created**:
- `backend/app/main.py` - FastAPI application entry point
- `backend/app/models/` - SQLAlchemy models
- `backend/app/api/` - API route handlers
- `backend/app/core/` - Auth, config, logging
- `backend/app/instrumentation/` - Metrics and monitoring
- `backend/seed.py` - Database seeding script
- `frontend/app/` - Next.js pages and components
- `frontend/components/admin/AnalyticsDashboard.tsx` - Real-time analytics UI
- `backend/Dockerfile` - Multi-stage Python build
- `frontend/Dockerfile` - Multi-stage Node.js build

Shall I proceed to Phase 2?
