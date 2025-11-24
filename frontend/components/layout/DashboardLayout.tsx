'use client';

import { useAuth } from '@/lib/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

interface MenuItem {
  name: string;
  href: string;
  icon: string;
  roles: string[];
}

const menuItems: MenuItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊', roles: ['ADMIN', 'TEACHER', 'STUDENT'] },
  { name: 'Courses', href: '/dashboard/courses', icon: '📚', roles: ['ADMIN', 'TEACHER', 'STUDENT'] },
  { name: 'Users', href: '/dashboard/users', icon: '👥', roles: ['ADMIN'] },
  { name: 'Payments', href: '/dashboard/payments', icon: '💳', roles: ['ADMIN', 'STUDENT'] },
  { name: 'Enrollments', href: '/dashboard/enrollments', icon: '📝', roles: ['STUDENT'] },
  { name: 'Grades', href: '/dashboard/grades', icon: '📈', roles: ['TEACHER', 'STUDENT'] },
  { name: 'Attendance', href: '/dashboard/attendance', icon: '✅', roles: ['TEACHER'] },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const filteredMenuItems = menuItems.filter(item =>
    item.roles.includes(user?.role?.toUpperCase() || '')
  );

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-gray-900">UEMS</h1>
          <p className="text-sm text-gray-600 mt-1">{user?.role}</p>
        </div>

        <nav className="p-4">
          {filteredMenuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-4 py-3 mb-2 rounded-lg transition-colors ${
                pathname === item.href
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 w-64 p-4 border-t">
          <div className="mb-3">
            <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
            <p className="text-xs text-gray-600">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
