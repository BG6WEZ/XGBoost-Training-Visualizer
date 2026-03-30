import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Loader2, CheckCircle, Clock, XCircle } from 'lucide-react'
import { experimentsApi, trainingApi } from '../lib/api'
import { useState } from 'react'

export function MonitorPage() {
  const [refreshKey] = useState(0)

  const { data: experiments } = useQuery({
    queryKey: ['experiments', refreshKey],
    queryFn: () => experimentsApi.list(),
    refetchInterval: 3000,
  })

  const runningExperiments = experiments?.filter(
    (e) => e.status === 'running' || e.status === 'queued'
  ) || []

  const recentExperiments = experiments?.filter(
    (e) => e.status === 'completed' || e.status === 'failed'
  ).slice(0, 5) || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">训练监控</h2>
        <p className="text-gray-600">实时监控训练进度和状态</p>
      </div>

      {/* Active Training */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          活跃训练 ({runningExperiments.length})
        </h3>
        {runningExperiments.length > 0 ? (
          <div className="space-y-4">
            {runningExperiments.map((exp) => (
              <RunningExperimentCard key={exp.id} experiment={exp} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p>当前没有正在运行的训练</p>
            <Link to="/experiments" className="text-blue-600 hover:text-blue-700 text-sm">
              去创建实验
            </Link>
          </div>
        )}
      </div>

      {/* Recent Completed */}
      {recentExperiments.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">最近完成</h3>
          <div className="space-y-3">
            {recentExperiments.map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
              >
                <div className="flex items-center">
                  {exp.status === 'completed' ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500 mr-3" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900">{exp.name}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(exp.created_at).toLocaleString('zh-CN')}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${
                    exp.status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {exp.status === 'completed' ? '成功' : '失败'}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function RunningExperimentCard({ experiment }: { experiment: { id: string; name: string; status: string; created_at: string } }) {
  const { data: status } = useQuery({
    queryKey: ['training-status', experiment.id],
    queryFn: () => trainingApi.getStatus(experiment.id),
    refetchInterval: 2000,
  })

  return (
    <Link
      to={`/experiments/${experiment.id}`}
      className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin mr-2" />
          <span className="font-medium text-gray-900">{experiment.name}</span>
        </div>
        <span
          className={`px-2 py-1 text-xs font-medium rounded ${
            experiment.status === 'running'
              ? 'bg-blue-100 text-blue-700'
              : 'bg-yellow-100 text-yellow-700'
          }`}
        >
          {experiment.status === 'running' ? '训练中' : '排队中'}
        </span>
      </div>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>
          {status?.started_at
            ? `开始于 ${new Date(status.started_at).toLocaleTimeString('zh-CN')}`
            : '等待开始...'}
        </span>
        <span className="font-medium text-blue-600">
          {status?.progress || 0}%
        </span>
      </div>
      {status && status.progress > 0 && (
        <div className="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-500"
            style={{ width: `${status.progress}%` }}
          />
        </div>
      )}
    </Link>
  )
}