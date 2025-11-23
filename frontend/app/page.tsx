import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-2xl mx-auto px-4 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          University Education Management System
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Production-grade full-stack application for managing university operations
        </p>

        <div className="space-y-4">
          <Link
            href="/login"
            className="inline-block px-8 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition"
          >
            Sign In
          </Link>

          <div className="mt-8 bg-white p-6 rounded-lg shadow-md text-left">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Features</h2>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>✅ Role-Based Access Control (Admin, Teacher, Student)</li>
              <li>✅ Course Management with Enrollment Tracking</li>
              <li>✅ Stripe Payment Integration (Test Mode)</li>
              <li>✅ Real-Time Analytics Dashboard</li>
              <li>✅ Prometheus Metrics for Monitoring</li>
              <li>✅ Structured JSON Logging</li>
              <li>✅ Kubernetes-Ready with Health Probes</li>
            </ul>
          </div>

          <div className="mt-6 bg-blue-50 p-4 rounded-lg text-left">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Tech Stack</h3>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
              <div>
                <strong>Backend:</strong> FastAPI, SQLAlchemy, PostgreSQL
              </div>
              <div>
                <strong>Frontend:</strong> Next.js 14, Tailwind CSS
              </div>
              <div>
                <strong>DevOps:</strong> Docker, Terraform, GitLab CI
              </div>
              <div>
                <strong>Cloud:</strong> Azure (AKS, ACR)
              </div>
              <div>
                <strong>Monitoring:</strong> Prometheus, Grafana
              </div>
              <div>
                <strong>Payments:</strong> Stripe API
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
