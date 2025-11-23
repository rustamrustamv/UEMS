# University Education Management System (UEMS)

A production-grade, full-stack application for managing university operations including course management, student enrollment, grading, attendance tracking, and financial transactions.

## Overview

This project demonstrates enterprise-level software architecture and modern DevOps practices through a comprehensive university management system. Built with scalability, observability, and security in mind.

**Key Technologies**: FastAPI, Next.js, PostgreSQL, Kubernetes, Terraform, Prometheus, Grafana, Azure Cloud

## Features

### Core Functionality
- Role-based access control (Admin, Teacher, Student)
- Course management with enrollment capacity and schedule conflict detection
- Grade and attendance tracking
- Stripe payment integration with webhook handling
- Real-time analytics dashboard

### Technical Capabilities
- RESTful API with automatic OpenAPI documentation
- JWT-based authentication with refresh tokens
- Structured JSON logging for log aggregation
- Prometheus metrics exposure for monitoring
- Kubernetes-ready with health probes
- Infrastructure as Code with Terraform
- Automated CI/CD with GitHub Actions

## Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Authentication, config, logging
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── instrumentation/# Prometheus metrics
│   │   └── middleware/     # Request logging middleware
│   ├── seed.py             # Database seeding script
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                # Next.js application
│   ├── app/                # Next.js 14 app directory
│   ├── components/         # React components
│   ├── lib/                # API client and auth context
│   ├── package.json
│   └── Dockerfile
│
├── terraform/               # Azure infrastructure
│   ├── main.tf
│   ├── variables.tf
│   └── README.md
│
├── k8s/                     # Kubernetes manifests
│   └── monitoring/         # Prometheus & Grafana config
│
├── .github/workflows/       # CI/CD pipeline
│   └── azure-deploy.yml
│
├── ARCHITECTURE.md          # System architecture documentation
└── DEPLOYMENT.md            # Deployment guide
```

## Technology Stack

**Backend**
- FastAPI 0.109+ (Python async web framework)
- SQLAlchemy 2.0+ (ORM with async support)
- PostgreSQL 15+ (Database)
- Pydantic v2 (Data validation)
- Prometheus FastAPI Instrumentator (Metrics)

**Frontend**
- Next.js 14 (React framework with App Router)
- Tailwind CSS 3 (Styling)
- Recharts (Data visualization)
- Axios (HTTP client)

**Infrastructure & DevOps**
- Azure Kubernetes Service (Container orchestration)
- Azure Container Registry (Docker registry)
- Terraform (Infrastructure as Code)
- GitHub Actions (CI/CD)
- Prometheus + Grafana (Monitoring)
- Helm (Kubernetes package manager)

## Quick Start

### Prerequisites
- Docker
- Node.js 20+
- Python 3.11+
- Azure CLI (for cloud deployment)
- Terraform (for infrastructure)

### Local Development

1. **Start Backend**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=uems \
  -p 5432:5432 \
  postgres:15-alpine

# Configure environment
cp .env.example .env

# Run migrations and seed data
python seed.py

# Start server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`
- API docs: `http://localhost:8000/api/v1/docs`
- Metrics: `http://localhost:8000/metrics`

2. **Start Frontend**

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start development server
npm run dev
```

Frontend runs at `http://localhost:3000`

3. **Login**

Default credentials:
- Admin: `admin@university.edu` / `admin123`
- Teacher: `prof.smith@university.edu` / `teacher123`
- Student: `student1@university.edu` / `student123`

## Architecture

### Database Schema
- **Users** - Authentication and role management
- **Courses** - Course catalog with capacity limits
- **Enrollments** - Student course registrations
- **Grades** - Assignment grades and scoring
- **Attendance** - Class attendance records
- **Payments** - Stripe transaction tracking
- **Payment History** - Audit trail for payment status changes

### API Structure
40+ RESTful endpoints organized by domain:
- Authentication (`/auth`)
- User Management (`/users`)
- Courses (`/courses`)
- Enrollments (via courses endpoints)
- Grades (`/grades`)
- Attendance (`/attendance`)
- Payments (`/payments`)
- Analytics (`/analytics`)
- Health Checks (`/health`)

### Observability
**Metrics**: 20+ custom business metrics exposed via `/metrics`
- Active users by role
- Enrollment trends
- Payment success/failure rates
- Request latency (p50, p95, p99)
- Error rates
- Database query performance

**Logging**: Structured JSON logs with request context
- Automatic request ID injection
- User ID tracking
- Trace ID support for distributed tracing

## Deployment

See `DEPLOYMENT.md` for complete deployment guide.

**Summary**:
1. Create Azure account
2. Deploy infrastructure with Terraform
3. Configure GitHub Actions secrets
4. Build and push Docker images
5. Deploy to Kubernetes
6. Set up monitoring

**Estimated Time**: 2-3 hours
**Estimated Cost**: ~$1-2 for testing (then delete resources)

## CI/CD Pipeline

GitHub Actions workflow with 5 stages:
1. **Lint** - Code quality checks (ruff, ESLint)
2. **Test** - Unit tests
3. **Build** - Docker image creation
4. **Push** - Push to Azure Container Registry
5. **Deploy** - Deploy to AKS

Triggered on push to `main` branch.

## Monitoring

Prometheus and Grafana deployed via Helm chart.

**Custom Dashboard** includes:
- Request latency percentiles
- Error rate tracking
- Active user metrics
- Enrollment trends
- Payment analytics
- Database performance

Access Grafana:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# http://localhost:3000 (admin/admin123)
```

## Security

- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC)
- Input validation via Pydantic schemas
- SQL injection prevention via ORM
- CORS configuration
- Kubernetes secrets for sensitive data
- Health check endpoints for liveness/readiness probes

## Testing

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm test

# Integration tests
curl http://localhost:8000/health
```

## Development Workflow

1. Create feature branch
2. Make changes
3. Commit and push
4. GitHub Actions runs tests and linting
5. Merge to `main` triggers deployment (if configured)

## License

This project is for educational and portfolio purposes.

## Author

Built to demonstrate production-grade full-stack development and DevOps practices.

For questions or collaboration, please open an issue.
