"""
Database seeding script for UEMS.
Populates the database with realistic test data for development and testing.

Run with: python seed.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models import (
    User, UserRole, Course, Enrollment, EnrollmentStatus,
    Grade, AssignmentType, Attendance, AttendanceStatus,
    Payment, PaymentStatus, PaymentType, PaymentHistory
)
from app.core.database import Base

# Sample data
STUDENTS_DATA = [
    {"email": f"student{i}@university.edu", "full_name": f"Student {i}", "student_id": f"S{1000+i}", "department": dept}
    for i, dept in enumerate([
        "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology",
        "Engineering", "Business", "Psychology", "History", "English"
    ] * 5, start=1)
]

TEACHERS_DATA = [
    {"email": "prof.smith@university.edu", "full_name": "Dr. John Smith", "department": "Computer Science"},
    {"email": "prof.johnson@university.edu", "full_name": "Dr. Sarah Johnson", "department": "Mathematics"},
    {"email": "prof.williams@university.edu", "full_name": "Dr. Michael Williams", "department": "Physics"},
    {"email": "prof.brown@university.edu", "full_name": "Dr. Emily Brown", "department": "Engineering"},
    {"email": "prof.davis@university.edu", "full_name": "Dr. Robert Davis", "department": "Chemistry"},
    {"email": "prof.miller@university.edu", "full_name": "Dr. Jennifer Miller", "department": "Biology"},
    {"email": "prof.wilson@university.edu", "full_name": "Dr. David Wilson", "department": "Business"},
    {"email": "prof.moore@university.edu", "full_name": "Dr. Lisa Moore", "department": "Psychology"},
    {"email": "prof.taylor@university.edu", "full_name": "Dr. James Taylor", "department": "History"},
    {"email": "prof.anderson@university.edu", "full_name": "Dr. Mary Anderson", "department": "English"},
]

COURSES_DATA = [
    {"code": "CS101", "name": "Introduction to Programming", "credits": 3, "capacity": 30, "department": "Computer Science"},
    {"code": "CS201", "name": "Data Structures", "credits": 4, "capacity": 25, "department": "Computer Science"},
    {"code": "CS301", "name": "Database Systems", "credits": 3, "capacity": 20, "department": "Computer Science"},
    {"code": "MATH101", "name": "Calculus I", "credits": 4, "capacity": 35, "department": "Mathematics"},
    {"code": "MATH201", "name": "Linear Algebra", "credits": 3, "capacity": 30, "department": "Mathematics"},
    {"code": "PHYS101", "name": "Physics I", "credits": 4, "capacity": 25, "department": "Physics"},
    {"code": "PHYS201", "name": "Quantum Mechanics", "credits": 4, "capacity": 20, "department": "Physics"},
    {"code": "CHEM101", "name": "General Chemistry", "credits": 4, "capacity": 30, "department": "Chemistry"},
    {"code": "BIO101", "name": "Biology Fundamentals", "credits": 3, "capacity": 35, "department": "Biology"},
    {"code": "ENG101", "name": "Engineering Principles", "credits": 3, "capacity": 25, "department": "Engineering"},
    {"code": "BUS101", "name": "Introduction to Business", "credits": 3, "capacity": 40, "department": "Business"},
    {"code": "PSY101", "name": "Introduction to Psychology", "credits": 3, "capacity": 30, "department": "Psychology"},
    {"code": "HIST101", "name": "World History", "credits": 3, "capacity": 35, "department": "History"},
    {"code": "ENGL101", "name": "English Composition", "credits": 3, "capacity": 25, "department": "English"},
    {"code": "CS401", "name": "Machine Learning", "credits": 4, "capacity": 15, "department": "Computer Science"},
    {"code": "MATH301", "name": "Statistics", "credits": 3, "capacity": 30, "department": "Mathematics"},
    {"code": "BUS201", "name": "Marketing Fundamentals", "credits": 3, "capacity": 30, "department": "Business"},
    {"code": "PSY201", "name": "Cognitive Psychology", "credits": 3, "capacity": 25, "department": "Psychology"},
    {"code": "PHYS301", "name": "Thermodynamics", "credits": 4, "capacity": 20, "department": "Physics"},
    {"code": "BIO201", "name": "Molecular Biology", "credits": 4, "capacity": 20, "department": "Biology"},
]

SCHEDULES = [
    {"monday": ["09:00-11:00"], "wednesday": ["09:00-11:00"]},
    {"tuesday": ["10:00-12:00"], "thursday": ["10:00-12:00"]},
    {"monday": ["14:00-16:00"], "wednesday": ["14:00-16:00"]},
    {"tuesday": ["13:00-15:00"], "thursday": ["13:00-15:00"]},
    {"friday": ["09:00-12:00"]},
]


async def seed_database():
    """Main seeding function"""
    print("Starting database seeding...")

    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        try:
            # 1. Create Admin User
            print("\n1. Creating admin user...")
            admin = User(
                email="admin@university.edu",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                full_name="System Administrator",
                department="Administration",
                is_active=True
            )
            session.add(admin)
            await session.flush()
            print(f"   ✓ Admin created: {admin.email}")

            # 2. Create Teachers
            print("\n2. Creating teachers...")
            teachers = []
            for teacher_data in TEACHERS_DATA:
                teacher = User(
                    email=teacher_data["email"],
                    password_hash=get_password_hash("teacher123"),
                    role=UserRole.TEACHER,
                    full_name=teacher_data["full_name"],
                    department=teacher_data["department"],
                    is_active=True
                )
                session.add(teacher)
                teachers.append(teacher)
            await session.flush()
            print(f"   ✓ {len(teachers)} teachers created")

            # 3. Create Students
            print("\n3. Creating students...")
            students = []
            for student_data in STUDENTS_DATA[:50]:  # Create 50 students
                student = User(
                    email=student_data["email"],
                    password_hash=get_password_hash("student123"),
                    role=UserRole.STUDENT,
                    full_name=student_data["full_name"],
                    student_id=student_data["student_id"],
                    department=student_data["department"],
                    is_active=True
                )
                session.add(student)
                students.append(student)
            await session.flush()
            print(f"   ✓ {len(students)} students created")

            # 4. Create Courses
            print("\n4. Creating courses...")
            courses = []
            for i, course_data in enumerate(COURSES_DATA):
                # Assign teacher based on department
                teacher = next((t for t in teachers if t.department == course_data["department"]), teachers[0])
                schedule = SCHEDULES[i % len(SCHEDULES)]

                course = Course(
                    code=course_data["code"],
                    name=course_data["name"],
                    description=f"This course covers fundamental concepts in {course_data['name']}.",
                    teacher_id=teacher.id,
                    capacity=course_data["capacity"],
                    enrolled_count=0,
                    credits=course_data["credits"],
                    semester="spring",
                    year=2025,
                    schedule=schedule,
                    room=f"Room {100 + i}",
                    is_active=True
                )
                session.add(course)
                courses.append(course)
            await session.flush()
            print(f"   ✓ {len(courses)} courses created")

            # 5. Create Enrollments
            print("\n5. Creating enrollments...")
            enrollments = []
            for student in students[:40]:  # 40 students with enrollments
                # Enroll each student in 3-5 random courses
                import random
                num_enrollments = random.randint(3, 5)
                student_courses = random.sample(courses, num_enrollments)

                for course in student_courses:
                    enrollment = Enrollment(
                        user_id=student.id,
                        course_id=course.id,
                        status=EnrollmentStatus.ENROLLED,
                        enrolled_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    session.add(enrollment)
                    enrollments.append(enrollment)
                    course.enrolled_count += 1

            await session.flush()
            print(f"   ✓ {len(enrollments)} enrollments created")

            # 6. Create Grades
            print("\n6. Creating grades...")
            grades_count = 0
            assignment_types = list(AssignmentType)

            for enrollment in enrollments:
                # Create 3-5 grades per enrollment
                import random
                num_grades = random.randint(3, 5)

                for j in range(num_grades):
                    assignment_type = assignment_types[j % len(assignment_types)]
                    score = Decimal(str(random.uniform(70, 100)))

                    grade = Grade(
                        enrollment_id=enrollment.id,
                        assignment_name=f"{assignment_type.value.capitalize()} {j+1}",
                        assignment_type=assignment_type,
                        score=score,
                        max_score=Decimal("100.00"),
                        weight=Decimal("0.20"),
                        graded_at=datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                        graded_by=None,  # Would be the course teacher
                        comments="Good work!" if score > 85 else "Needs improvement"
                    )
                    session.add(grade)
                    grades_count += 1

            await session.flush()
            print(f"   ✓ {grades_count} grades created")

            # 7. Create Attendance Records
            print("\n7. Creating attendance records...")
            attendance_count = 0
            attendance_statuses = list(AttendanceStatus)

            for enrollment in enrollments[:20]:  # Attendance for first 20 enrollments
                # Create attendance for last 10 days
                import random
                for day_offset in range(10):
                    attendance_date = datetime.utcnow().date() - timedelta(days=day_offset)
                    status = random.choice(attendance_statuses)

                    attendance = Attendance(
                        enrollment_id=enrollment.id,
                        date=attendance_date,
                        status=status,
                        marked_at=datetime.utcnow() - timedelta(days=day_offset),
                        notes="Regular class" if status == AttendanceStatus.PRESENT else None
                    )
                    session.add(attendance)
                    attendance_count += 1

            await session.flush()
            print(f"   ✓ {attendance_count} attendance records created")

            # 8. Create Payments
            print("\n8. Creating payments...")
            payments = []
            payment_types = list(PaymentType)

            for student in students[:30]:  # Payments for first 30 students
                import random
                # Create 1-3 payments per student
                num_payments = random.randint(1, 3)

                for _ in range(num_payments):
                    payment_type = random.choice(payment_types)
                    amount = Decimal(str(random.uniform(500, 5000)))
                    status = random.choice([PaymentStatus.SUCCEEDED, PaymentStatus.SUCCEEDED, PaymentStatus.PENDING])

                    payment = Payment(
                        user_id=student.id,
                        amount=amount,
                        currency="USD",
                        stripe_payment_intent_id=f"pi_test_{random.randint(100000, 999999)}",
                        status=status,
                        payment_type=payment_type,
                        semester="spring",
                        year=2025,
                        description=f"{payment_type.value.capitalize()} payment for Spring 2025",
                        created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                    )
                    session.add(payment)
                    payments.append(payment)

            await session.flush()
            print(f"   ✓ {len(payments)} payments created")

            # 9. Create Payment History
            print("\n9. Creating payment history...")
            history_count = 0
            for payment in payments:
                # Create initial history record
                history = PaymentHistory(
                    payment_id=payment.id,
                    status=payment.status.value,
                    timestamp=payment.created_at,
                    notes="Payment initiated"
                )
                session.add(history)
                history_count += 1

            await session.flush()
            print(f"   ✓ {history_count} payment history records created")

            # Commit all changes
            await session.commit()

            print("\n" + "="*60)
            print("Database seeding completed successfully!")
            print("="*60)
            print("\nSeeded Data Summary:")
            print(f"  • 1 Admin user")
            print(f"  • {len(teachers)} Teachers")
            print(f"  • {len(students)} Students")
            print(f"  • {len(courses)} Courses")
            print(f"  • {len(enrollments)} Enrollments")
            print(f"  • {grades_count} Grades")
            print(f"  • {attendance_count} Attendance records")
            print(f"  • {len(payments)} Payments")
            print(f"  • {history_count} Payment history records")
            print("\nDefault Login Credentials:")
            print("  Admin:   admin@university.edu / admin123")
            print("  Teacher: prof.smith@university.edu / teacher123")
            print("  Student: student1@university.edu / student123")
            print("="*60)

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await session.close()
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
