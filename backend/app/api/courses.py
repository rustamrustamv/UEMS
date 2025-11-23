"""
Course management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    ScheduleValidationRequest, ScheduleValidationResponse
)
from app.instrumentation.metrics import enrollment_capacity_gauge

router = APIRouter(prefix="/courses", tags=["courses"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[CourseResponse])
async def list_courses(
    semester: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all courses with optional filters.
    """
    query = select(Course).where(Course.is_active == is_active)

    if semester:
        query = query.where(Course.semester == semester)
    if year:
        query = query.where(Course.year == year)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    courses = result.scalars().all()

    logger.info(
        "Courses listed",
        extra={
            'event': 'courses_listed',
            'count': len(courses),
            'user_id': str(current_user.id)
        }
    )

    return courses


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get course details by ID.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return course


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Create a new course (Admin only).
    """
    # Check if course code already exists
    result = await db.execute(select(Course).where(Course.code == course_data.code))
    existing_course = result.scalar_one_or_none()

    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course with code {course_data.code} already exists"
        )

    # Verify teacher exists if provided
    if course_data.teacher_id:
        teacher_result = await db.execute(select(User).where(User.id == course_data.teacher_id))
        teacher = teacher_result.scalar_one_or_none()
        if not teacher or teacher.role.value != "teacher":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid teacher ID or user is not a teacher"
            )

    # Create course
    new_course = Course(**course_data.model_dump())
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)

    # Update capacity gauge
    utilization = (new_course.enrolled_count / new_course.capacity) * 100
    enrollment_capacity_gauge.labels(course_code=new_course.code).set(utilization)

    logger.info(
        "Course created",
        extra={
            'event': 'course_created',
            'course_id': str(new_course.id),
            'course_code': new_course.code,
            'created_by': str(current_user.id)
        }
    )

    return new_course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update course details.
    Admin can update any course, Teachers can update their own courses.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Authorization check
    if current_user.role.value == "teacher" and str(course.teacher_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own courses"
        )
    elif current_user.role.value not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Update fields
    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)

    # Update capacity gauge
    utilization = (course.enrolled_count / course.capacity) * 100
    enrollment_capacity_gauge.labels(course_code=course.code).set(utilization)

    logger.info(
        "Course updated",
        extra={
            'event': 'course_updated',
            'course_id': str(course.id),
            'updated_by': str(current_user.id)
        }
    )

    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Deactivate a course (soft delete, Admin only).
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    course.is_active = False
    await db.commit()

    logger.info(
        "Course deactivated",
        extra={
            'event': 'course_deactivated',
            'course_id': str(course.id),
            'deleted_by': str(current_user.id)
        }
    )


@router.post("/validate-schedule", response_model=ScheduleValidationResponse)
async def validate_schedule(
    validation_request: ScheduleValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a new course schedule conflicts with student's existing enrollments.
    """
    # Get student's current enrollments for the semester
    enrollments_result = await db.execute(
        select(Enrollment, Course)
        .join(Course)
        .where(
            and_(
                Enrollment.user_id == validation_request.user_id,
                Enrollment.status == EnrollmentStatus.ENROLLED,
                Course.semester == validation_request.semester,
                Course.year == validation_request.year
            )
        )
    )

    enrolled_courses = [course for _, course in enrollments_result.all()]
    conflicting_courses = []

    # Check for schedule conflicts
    new_schedule = validation_request.new_course_schedule

    for course in enrolled_courses:
        for day, new_times in new_schedule.items():
            if day in course.schedule:
                existing_times = course.schedule[day]
                # Simple overlap check (you can make this more sophisticated)
                if existing_times and new_times:
                    conflicting_courses.append(course.code)
                    break

    return ScheduleValidationResponse(
        has_conflict=len(conflicting_courses) > 0,
        conflicting_courses=conflicting_courses
    )
