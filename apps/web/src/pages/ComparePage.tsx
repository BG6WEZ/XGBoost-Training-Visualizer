import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Trophy } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { experimentsApi, resultsApi } from '../lib/api'

export function ComparePage() {
  const [selectedIds, setSelectedIds] = useState<string[]>([])

  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => experimentsApi.list(),
  })

  const completedExperiments = experiments?.filter((e) => e.status === 'completed') || []

  const { data: compareResult, isLoading: isComparing } = useQuery({
    queryKey: ['compare', selectedIds],
    queryFn: () => resultsApi.compare(selectedIds),
    enabled: selectedIds.length >= 2,
  })

  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((i) => i !== id))
    } else if (selectedIds.length < 4) {
      setSelectedIds([...selectedIds, id])
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">结果对比</h2>
        <p className="text-gray-600">选择 2-4 个已完成的实验进行对比分析</p>
      </div>

      {completedExperiments.length < 2 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">需要至少 2 个已完成的实验才能进行对比</p>
          <Link to="/experiments" className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-block">
            去创建实验
          </Link>
        </div>
      ) : (
        <>
          {/* Experiment Selection */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              选择实验 ({selectedIds.length}/4)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {completedExperiments.map((exp) => (
                <button
                  key={exp.id}
                  onClick={() => toggleSelection(exp.id)}
                  className={`p-4 text-left border rounded-lg transition-colors ${
                    selectedIds.includes(exp.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{exp.name}</span>
                    {selectedIds.includes(exp.id) && (
                      <span className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(exp.created_at).toLocaleDateString('zh-CN')}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Comparison Results */}
          {selectedIds.length >= 2 && (
            <>
              {isComparing ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : compareResult && (
                <>
                  {/* Best Experiment */}
                  {compareResult.best_val_rmse && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                      <div className="flex items-center">
                        <Trophy className="w-6 h-6 text-green-600 mr-2" />
                        <div>
                          <h3 className="font-semibold text-green-900">最佳模型</h3>
                          <p className="text-sm text-green-700">
                            验证 RMSE: {compareResult.best_val_rmse.toFixed(4)}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Metrics Comparison Table */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">指标对比</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              实验名称
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              训练 RMSE
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              验证 RMSE
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              树数量
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              最大深度
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                              学习率
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {compareResult.experiments.map((exp) => (
                            <tr
                              key={exp.experiment_id}
                              className={
                                exp.experiment_id === compareResult.comparison?.best_experiment
                                  ? 'bg-green-50'
                                  : ''
                              }
                            >
                              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                <Link
                                  to={`/experiments/${exp.experiment_id}`}
                                  className="hover:text-blue-600"
                                >
                                  {exp.name}
                                </Link>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {exp.metrics.train_rmse?.toFixed(4) || '-'}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {exp.metrics.val_rmse?.toFixed(4) || '-'}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {exp.config?.xgboost_params?.n_estimators || '-'}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {exp.config?.xgboost_params?.max_depth || '-'}
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">
                                {exp.config?.xgboost_params?.learning_rate || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Chart */}
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">RMSE 对比图</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={compareResult.experiments.map((exp) => ({
                            name: exp.name.slice(0, 15) + (exp.name.length > 15 ? '...' : ''),
                            train_rmse: exp.metrics.train_rmse,
                            val_rmse: exp.metrics.val_rmse,
                          }))}
                          layout="vertical"
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis type="number" />
                          <YAxis dataKey="name" type="category" width={100} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="train_rmse" fill="#3b82f6" name="训练 RMSE" />
                          <Bar dataKey="val_rmse" fill="#10b981" name="验证 RMSE" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}