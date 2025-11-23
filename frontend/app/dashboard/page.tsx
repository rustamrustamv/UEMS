'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';
import AnalyticsDashboard from '@/components/admin/AnalyticsDashboard';

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
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
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">UEMS Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm">
                <span className="text-gray-600">Welcome, </span>
                <span className="font-semibold text-gray-900">{user.full_name}</span>
                <span className="ml-2 px-2 py-1 text-xs bg-primary-100 text-primary-800 rounded-full capitalize">
                  {user.role}
                </span>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {user.role === 'admin' ? (
          <AnalyticsDashboard />
        ) : (
          <div className="bg-white p-8 rounded-lg shadow">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome to UEMS!
            </h2>
            <p className="text-gray-600 mb-4">
              You are logged in as a <span className="font-semibold capitalize">{user.role}</span>.
            </p>
            <p className="text-gray-600">
              The Admin Analytics Dashboard is available for admin users only.
              Log in with an admin account to view comprehensive analytics.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
