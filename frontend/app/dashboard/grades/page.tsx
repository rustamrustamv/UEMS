'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface Grade {
  id: string;
  midterm_grade?: number;
  final_grade?: number;
  final_letter_grade?: string;
  enrollment: {
    id: string;
    student: {
      full_name: string;
      email: string;
      student_id: string;
    };
    course: {
      code: string;
      name: string;
    };
  };
}

export default function GradesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [grades, setGrades] = useState<Grade[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    } else if (user) {
      if (user.role === 'TEACHER') {
        fetchTeacherCourses();
      } else if (user.role === 'STUDENT') {
        fetchStudentGrades();
      }
    }
  }, [user, loading, router]);

  const fetchTeacherCourses = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/courses/my-courses');
      setCourses(response.data || []);
      if (response.data && response.data.length > 0) {
        setSelectedCourse(response.data[0].id);
        await fetchCourseGrades(response.data[0].id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load courses');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCourseGrades = async (courseId: string) => {
    try {
      setIsLoading(true);
      const response = await api.get(`/grades/course/${courseId}`);
      setGrades(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load grades');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStudentGrades = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/grades/my-grades');
      setGrades(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load grades');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCourseChange = async (courseId: string) => {
    setSelectedCourse(courseId);
    await fetchCourseGrades(courseId);
  };

  if (loading || isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading grades...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!user) return null;

  return (
    <DashboardLayout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          {user.role === 'TEACHER' ? 'Grade Management' : 'My Grades'}
        </h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {user.role === 'TEACHER' && courses.length > 0 && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Select Course</label>
            <select
              value={selectedCourse}
              onChange={(e) => handleCourseChange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
            >
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.code} - {course.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Grades Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {user.role === 'TEACHER' && (
                  <>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student ID</th>
                  </>
                )}
                {user.role === 'STUDENT' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Course</th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Midterm</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Final</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Letter Grade</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {grades.map((grade) => (
                <tr key={grade.id} className="hover:bg-gray-50">
                  {user.role === 'TEACHER' && grade.enrollment && (
                    <>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {grade.enrollment.student.full_name}
                        </div>
                        <div className="text-xs text-gray-500">{grade.enrollment.student.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {grade.enrollment.student.student_id}
                      </td>
                    </>
                  )}
                  {user.role === 'STUDENT' && grade.enrollment && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {grade.enrollment.course.name}
                      </div>
                      <div className="text-xs text-gray-500">{grade.enrollment.course.code}</div>
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {grade.midterm_grade ? `${grade.midterm_grade}%` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {grade.final_grade ? `${grade.final_grade}%` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {grade.final_letter_grade ? (
                      <span className="px-3 py-1 text-lg font-bold text-primary-600">
                        {grade.final_letter_grade}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {grades.length === 0 && (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <p className="text-gray-600">
              {user.role === 'TEACHER'
                ? 'No students enrolled in this course yet.'
                : 'No grades available yet.'}
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
