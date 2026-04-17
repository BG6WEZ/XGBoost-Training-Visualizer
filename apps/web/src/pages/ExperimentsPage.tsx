import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { Plus, Loader2, Play, Trash2, Clock, CheckCircle, XCircle, AlertTriangle, Users, ListOrdered, Filter, X, Tag, Calendar, Search } from 'lucide-react'
import { experimentsApi, datasetsApi, ExperimentListResponse, ParamTemplateItem, ExperimentFilterParams } from '../lib/api'
import { validateTrainingParams, FieldError } from '../lib/validation'

const TEMPLATE_LABELS: Record<string, string> = {
  conservative: '保守 (防过拟合)',
  balanced: '平衡 (推荐)',
  aggressive: '激进 (快速探索)',
}

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '待启动' },
  { value: 'queued', label: '排队中' },
  { value: 'running', label: '训练中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
  { value: 'cancelled', label: '已取消' },
]

const TAG_MATCH_MODES = [
  { value: 'any', label: '任一匹配' },
  { value: 'all', label: '全部匹配' },
]

export function ExperimentsPage() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const preselectedDataset = searchParams.get('dataset')

  const [showCreate, setShowCreate] = useState(!!preselectedDataset)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string>('balanced')
  const [validationErrors, setValidationErrors] = useState<FieldError[]>([])
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dataset_id: preselectedDataset || '',
    task_type: 'regression',
    n_estimators: 100,
    max_depth: 6,
    learning_rate: 0.1,
    subsample: 1.0,
    colsample_bytree: 1.0,
    early_stopping_rounds: 10,
    tags: '',
  })

  const [filterParams, setFilterParams] = useState<ExperimentFilterParams>({})

  const { data: experiments, isLoading } = useQuery({
    queryKey: ['experiments', filterParams],
    queryFn: () => experimentsApi.list(filterParams),
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  })

  const { data: templates } = useQuery({
    queryKey: ['param-templates'],
    queryFn: experimentsApi.getParamTemplates,
  })

  const { data: queueStats } = useQuery({
    queryKey: ['queue-stats'],
    queryFn: experimentsApi.getQueueStats,
    refetchInterval: 3000,
  })

  const applyTemplate = (templateName: string) => {
    if (!templates?.templates?.[templateName as keyof typeof templates.templates]) return
    const t: ParamTemplateItem = templates.templates[templateName as keyof typeof templates.templates]
    const newFormData = {
      ...formData,
      n_estimators: t.n_estimators,
      max_depth: t.max_depth,
      learning_rate: t.learning_rate,
      subsample: t.subsample,
      colsample_bytree: t.colsample_bytree,
      early_stopping_rounds: t.early_stopping_rounds,
    }
    setFormData(newFormData)
    setSelectedTemplate(templateName)
    
    const result = validateTrainingParams({
      learning_rate: t.learning_rate,
      max_depth: t.max_depth,
      n_estimators: t.n_estimators,
      subsample: t.subsample,
      colsample_bytree: t.colsample_bytree,
      early_stopping_rounds: t.early_stopping_rounds,
    })
    setValidationErrors(result.fieldErrors)
  }

  const createMutation = useMutation({
    mutationFn: () =>
      experimentsApi.create({
        name: formData.name,
        description: formData.description || undefined,
        dataset_id: formData.dataset_id,
        config: {
          task_type: formData.task_type,
          test_size: 0.2,
          xgboost_params: {
            n_estimators: formData.n_estimators,
            max_depth: formData.max_depth,
            learning_rate: formData.learning_rate,
            subsample: formData.subsample,
            colsample_bytree: formData.colsample_bytree,
          },
          early_stopping_rounds: formData.early_stopping_rounds,
        },
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(t => t) : undefined,
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
        subsample: 1.0,
        colsample_bytree: 1.0,
        early_stopping_rounds: 10,
        tags: '',
      })
      setSelectedTemplate('balanced')
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
    
    const result = validateTrainingParams({
      learning_rate: formData.learning_rate,
      max_depth: formData.max_depth,
      n_estimators: formData.n_estimators,
      subsample: formData.subsample,
      colsample_bytree: formData.colsample_bytree,
      early_stopping_rounds: formData.early_stopping_rounds,
    })
    
    if (!result.valid) {
      setValidationErrors(result.fieldErrors)
      return
    }
    
    setValidationErrors([])
    createMutation.mutate()
  }

  const handleClearFilters = () => {
    setFilterParams({})
  }

  const hasActiveFilters = 
    filterParams.status || 
    filterParams.tags || 
    filterParams.name_contains || 
    filterParams.created_after || 
    filterParams.created_before

  const isFiltering = hasActiveFilters

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">实验管理</h2>
          <p className="text-gray-600">创建、配置和管理训练实验</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-blue-50 text-blue-700 border-blue-300'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            <Filter className="w-4 h-4 mr-2" />
            筛选
            {hasActiveFilters && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full">
                {[filterParams.status, filterParams.tags, filterParams.name_contains, filterParams.created_after, filterParams.created_before].filter(Boolean).length}
              </span>
            )}
          </button>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            创建实验
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">筛选条件</h3>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center text-sm text-gray-500 hover:text-gray-700"
              >
                <X className="w-4 h-4 mr-1" />
                清空筛选
              </button>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Search className="w-4 h-4 inline mr-1" />
                名称搜索
              </label>
              <input
                type="text"
                value={filterParams.name_contains || ''}
                onChange={(e) => setFilterParams({ ...filterParams, name_contains: e.target.value || undefined })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                placeholder="搜索实验名称..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                状态
              </label>
              <select
                value={filterParams.status || ''}
                onChange={(e) => setFilterParams({ ...filterParams, status: e.target.value || undefined })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Tag className="w-4 h-4 inline mr-1" />
                标签筛选
              </label>
              <input
                type="text"
                value={filterParams.tags || ''}
                onChange={(e) => setFilterParams({ ...filterParams, tags: e.target.value || undefined })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                placeholder="标签1,标签2..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标签匹配模式
              </label>
              <select
                value={filterParams.tag_match_mode || 'any'}
                onChange={(e) => setFilterParams({ ...filterParams, tag_match_mode: e.target.value as 'any' | 'all' })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                {TAG_MATCH_MODES.map((mode) => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                创建时间起始
              </label>
              <input
                type="date"
                value={filterParams.created_after ? filterParams.created_after.split('T')[0] : ''}
                onChange={(e) => setFilterParams({ 
                  ...filterParams, 
                  created_after: e.target.value ? `${e.target.value}T00:00:00` : undefined 
                })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                创建时间截止
              </label>
              <input
                type="date"
                value={filterParams.created_before ? filterParams.created_before.split('T')[0] : ''}
                onChange={(e) => setFilterParams({ 
                  ...filterParams, 
                  created_before: e.target.value ? `${e.target.value}T23:59:59` : undefined 
                })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">创建新实验</h3>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              参数模板
            </label>
            <div className="flex gap-2">
              {['conservative', 'balanced', 'aggressive'].map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => applyTemplate(key)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg border transition-colors ${
                    selectedTemplate === key
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {TEMPLATE_LABELS[key]}
                </button>
              ))}
            </div>
            {templates?.templates?.[selectedTemplate as keyof typeof templates.templates] && (
              <p className="mt-1 text-xs text-gray-500">
                {templates.templates[selectedTemplate as keyof typeof templates.templates].description}
              </p>
            )}
          </div>
          
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
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Tag className="w-4 h-4 inline mr-1" />
                标签
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="标签1, 标签2, ...（逗号分隔，可选）"
              />
              <p className="mt-1 text-xs text-gray-500">
                多个标签用逗号分隔，创建后可在实验列表中按标签筛选
              </p>
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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                子采样 (subsample)
              </label>
              <input
                type="number"
                value={formData.subsample}
                onChange={(e) => setFormData({ ...formData, subsample: parseFloat(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={0.1}
                max={1}
                step={0.1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                列采样 (colsample_bytree)
              </label>
              <input
                type="number"
                value={formData.colsample_bytree}
                onChange={(e) => setFormData({ ...formData, colsample_bytree: parseFloat(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={0.1}
                max={1}
                step={0.1}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                早停轮数 (early_stopping_rounds)
              </label>
              <input
                type="number"
                value={formData.early_stopping_rounds}
                onChange={(e) => setFormData({ ...formData, early_stopping_rounds: parseInt(e.target.value) })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                min={1}
                max={100}
              />
            </div>
          </div>
          <div className="mt-4 flex space-x-3">
            <button
              onClick={handleCreate}
              disabled={createMutation.isPending || !formData.name || !formData.dataset_id || validationErrors.length > 0}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              创建
            </button>
            <button
              onClick={() => {
                setShowCreate(false)
                setValidationErrors([])
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              取消
            </button>
          </div>
          
          {validationErrors.length > 0 && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
                <div>
                  <p className="font-medium text-red-800">参数配置存在以下问题：</p>
                  <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                    {validationErrors.map((error, index) => (
                      <li key={index} className="flex items-start">
                        <span className="font-medium">{error.fields.join(', ')}</span>
                        <span className="ml-2 text-gray-600">{error.suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Experiments List */}
      {queueStats && (queueStats.running_count > 0 || queueStats.queued_count > 0) && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">
                运行中: {queueStats.running_count}/{queueStats.max_concurrency}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">
                排队中: {queueStats.queued_count}
              </span>
            </div>
            {queueStats.available_slots > 0 && (
              <span className="text-sm text-green-700">
                可用槽位: {queueStats.available_slots}
              </span>
            )}
          </div>
        </div>
      )}

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
                  标签
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
                  queuePosition={queueStats?.queue_positions?.[exp.id]}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          {isFiltering ? (
            <>
              <Filter className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">没有找到匹配的实验</p>
              <button
                onClick={handleClearFilters}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                清空筛选条件
              </button>
            </>
          ) : (
            <>
              <p className="text-gray-500">暂无实验</p>
              <button
                onClick={() => setShowCreate(true)}
                className="mt-4 text-blue-600 hover:text-blue-700 text-sm"
              >
                创建第一个实验
              </button>
            </>
          )}
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
  queuePosition,
}: {
  experiment: ExperimentListResponse
  onStart: () => void
  onDelete: () => void
  isStarting: boolean
  isDeleting: boolean
  queuePosition?: number
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
        <div className="flex flex-wrap gap-1">
          {experiment.tags && experiment.tags.length > 0 ? (
            experiment.tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
              >
                <Tag className="w-3 h-3 mr-1" />
                {tag}
              </span>
            ))
          ) : (
            <span className="text-sm text-gray-400">-</span>
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
          <Icon className={`w-3 h-3 mr-1 ${experiment.status === 'running' ? 'animate-spin' : ''}`} />
          {config.label}
          {experiment.status === 'queued' && queuePosition && (
            <span className="ml-1">#{queuePosition}</span>
          )}
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
