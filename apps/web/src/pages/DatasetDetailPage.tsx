import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Play, Trash2, Loader2, Split, RefreshCw, CheckCircle, XCircle, BarChart3 } from 'lucide-react'
import { datasetsApi, PreprocessingRequest, FeatureEngineeringRequest, TaskStatus } from '../lib/api'
import { useState, useEffect } from 'react'

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [splitMethod, setSplitMethod] = useState<'random' | 'time'>('random')
  const [testSize, setTestSize] = useState(0.2)
  const [timeColumn, setTimeColumn] = useState('')
  const [trainEndDate, setTrainEndDate] = useState('')

  // 预处理任务状态
  const [preprocessConfig, setPreprocessConfig] = useState<PreprocessingRequest>({
    missing_value_strategy: 'mean_fill',
    encoding_strategy: 'one_hot',
    target_columns: [],
  })
  const [preprocessTaskId, setPreprocessTaskId] = useState<string>('')
  const [preprocessTaskStatus, setPreprocessTaskStatus] = useState<TaskStatus | null>(null)
  const [preprocessPolling, setPreprocessPolling] = useState<NodeJS.Timeout | null>(null)
  const [preprocessError, setPreprocessError] = useState<string>('')

  // 特征工程任务状态
  const [featureConfig, setFeatureConfig] = useState<FeatureEngineeringRequest>({
    time_features: {
      enabled: false,
      features: ['hour', 'dayofweek', 'month'],
      column: '',
    },
    lag_features: {
      enabled: false,
      lags: [1, 6, 12, 24],
      columns: [],
    },
    rolling_features: {
      enabled: false,
      windows: [3, 6, 24],
      columns: [],
      functions: ['mean', 'std'],
    },
  })
  const [featureTaskId, setFeatureTaskId] = useState<string>('')
  const [featureTaskStatus, setFeatureTaskStatus] = useState<TaskStatus | null>(null)
  const [featurePolling, setFeaturePolling] = useState<NodeJS.Timeout | null>(null)
  const [featureError, setFeatureError] = useState<string>('')

  const { data: dataset, isLoading } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => datasetsApi.get(id!),
    enabled: !!id,
  })

  // 当 dataset 加载完成后，更新配置默认值
  useEffect(() => {
    if (dataset) {
      setPreprocessConfig(prev => ({
        ...prev,
        target_columns: dataset.target_column ? [dataset.target_column] : [],
      }))
      setFeatureConfig(prev => ({
        ...prev,
        time_features: {
          ...prev.time_features,
          column: dataset.time_column || '',
        },
        lag_features: {
          ...prev.lag_features,
          columns: dataset.target_column ? [dataset.target_column] : [],
        },
        rolling_features: {
          ...prev.rolling_features,
          columns: dataset.target_column ? [dataset.target_column] : [],
        },
      }))
    }
  }, [dataset])

  const { data: preview } = useQuery({
    queryKey: ['dataset-preview', id],
    queryFn: () => datasetsApi.preview(id!, 20),
    enabled: !!id,
  })

  const splitMutation = useMutation({
    mutationFn: () =>
      datasetsApi.split(id!, {
        split_method: splitMethod,
        test_size: testSize,
        time_column: timeColumn || dataset?.time_column,
        train_end_date: trainEndDate || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset', id] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => datasetsApi.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })

  // 预处理任务 mutation
  const preprocessMutation = useMutation({
    mutationFn: () => datasetsApi.preprocess(id!, preprocessConfig),
    onSuccess: (data) => {
      setPreprocessTaskId(data.task_id)
      // 开始轮询任务状态
      startPreprocessPolling(data.task_id)
    },
    onError: (error: Error) => {
      alert(`预处理任务提交失败: ${error.message}`)
    },
  })

  // 特征工程任务 mutation
  const featureMutation = useMutation({
    mutationFn: () => datasetsApi.featureEngineering(id!, featureConfig),
    onSuccess: (data) => {
      setFeatureTaskId(data.task_id)
      // 开始轮询任务状态
      startFeaturePolling(data.task_id)
    },
    onError: (error: Error) => {
      alert(`特征工程任务提交失败: ${error.message}`)
    },
  })

  // 开始预处理任务轮询
  const startPreprocessPolling = (taskId: string) => {
    // 清除之前的轮询
    if (preprocessPolling) {
      clearInterval(preprocessPolling)
    }

    // 立即获取一次状态
    fetchPreprocessTaskStatus(taskId)

    // 设置轮询
    const interval = setInterval(() => {
      fetchPreprocessTaskStatus(taskId)
    }, 2000)

    setPreprocessPolling(interval)
  }

  // 获取预处理任务状态
  const fetchPreprocessTaskStatus = async (taskId: string) => {
    try {
      const status = await datasetsApi.getTask(taskId)
      setPreprocessTaskStatus(status)
      setPreprocessError('')

      // 如果任务完成或失败，停止轮询
      if (status.status === 'completed' || status.status === 'failed') {
        if (preprocessPolling) {
          clearInterval(preprocessPolling)
          setPreprocessPolling(null)
        }
      }
    } catch (error: any) {
      console.error('获取预处理任务状态失败:', error)
      const errorMessage = error.message || '轮询失败，请稍后重试'
      setPreprocessError(errorMessage)
      // 出现错误后停止轮询
      if (preprocessPolling) {
        clearInterval(preprocessPolling)
        setPreprocessPolling(null)
      }
    }
  }

  // 开始特征工程任务轮询
  const startFeaturePolling = (taskId: string) => {
    // 清除之前的轮询
    if (featurePolling) {
      clearInterval(featurePolling)
    }

    // 立即获取一次状态
    fetchFeatureTaskStatus(taskId)

    // 设置轮询
    const interval = setInterval(() => {
      fetchFeatureTaskStatus(taskId)
    }, 2000)

    setFeaturePolling(interval)
  }

  // 获取特征工程任务状态
  const fetchFeatureTaskStatus = async (taskId: string) => {
    try {
      const status = await datasetsApi.getTask(taskId)
      setFeatureTaskStatus(status)
      setFeatureError('')

      // 如果任务完成或失败，停止轮询
      if (status.status === 'completed' || status.status === 'failed') {
        if (featurePolling) {
          clearInterval(featurePolling)
          setFeaturePolling(null)
        }
      }
    } catch (error: any) {
      console.error('获取特征工程任务状态失败:', error)
      const errorMessage = error.message || '轮询失败，请稍后重试'
      setFeatureError(errorMessage)
      // 出现错误后停止轮询
      if (featurePolling) {
        clearInterval(featurePolling)
        setFeaturePolling(null)
      }
    }
  }

  // 清理轮询
  useEffect(() => {
    return () => {
      if (preprocessPolling) {
        clearInterval(preprocessPolling)
      }
      if (featurePolling) {
        clearInterval(featurePolling)
      }
    }
  }, [preprocessPolling, featurePolling])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!dataset) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">数据集不存在</p>
        <Link to="/assets" className="text-blue-600 hover:text-blue-700 mt-2 inline-block">
          返回列表
        </Link>
      </div>
    )
  }

  const primaryFile = dataset.files.find(f => f.role === 'primary') || dataset.files[0]
  const columnsInfo = primaryFile?.columns_info || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/assets" className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{dataset.name}</h2>
            {dataset.description && (
              <p className="text-gray-600">{dataset.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to={`/assets/${id}/quality`}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            查看质量报告
          </Link>
          <button
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="flex items-center px-3 py-2 text-sm text-red-600 border border-red-600 rounded-lg hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            删除
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">总行数</p>
          <p className="text-2xl font-bold text-gray-900">
            {dataset.total_row_count.toLocaleString()}
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">总列数</p>
          <p className="text-2xl font-bold text-gray-900">{dataset.total_column_count}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">文件数</p>
          <p className="text-2xl font-bold text-gray-900">{dataset.files.length}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-500">已配置</p>
          <p className="text-sm text-gray-900">
            {dataset.time_column && `时间: ${dataset.time_column}`}
            {dataset.target_column && ` / 目标: ${dataset.target_column}`}
            {!dataset.time_column && !dataset.target_column && '未配置'}
          </p>
        </div>
      </div>

      {/* Column Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">列配置</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              时间列
            </label>
            <select
              value={dataset.time_column || ''}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              disabled
            >
              <option value="">未选择</option>
              {columnsInfo.map(col => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              实体列
            </label>
            <select
              value={dataset.entity_column || ''}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              disabled
            >
              <option value="">未选择</option>
              {columnsInfo.map(col => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              目标列
            </label>
            <select
              value={dataset.target_column || ''}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              disabled
            >
              <option value="">未选择</option>
              {columnsInfo.map(col => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Split Dataset */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">数据切分</h3>
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="random"
                checked={splitMethod === 'random'}
                onChange={() => setSplitMethod('random')}
                className="mr-2"
              />
              随机切分
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="time"
                checked={splitMethod === 'time'}
                onChange={() => setSplitMethod('time')}
                className="mr-2"
              />
              时间切分
            </label>
          </div>

          {splitMethod === 'random' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                测试集比例
              </label>
              <input
                type="number"
                value={testSize}
                onChange={(e) => setTestSize(parseFloat(e.target.value))}
                min={0.1}
                max={0.5}
                step={0.1}
                className="w-32 border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          )}

          {splitMethod === 'time' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  时间列
                </label>
                <select
                  value={timeColumn}
                  onChange={(e) => setTimeColumn(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">使用数据集配置</option>
                  {columnsInfo
                    .filter(c => c.is_time_candidate || c.is_datetime)
                    .map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  训练集结束日期
                </label>
                <input
                  type="text"
                  value={trainEndDate}
                  onChange={(e) => setTrainEndDate(e.target.value)}
                  placeholder="YYYY-MM-DD"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
            </div>
          )}

          <button
            onClick={() => splitMutation.mutate()}
            disabled={splitMutation.isPending}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {splitMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Split className="w-4 h-4 mr-2" />
            )}
            执行切分
          </button>

          {splitMutation.isSuccess && splitMutation.data && (
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-700 mb-2">切分完成</p>
              <div className="flex space-x-4">
                {splitMutation.data.subsets.map((subset) => (
                  <div key={subset.id} className="text-sm text-green-600">
                    <strong>{subset.name}</strong>: {subset.row_count} 行
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 预处理任务 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">预处理任务</h3>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                缺失值处理策略
              </label>
              <select
                value={preprocessConfig.missing_value_strategy}
                onChange={(e) => setPreprocessConfig(prev => ({
                  ...prev,
                  missing_value_strategy: e.target.value as 'forward_fill' | 'mean_fill' | 'drop_rows'
                }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="forward_fill">前向填充</option>
                <option value="mean_fill">均值填充</option>
                <option value="drop_rows">删除行</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                编码策略
              </label>
              <select
                value={preprocessConfig.encoding_strategy}
                onChange={(e) => setPreprocessConfig(prev => ({
                  ...prev,
                  encoding_strategy: e.target.value as 'one_hot' | 'label_encoding'
                }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="one_hot">One-Hot 编码</option>
                <option value="label_encoding">标签编码</option>
              </select>
            </div>
          </div>

          <button
            onClick={() => preprocessMutation.mutate()}
            disabled={preprocessMutation.isPending}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {preprocessMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            执行预处理
          </button>

          {preprocessTaskId && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                任务 ID: {preprocessTaskId}
              </p>
              {preprocessError && (
                <div className="p-4 rounded-lg bg-red-50 mb-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-500 mr-2" />
                    <span className="text-sm font-medium text-red-700">
                      轮询错误
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-red-600">
                    {preprocessError}
                  </p>
                </div>
              )}
              {preprocessTaskStatus && (
                <div className={`p-4 rounded-lg ${preprocessTaskStatus.status === 'completed' ? 'bg-green-50' : preprocessTaskStatus.status === 'failed' ? 'bg-red-50' : 'bg-blue-50'}`}>
                  <div className="flex items-center">
                    {preprocessTaskStatus.status === 'completed' && (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    )}
                    {preprocessTaskStatus.status === 'failed' && (
                      <XCircle className="w-5 h-5 text-red-500 mr-2" />
                    )}
                    {preprocessTaskStatus.status === 'queued' && (
                      <Loader2 className="w-5 h-5 text-blue-500 mr-2" />
                    )}
                    {preprocessTaskStatus.status === 'running' && (
                      <Loader2 className="w-5 h-5 text-blue-500 mr-2 animate-spin" />
                    )}
                    <span className="text-sm font-medium">
                      状态: {preprocessTaskStatus.status}
                    </span>
                  </div>
                  {preprocessTaskStatus.error_message && (
                    <p className="mt-2 text-sm text-red-600">
                      错误: {preprocessTaskStatus.error_message}
                    </p>
                  )}
                  {preprocessTaskStatus.result && (
                    <p className="mt-2 text-sm text-green-600">
                      结果: 处理完成
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 特征工程任务 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">特征工程任务</h3>
        <div className="space-y-4">
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={featureConfig.time_features?.enabled}
                onChange={(e) => setFeatureConfig(prev => ({
                  ...prev,
                  time_features: {
                    ...prev.time_features!,
                    enabled: e.target.checked
                  }
                }))}
                className="mr-2"
              />
              时间特征
            </label>
            {featureConfig.time_features?.enabled && (
              <div className="ml-6 mt-2 space-y-2">
                <select
                  value={featureConfig.time_features.column}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    time_features: {
                      ...prev.time_features!,
                      column: e.target.value
                    }
                  }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">选择时间列</option>
                  {columnsInfo
                    .filter(c => c.is_time_candidate || c.is_datetime)
                    .map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                </select>
                <div className="grid grid-cols-2 gap-2">
                  {(['hour', 'dayofweek', 'month', 'is_weekend'] as const).map(feature => (
                    <label key={feature} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={featureConfig.time_features.features.includes(feature)}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          time_features: {
                            ...prev.time_features,
                            features: e.target.checked
                              ? [...prev.time_features.features, feature]
                              : prev.time_features.features.filter(f => f !== feature)
                          }
                        }))}
                        className="mr-1"
                      />
                      {feature === 'dayofweek' ? '星期' : feature === 'is_weekend' ? '是否周末' : feature}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={featureConfig.lag_features?.enabled}
                onChange={(e) => setFeatureConfig(prev => ({
                  ...prev,
                  lag_features: {
                    ...prev.lag_features!,
                    enabled: e.target.checked
                  }
                }))}
                className="mr-2"
              />
              滞后特征
            </label>
            {featureConfig.lag_features?.enabled && (
              <div className="ml-6 mt-2 space-y-2">
                <input
                  type="text"
                  value={featureConfig.lag_features.lags.join(',')}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    lag_features: {
                      ...prev.lag_features!,
                      lags: e.target.value.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n))
                    }
                  }))}
                  placeholder="输入滞后阶数，如: 1,2,3"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
                <select
                  multiple
                  value={featureConfig.lag_features.columns}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    lag_features: {
                      ...prev.lag_features!,
                      columns: Array.from(e.target.selectedOptions, option => option.value)
                    }
                  }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {columnsInfo
                    .filter(c => c.is_numeric)
                    .map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                </select>
              </div>
            )}
          </div>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={featureConfig.rolling_features?.enabled}
                onChange={(e) => setFeatureConfig(prev => ({
                  ...prev,
                  rolling_features: {
                    ...prev.rolling_features!,
                    enabled: e.target.checked
                  }
                }))}
                className="mr-2"
              />
              滚动特征
            </label>
            {featureConfig.rolling_features?.enabled && (
              <div className="ml-6 mt-2 space-y-2">
                <input
                  type="text"
                  value={featureConfig.rolling_features.windows.join(',')}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    rolling_features: {
                      ...prev.rolling_features!,
                      windows: e.target.value.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n))
                    }
                  }))}
                  placeholder="输入窗口大小，如: 7,14,30"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
                <select
                  multiple
                  value={featureConfig.rolling_features.columns}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    rolling_features: {
                      ...prev.rolling_features!,
                      columns: Array.from(e.target.selectedOptions, option => option.value)
                    }
                  }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  {columnsInfo
                    .filter(c => c.is_numeric)
                    .map(col => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                </select>
                <div className="grid grid-cols-3 gap-2">
                  {(['mean', 'std', 'min', 'max', 'sum'] as const).map(func => (
                    <label key={func} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={featureConfig.rolling_features.functions.includes(func)}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          rolling_features: {
                            ...prev.rolling_features,
                            functions: e.target.checked
                              ? [...prev.rolling_features.functions, func]
                              : prev.rolling_features.functions.filter(f => f !== func)
                          }
                        }))}
                        className="mr-1"
                      />
                      {func}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => featureMutation.mutate()}
            disabled={featureMutation.isPending}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {featureMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            执行特征工程
          </button>

          {featureTaskId && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                任务 ID: {featureTaskId}
              </p>
              {featureError && (
                <div className="p-4 rounded-lg bg-red-50 mb-4">
                  <div className="flex items-center">
                    <XCircle className="w-5 h-5 text-red-500 mr-2" />
                    <span className="text-sm font-medium text-red-700">
                      轮询错误
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-red-600">
                    {featureError}
                  </p>
                </div>
              )}
              {featureTaskStatus && (
                <div className={`p-4 rounded-lg ${featureTaskStatus.status === 'completed' ? 'bg-green-50' : featureTaskStatus.status === 'failed' ? 'bg-red-50' : 'bg-blue-50'}`}>
                  <div className="flex items-center">
                    {featureTaskStatus.status === 'completed' && (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    )}
                    {featureTaskStatus.status === 'failed' && (
                      <XCircle className="w-5 h-5 text-red-500 mr-2" />
                    )}
                    {featureTaskStatus.status === 'queued' && (
                      <Loader2 className="w-5 h-5 text-blue-500 mr-2" />
                    )}
                    {featureTaskStatus.status === 'running' && (
                      <Loader2 className="w-5 h-5 text-blue-500 mr-2 animate-spin" />
                    )}
                    <span className="text-sm font-medium">
                      状态: {featureTaskStatus.status}
                    </span>
                  </div>
                  {featureTaskStatus.error_message && (
                    <p className="mt-2 text-sm text-red-600">
                      错误: {featureTaskStatus.error_message}
                    </p>
                  )}
                  {featureTaskStatus.result && (
                    <p className="mt-2 text-sm text-green-600">
                      结果: 处理完成
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Experiment */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">创建实验</h3>
          <Link
            to={`/experiments?dataset=${id}`}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
          >
            <Play className="w-4 h-4 mr-2" />
            创建训练实验
          </Link>
        </div>
      </div>

      {/* Preview */}
      {preview && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">数据预览</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {preview.columns.map((col) => (
                    <th
                      key={col}
                      className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {preview.data.slice(0, 10).map((row, i) => (
                  <tr key={i}>
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-sm text-gray-900 whitespace-nowrap">
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            显示前 {preview.preview_rows} 行，共 {preview.total_rows} 行
          </p>
        </div>
      )}
    </div>
  )
}