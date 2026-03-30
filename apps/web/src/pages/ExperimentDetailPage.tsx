import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Loader2, Download } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { experimentsApi, resultsApi, trainingApi } from '../lib/api'
import { useEffect, useState } from 'react'

export function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [pollStatus, setPollStatus] = useState(false)

  const { data: experiment, isLoading: isLoadingExp } = useQuery({
    queryKey: ['experiment', id],
    queryFn: () => experimentsApi.get(id!),
    enabled: !!id,
  })

  const { data: trainingStatus } = useQuery({
    queryKey: ['training-status', id],
    queryFn: () => trainingApi.getStatus(id!),
    enabled: !!id && pollStatus,
    refetchInterval: pollStatus ? 2000 : false,
  })

  const { data: results } = useQuery({
    queryKey: ['results', id],
    queryFn: () => resultsApi.get(id!),
    enabled: !!id && experiment?.status === 'completed',
  })

  const { data: metricsHistory } = useQuery({
    queryKey: ['metrics-history', id],
    queryFn: () => resultsApi.getMetricsHistory(id!),
    enabled: !!id && experiment?.status === 'completed',
  })

  const { data: featureImportance } = useQuery({
    queryKey: ['feature-importance', id],
    queryFn: () => resultsApi.getFeatureImportance(id!, 15),
    enabled: !!id && experiment?.status === 'completed',
  })

  useEffect(() => {
    if (experiment?.status === 'running' || experiment?.status === 'queued') {
      setPollStatus(true)
    } else {
      setPollStatus(false)
    }
  }, [experiment?.status])

  if (isLoadingExp) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!experiment) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">实验不存在</p>
        <Link to="/experiments" className="text-blue-600 hover:text-blue-700 mt-2 inline-block">
          返回列表
        </Link>
      </div>
    )
  }

  const isRunning = experiment.status === 'running' || experiment.status === 'queued'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link to="/experiments" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-gray-900">{experiment.name}</h2>
          {experiment.description && (
            <p className="text-gray-600">{experiment.description}</p>
          )}
        </div>
        {experiment.status === 'completed' && results?.model && (
          <a
            href={resultsApi.downloadModel(id!)}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4 mr-2" />
            下载模型
          </a>
        )}
      </div>

      {/* Status Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">实验状态</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">状态</p>
            <p className="text-lg font-semibold">
              {isRunning ? (
                <span className="text-blue-600 flex items-center">
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                  {trainingStatus?.status || experiment.status}
                </span>
              ) : experiment.status === 'completed' ? (
                <span className="text-green-600">已完成</span>
              ) : experiment.status === 'failed' ? (
                <span className="text-red-600">失败</span>
              ) : (
                <span className="text-gray-600">{experiment.status}</span>
              )}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">进度</p>
            <p className="text-lg font-semibold">{trainingStatus?.progress || 0}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">开始时间</p>
            <p className="text-sm">
              {experiment.started_at
                ? new Date(experiment.started_at).toLocaleString('zh-CN')
                : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">结束时间</p>
            <p className="text-sm">
              {experiment.finished_at
                ? new Date(experiment.finished_at).toLocaleString('zh-CN')
                : '-'}
            </p>
          </div>
        </div>
        {experiment.error_message && (
          <div className="mt-4 p-3 bg-red-50 rounded-lg">
            <p className="text-sm text-red-700">{experiment.error_message}</p>
          </div>
        )}
      </div>

      {/* Config */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">训练配置</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500">任务类型</p>
            <p className="font-medium">{experiment.config?.task_type || 'regression'}</p>
          </div>
          <div>
            <p className="text-gray-500">树数量</p>
            <p className="font-medium">{experiment.config?.xgboost_params?.n_estimators || '-'}</p>
          </div>
          <div>
            <p className="text-gray-500">最大深度</p>
            <p className="font-medium">{experiment.config?.xgboost_params?.max_depth || '-'}</p>
          </div>
          <div>
            <p className="text-gray-500">学习率</p>
            <p className="font-medium">{experiment.config?.xgboost_params?.learning_rate || '-'}</p>
          </div>
        </div>
      </div>

      {/* Results */}
      {results && (
        <>
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">训练结果</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">训练 RMSE</p>
                <p className="text-xl font-bold text-gray-900">
                  {results.metrics?.train_rmse?.toFixed(4) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">验证 RMSE</p>
                <p className="text-xl font-bold text-gray-900">
                  {results.metrics?.val_rmse?.toFixed(4) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">R²</p>
                <p className="text-xl font-bold text-gray-900">
                  {results.metrics?.r2?.toFixed(4) || '-'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">训练时间</p>
                <p className="text-xl font-bold text-gray-900">
                  {results.training_time_seconds?.toFixed(1) || '-'}s
                </p>
              </div>
            </div>
          </div>

          {/* Loss Curve */}
          {metricsHistory && metricsHistory.iterations.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">损失曲线</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={metricsHistory.iterations.map((_, i) => ({
                      iteration: i + 1,
                      train: metricsHistory.train_loss[i],
                      val: metricsHistory.val_loss[i],
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="iteration" label={{ value: '迭代次数', position: 'bottom' }} />
                    <YAxis label={{ value: 'RMSE', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="train" stroke="#3b82f6" name="训练集" />
                    <Line type="monotone" dataKey="val" stroke="#10b981" name="验证集" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Feature Importance */}
          {featureImportance && featureImportance.features.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">特征重要性 (Top 15)</h3>
              <div className="space-y-2">
                {featureImportance.features.map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <span className="w-32 text-sm text-gray-600 truncate">{feature.feature_name}</span>
                    <div className="flex-1 h-4 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500"
                        style={{ width: `${feature.importance_pct}%` }}
                      />
                    </div>
                    <span className="w-20 text-right text-sm text-gray-600">
                      {feature.importance_pct.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}