import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, Loader2, Play, Trash2, Clock, CheckCircle, XCircle } from 'lucide-react'
import { experimentsApi, datasetsApi, ExperimentListResponse } from '../lib/api'

export function ExperimentsPage() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const preselectedDataset = searchParams.get('dataset')

  const [showCreate, setShowCreate] = useState(!!preselectedDataset)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dataset_id: preselectedDataset || '',
    task_type: 'regression',
    n_estimators: 100,
    max_depth: 6,
    learning_rate: 0.1,
  })

  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => experimentsApi.list(),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      experimentsApi.create({
        name: formData.name,
        description: formData.description || undefined,
        dataset_id: formData.dataset_id,
        config: {
          task_type: formData.task_type,
          xgboost_params: {
            n_estimators: formData.n_estimators,
            max_depth: formData.max_depth,
            learning_rate: formData.learning_rate,
          },
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
      setShowCreate(false)
      setFormData({
        name: '',
        description: '',
        dataset_id: preselectedDataset || '',
        task_type: 'regression',
        n_estimators: 100,
        max_depth: 6,
        learning_rate: 0.1,
      })
    },
  })

  const startMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.start(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => experimentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })

  const handleCreate = () => {
    if (!formData.name || !formData.dataset_id) return
    createMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">实验管理</h2>
          <p className="text-gray-600">创建、配置和管理训练实验</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          创建实验
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">创建新实验</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                实验名称 *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="输入实验名称"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                数据集 *
              </label>
              <select
                value={formData.dataset_id}
                onChange={(e) => setFormData({ ...formData, dataset_id: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="">选择数据集</option>
                {datasets?.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                描述
              </label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="实验描述（可选）"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                树的数量 (n_estimators)
              </label>
              <input
                type="number"
                value={formData.n_estimators}
                onChange={(e) => setFormData({ ...formData, n_estimators: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={1}
                max={1000}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最大深度 (max_depth)
              </label>
              <input
                type="number"
                value={formData.max_depth}
                onChange={(e) => setFormData({ ...formData, max_depth: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={1}
                max={20}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                学习率 (learning_rate)
              </label>
              <input
                type="number"
                value={formData.learning_rate}
                onChange={(e) => setFormData({ ...formData, learning_rate: parseFloat(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={0.001}
                max={1}
                step={0.01}
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button
              onClick={handleCreate}
              disabled={createMutation.isPending || !formData.name || !formData.dataset_id}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              创建
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* Experiments List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : experiments && experiments.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  实验名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {experiments.map((exp) => (
                <ExperimentRow
                  key={exp.id}
                  experiment={exp}
                  onStart={() => startMutation.mutate(exp.id)}
                  onDelete={() => deleteMutation.mutate(exp.id)}
                  isStarting={startMutation.isPending}
                  isDeleting={deleteMutation.isPending}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">暂无实验</p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-4 text-blue-600 hover:text-blue-700 text-sm"
          >
            创建第一个实验
          </button>
        </div>
      )}
    </div>
  )
}

function ExperimentRow({
  experiment,
  onStart,
  onDelete,
  isStarting,
  isDeleting,
}: {
  experiment: ExperimentListResponse
  onStart: () => void
  onDelete: () => void
  isStarting: boolean
  isDeleting: boolean
}) {
  const statusConfig = {
    pending: { color: 'bg-gray-100 text-gray-700', icon: Clock, label: '待启动' },
    queued: { color: 'bg-yellow-100 text-yellow-700', icon: Clock, label: '排队中' },
    running: { color: 'bg-blue-100 text-blue-700', icon: Loader2, label: '训练中' },
    completed: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: '已完成' },
    failed: { color: 'bg-red-100 text-red-700', icon: XCircle, label: '失败' },
    cancelled: { color: 'bg-gray-100 text-gray-700', icon: XCircle, label: '已取消' },
  }

  const config = statusConfig[experiment.status as keyof typeof statusConfig] || statusConfig.pending
  const Icon = config.icon

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 whitespace-nowrap">
        <Link to={`/experiments/${experiment.id}`} className="text-gray-900 hover:text-blue-600">
          <div className="font-medium">{experiment.name}</div>
          {experiment.description && (
            <div className="text-sm text-gray-500">{experiment.description}</div>
          )}
        </Link>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
          <Icon className={`w-3 h-3 mr-1 ${experiment.status === 'running' ? 'animate-spin' : ''}`} />
          {config.label}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {new Date(experiment.created_at).toLocaleString('zh-CN')}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        {experiment.status === 'pending' && (
          <button
            onClick={onStart}
            disabled={isStarting}
            className="text-green-600 hover:text-green-700 mr-3 disabled:opacity-50"
          >
            {isStarting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : <Play className="w-4 h-4 inline" />}
            <span className="ml-1">启动</span>
          </button>
        )}
        {(experiment.status === 'pending' || experiment.status === 'completed' || experiment.status === 'failed') && (
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-700 disabled:opacity-50"
          >
            {isDeleting ? <Loader2 className="w-4 h-4 animate-spin inline" /> : <Trash2 className="w-4 h-4 inline" />}
            <span className="ml-1">删除</span>
          </button>
        )}
      </td>
    </tr>
  )
}