'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AnalyticsDashboard from '@/components/admin/AnalyticsDashboard';

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <DashboardLayout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>

        {user.role === 'ADMIN' ? (
          <AnalyticsDashboard />
        ) : user.role === 'TEACHER' ? (
          <div className="bg-white p-8 rounded-lg shadow">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome, {user.full_name}!
            </h2>
            <p className="text-gray-600 mb-4">
              You are logged in as a Teacher.
            </p>
            <p className="text-gray-600">
              Use the sidebar to navigate to your courses, manage grades, and track attendance.
            </p>
          </div>
        ) : (
          <div className="bg-white p-8 rounded-lg shadow">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome, {user.full_name}!
            </h2>
            <p className="text-gray-600 mb-4">
              You are logged in as a Student.
            </p>
            <p className="text-gray-600">
              Use the sidebar to view your courses, check grades, and manage payments.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
