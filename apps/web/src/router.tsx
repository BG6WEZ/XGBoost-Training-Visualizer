import { Routes, Route, Navigate } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { AssetsPage } from './pages/AssetsPage'
import { DatasetDetailPage } from './pages/DatasetDetailPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { ExperimentDetailPage } from './pages/ExperimentDetailPage'
import { MonitorPage } from './pages/MonitorPage'
import { ComparePage } from './pages/ComparePage'

export function Router() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/assets" element={<AssetsPage />} />
      <Route path="/assets/:id" element={<DatasetDetailPage />} />
      <Route path="/experiments" element={<ExperimentsPage />} />
      <Route path="/experiments/:id" element={<ExperimentDetailPage />} />
      <Route path="/monitor" element={<MonitorPage />} />
      <Route path="/compare" element={<ComparePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}