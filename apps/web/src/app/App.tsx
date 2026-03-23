import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// 布局组件
import Layout from '../components/layout/Layout'

// 页面组件
import Dashboard from '../pages/dashboard/Dashboard'
import DataUpload from '../pages/data-upload/DataUpload'
import DatasetPreview from '../pages/data-upload/DatasetPreview'
import DatasetSplit from '../pages/data-upload/DatasetSplit'
import FeatureEngineering from '../pages/data-upload/FeatureEngineering'
import TrainingConfig from '../pages/training-config/TrainingConfig'
import TrainingMonitor from '../pages/training-monitor/TrainingMonitor'
import TrainingResults from '../pages/training-results/TrainingResults'
import Experiments from '../pages/experiments/Experiments'
import CompareExperiments from '../pages/compare/CompareExperiments'
import TransferLearning from '../pages/transfer/TransferLearning'
import Settings from '../pages/settings/Settings'

// 创建 QueryClient 实例
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/data" element={<DataUpload />} />
            <Route path="/data/:id/preview" element={<DatasetPreview />} />
            <Route path="/data/:id/split" element={<DatasetSplit />} />
            <Route path="/data/:id/features" element={<FeatureEngineering />} />
            <Route path="/training/config" element={<TrainingConfig />} />
            <Route path="/training/monitor/:id" element={<TrainingMonitor />} />
            <Route path="/training/results/:id" element={<TrainingResults />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/compare" element={<CompareExperiments />} />
            <Route path="/transfer" element={<TransferLearning />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App