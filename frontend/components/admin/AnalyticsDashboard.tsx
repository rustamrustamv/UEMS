'use client';

import { useEffect, useState } from 'react';
import { analyticsAPI } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface ActiveUsersMetric {
  admin: number;
  teacher: number;
  student: number;
  total: number;
}

interface EnrollmentTrends {
  enrolled: number;
  dropped: number;
  completed: number;
  pending: number;
}

interface PaymentMetrics {
  total_succeeded: number;
  total_failed: number;
  total_pending: number;
  total_amount_usd: number;
  recent_payments: any[];
}

interface DashboardData {
  active_users: ActiveUsersMetric;
  enrollment_trends: EnrollmentTrends;
  payment_metrics: PaymentMetrics;
  total_courses: number;
  total_active_courses: number;
  timestamp: string;
}

const COLORS = {
  admin: '#ef4444',
  teacher: '#3b82f6',
  student: '#10b981',
  enrolled: '#10b981',
  dropped: '#ef4444',
  completed: '#6366f1',
  pending: '#f59e0b',
  succeeded: '#10b981',
  failed: '#ef4444',
};

export default function AnalyticsDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchDashboardData = async () => {
    try {
      const dashboardData = await analyticsAPI.getDashboard();
      setData(dashboardData);
      setLastUpdate(new Date());
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!data) return null;

  // Prepare data for charts
  const activeUsersData = [
    { name: 'Admin', value: data.active_users.admin, color: COLORS.admin },
    { name: 'Teachers', value: data.active_users.teacher, color: COLORS.teacher },
    { name: 'Students', value: data.active_users.student, color: COLORS.student },
  ];

  const enrollmentData = [
    { name: 'Enrolled', value: data.enrollment_trends.enrolled, color: COLORS.enrolled },
    { name: 'Dropped', value: data.enrollment_trends.dropped, color: COLORS.dropped },
    { name: 'Completed', value: data.enrollment_trends.completed, color: COLORS.completed },
    { name: 'Pending', value: data.enrollment_trends.pending, color: COLORS.pending },
  ];

  const paymentData = [
    { name: 'Succeeded', value: data.payment_metrics.total_succeeded, color: COLORS.succeeded },
    { name: 'Failed', value: data.payment_metrics.total_failed, color: COLORS.failed },
    { name: 'Pending', value: data.payment_metrics.total_pending, color: COLORS.pending },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Analytics Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
        >
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Active Users"
          value={data.active_users.total}
          icon="👥"
          color="bg-blue-500"
        />
        <StatCard
          title="Active Courses"
          value={data.total_active_courses}
          subtitle={`of ${data.total_courses} total`}
          icon="📚"
          color="bg-green-500"
        />
        <StatCard
          title="Total Enrollments"
          value={data.enrollment_trends.enrolled}
          icon="✅"
          color="bg-purple-500"
        />
        <StatCard
          title="Revenue (USD)"
          value={`$${data.payment_metrics.total_amount_usd.toLocaleString()}`}
          icon="💰"
          color="bg-yellow-500"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Users by Role */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Active Users by Role</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={activeUsersData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {activeUsersData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Enrollment Trends */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Enrollment Status</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={enrollmentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#8884d8">
                {enrollmentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Status */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Payment Status</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={paymentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {paymentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Payments */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Recent Payments</h2>
          <div className="overflow-auto max-h-80">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Amount
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.payment_metrics.recent_payments.slice(0, 10).map((payment) => (
                  <tr key={payment.id}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                      ${payment.amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 capitalize">
                      {payment.payment_type}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          payment.status === 'succeeded'
                            ? 'bg-green-100 text-green-800'
                            : payment.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {payment.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Detailed Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricRow label="Admin Users" value={data.active_users.admin} />
          <MetricRow label="Teachers" value={data.active_users.teacher} />
          <MetricRow label="Students" value={data.active_users.student} />
          <MetricRow label="Enrolled" value={data.enrollment_trends.enrolled} />
          <MetricRow label="Dropped Courses" value={data.enrollment_trends.dropped} />
          <MetricRow label="Completed Courses" value={data.enrollment_trends.completed} />
          <MetricRow label="Successful Payments" value={data.payment_metrics.total_succeeded} />
          <MetricRow label="Failed Payments" value={data.payment_metrics.total_failed} />
          <MetricRow label="Pending Payments" value={data.payment_metrics.total_pending} />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: string;
  color: string;
}) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`${color} w-12 h-12 rounded-full flex items-center justify-center text-2xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-200">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-semibold text-gray-900">{value}</span>
    </div>
  );
}
