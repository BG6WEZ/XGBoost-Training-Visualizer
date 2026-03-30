import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Database,
  FlaskConical,
  LineChart,
  BarChart3,
  Home
} from 'lucide-react'

interface AppLayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: '首页', icon: Home },
  { path: '/assets', label: '数据资产', icon: Database },
  { path: '/experiments', label: '实验管理', icon: FlaskConical },
  { path: '/monitor', label: '训练监控', icon: LineChart },
  { path: '/compare', label: '结果对比', icon: BarChart3 },
]

export function AppLayout({ children }: AppLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900">
                XGBoost Training Visualizer
              </h1>
              <span className="text-sm text-gray-500">
                建筑能耗时序建模工作台
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-4rem)] sticky top-16">
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path))

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}