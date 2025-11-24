'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import api from '@/lib/api';

interface Enrollment {
  id: string;
  status: string;
  enrolled_at: string;
  course: {
    id: string;
    code: string;
    name: string;
    credits: number;
    semester: string;
    year: number;
    teacher_name: string;
  };
  grades?: {
    midterm_grade?: number;
    final_grade?: number;
    final_letter_grade?: string;
  }[];
}

export default function EnrollmentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && (!user || user.role !== 'STUDENT')) {
      router.push('/dashboard');
    } else if (user?.role === 'STUDENT') {
      fetchEnrollments();
    }
  }, [user, loading, router]);

  const fetchEnrollments = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/enrollments/my-enrollments');
      setEnrollments(response.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load enrollments');
    } finally {
      setIsLoading(false);
    }
  };

  if (loading || isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading enrollments...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (!user || user.role !== 'STUDENT') return null;

  const activeEnrollments = enrollments.filter(e => e.status === 'active');
  const totalCredits = activeEnrollments.reduce((sum, e) => sum + e.course.credits, 0);

  return (
    <DashboardLayout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">My Enrollments</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600 mb-1">Enrolled Courses</p>
            <p className="text-3xl font-bold text-gray-900">{activeEnrollments.length}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600 mb-1">Total Credits</p>
            <p className="text-3xl font-bold text-gray-900">{totalCredits}</p>
          </div>
        </div>

        {/* Enrollments Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {enrollments.map((enrollment) => (
            <div key={enrollment.id} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{enrollment.course.name}</h3>
                  <p className="text-sm text-gray-600">{enrollment.course.code}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full capitalize ${
                  enrollment.status === 'active' ? 'bg-green-100 text-green-800' :
                  enrollment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {enrollment.status}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <div className="flex justify-between">
                  <span>Instructor:</span>
                  <span className="font-medium text-gray-900">{enrollment.course.teacher_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Semester:</span>
                  <span className="font-medium text-gray-900">
                    {enrollment.course.semester} {enrollment.course.year}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Credits:</span>
                  <span className="font-medium text-gray-900">{enrollment.course.credits}</span>
                </div>
                <div className="flex justify-between">
                  <span>Enrolled:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(enrollment.enrolled_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {enrollment.grades && enrollment.grades.length > 0 && (
                <div className="border-t pt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Grades</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {enrollment.grades[0].midterm_grade && (
                      <div>
                        <span className="text-gray-600">Midterm:</span>
                        <span className="ml-2 font-bold text-gray-900">
                          {enrollment.grades[0].midterm_grade}%
                        </span>
                      </div>
                    )}
                    {enrollment.grades[0].final_grade && (
                      <div>
                        <span className="text-gray-600">Final:</span>
                        <span className="ml-2 font-bold text-gray-900">
                          {enrollment.grades[0].final_grade}%
                        </span>
                      </div>
                    )}
                    {enrollment.grades[0].final_letter_grade && (
                      <div className="col-span-2">
                        <span className="text-gray-600">Letter Grade:</span>
                        <span className="ml-2 text-2xl font-bold text-primary-600">
                          {enrollment.grades[0].final_letter_grade}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {enrollments.length === 0 && (
          <div className="bg-white p-12 rounded-lg shadow text-center">
            <p className="text-gray-600 mb-4">You are not enrolled in any courses yet.</p>
            <button
              onClick={() => router.push('/dashboard/courses')}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Browse Courses
            </button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
