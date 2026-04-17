import { Routes, Route, Navigate } from 'react-router-dom'
import { AssetsPage } from './pages/AssetsPage'
import { DatasetDetailPage } from './pages/DatasetDetailPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { ExperimentDetailPage } from './pages/ExperimentDetailPage'
import { MonitorPage } from './pages/MonitorPage'
import { ComparePage } from './pages/ComparePage'
import { QualityReportPage } from './pages/QualityReportPage'
import { LoginPage } from './pages/LoginPage'
import { AdminUsersPage } from './pages/AdminUsersPage'
import { useAuth } from './contexts/AuthContext'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, mustChangePassword } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Block access to business routes if user must change password
  if (mustChangePassword) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, isAdmin } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isAdmin) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">需要管理员权限才能访问此页面</p>
      </div>
    )
  }

  return <>{children}</>
}

export function Router() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AssetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets/:id"
        element={
          <ProtectedRoute>
            <DatasetDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets/:id/quality"
        element={
          <ProtectedRoute>
            <QualityReportPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/experiments"
        element={
          <ProtectedRoute>
            <ExperimentsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/experiments/:id"
        element={
          <ProtectedRoute>
            <ExperimentDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/monitor"
        element={
          <ProtectedRoute>
            <MonitorPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/compare"
        element={
          <ProtectedRoute>
            <ComparePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <AdminUsersPage />
          </AdminRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
