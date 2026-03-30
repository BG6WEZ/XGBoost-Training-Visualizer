import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Database, FlaskConical, LineChart, ArrowRight } from 'lucide-react'
import { datasetsApi, experimentsApi } from '../lib/api'

export function HomePage() {
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  })

  const { data: experiments } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => experimentsApi.list(),
  })

  const runningExperiments = experiments?.filter(e => e.status === 'running' || e.status === 'queued') || []
  const completedExperiments = experiments?.filter(e => e.status === 'completed') || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">欢迎使用 XGBoost 训练可视化工具</h2>
        <p className="mt-2 text-gray-600">
          面向建筑能耗时序建模的实验工作台，支持数据资产管理、模型训练、实验对比与分析
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">数据集</p>
              <p className="text-3xl font-bold text-gray-900">{datasets?.length || 0}</p>
            </div>
            <Database className="w-8 h-8 text-blue-500" />
          </div>
          <Link
            to="/assets"
            className="mt-4 flex items-center text-sm text-blue-600 hover:text-blue-700"
          >
            查看全部 <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">实验总数</p>
              <p className="text-3xl font-bold text-gray-900">{experiments?.length || 0}</p>
            </div>
            <FlaskConical className="w-8 h-8 text-green-500" />
          </div>
          <Link
            to="/experiments"
            className="mt-4 flex items-center text-sm text-blue-600 hover:text-blue-700"
          >
            查看全部 <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">训练中</p>
              <p className="text-3xl font-bold text-gray-900">{runningExperiments.length}</p>
            </div>
            <LineChart className="w-8 h-8 text-orange-500" />
          </div>
          <Link
            to="/monitor"
            className="mt-4 flex items-center text-sm text-blue-600 hover:text-blue-700"
          >
            训练监控 <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">快速开始</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/assets"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Database className="w-6 h-6 text-blue-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">扫描数据资产</p>
              <p className="text-sm text-gray-500">从 dataset/ 目录导入</p>
            </div>
          </Link>

          <Link
            to="/experiments"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FlaskConical className="w-6 h-6 text-green-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">创建实验</p>
              <p className="text-sm text-gray-500">配置并启动训练</p>
            </div>
          </Link>

          <Link
            to="/monitor"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <LineChart className="w-6 h-6 text-orange-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">训练监控</p>
              <p className="text-sm text-gray-500">实时查看训练进度</p>
            </div>
          </Link>

          <Link
            to="/compare"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <LineChart className="w-6 h-6 text-purple-500 mr-3" />
            <div>
              <p className="font-medium text-gray-900">结果对比</p>
              <p className="text-sm text-gray-500">比较多个实验结果</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Experiments */}
      {completedExperiments.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">最近完成的实验</h3>
          <div className="space-y-3">
            {completedExperiments.slice(0, 5).map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900">{exp.name}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(exp.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded">
                  已完成
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}