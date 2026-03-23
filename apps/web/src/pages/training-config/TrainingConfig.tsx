import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, Database, Settings, Sliders, Play } from 'lucide-react'
import { XGBOOST_DEFAULT_PARAMS, TASK_TYPES, EARLY_STOPPING_METRICS } from '@xgboost-vis/utils'

interface XGBoostParams {
  learningRate: number
  maxDepth: number
  nEstimators: number
  subsample: number
  colsampleBytree: number
  gamma: number
  alpha: number
  lambda: number
  minChildWeight: number
  treeMethod?: string
  booster?: string
  objective?: string
  evalMetric?: string
}

interface TrainingConfig {
  taskType: 'regression' | 'classification'
  datasetId: string
  subsetId?: string
  targetColumn: string
  featureColumns: string[]
  testSize: number
  randomSeed: number
  xgboostParams: XGBoostParams
  earlyStopping: {
    enabled: boolean
    rounds: number
    metric: string
  }
  name: string
  description?: string
}

const TrainingConfig: React.FC = () => {
  const navigate = useNavigate()
  const [datasets, setDatasets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [config, setConfig] = useState<TrainingConfig>({
    taskType: 'regression',
    datasetId: '',
    targetColumn: '',
    featureColumns: [],
    testSize: 0.2,
    randomSeed: 42,
    xgboostParams: { ...XGBOOST_DEFAULT_PARAMS },
    earlyStopping: {
      enabled: true,
      rounds: 10,
      metric: 'rmse'
    },
    name: '',
    description: ''
  })
  const [selectedDataset, setSelectedDataset] = useState<any>(null)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      setLoading(true)
      // 模拟 API 调用
      const mockDatasets = [
        {
          id: '1',
          name: 'Building Energy Data',
          columns: [
            { name: 'timestamp', type: 'datetime' },
            { name: 'building_id', type: 'string' },
            { name: 'energy_consumption', type: 'number' },
            { name: 'temperature', type: 'number' },
            { name: 'humidity', type: 'number' }
          ]
        },
        {
          id: '2',
          name: 'Weather Data',
          columns: [
            { name: 'timestamp', type: 'datetime' },
            { name: 'temperature', type: 'number' },
            { name: 'humidity', type: 'number' },
            { name: 'wind_speed', type: 'number' },
            { name: 'precipitation', type: 'number' }
          ]
        }
      ]
      setDatasets(mockDatasets)
      if (mockDatasets.length > 0) {
        setConfig(prev => ({ ...prev, datasetId: mockDatasets[0].id }))
        setSelectedDataset(mockDatasets[0])
      }
    } catch (err) {
      console.error('Failed to fetch datasets', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDatasetChange = (datasetId: string) => {
    const dataset = datasets.find(d => d.id === datasetId)
    setConfig(prev => ({ ...prev, datasetId }))
    setSelectedDataset(dataset)
    setConfig(prev => ({
      ...prev,
      targetColumn: dataset?.columns.find((col: any) => col.type === 'number')?.name || '',
      featureColumns: dataset?.columns.filter((col: any) => col.type === 'number' && col.name !== 'energy_consumption').map((col: any) => col.name) || []
    }))
  }

  const handleTaskTypeChange = (taskType: 'regression' | 'classification') => {
    setConfig(prev => ({
      ...prev,
      taskType,
      xgboostParams: {
        ...prev.xgboostParams,
        objective: taskType === 'regression' ? 'reg:squarederror' : 'binary:logistic',
        evalMetric: taskType === 'regression' ? 'rmse' : 'auc'
      },
      earlyStopping: {
        ...prev.earlyStopping,
        metric: taskType === 'regression' ? 'rmse' : 'auc'
      }
    }))
  }

  const handleParamChange = (param: keyof XGBoostParams, value: number | string) => {
    setConfig(prev => ({
      ...prev,
      xgboostParams: {
        ...prev.xgboostParams,
        [param]: value
      }
    }))
  }

  const handleStartTraining = async () => {
    try {
      // 验证配置
      if (!config.name) {
        alert('请输入实验名称')
        return
      }
      if (!config.datasetId) {
        alert('请选择数据集')
        return
      }
      if (!config.targetColumn) {
        alert('请选择目标列')
        return
      }
      if (config.featureColumns.length === 0) {
        alert('请至少选择一个特征列')
        return
      }

      // 模拟 API 调用
      console.log('Starting training with config:', config)
      
      // 模拟成功响应
      const experimentId = 'exp-' + Date.now()
      alert('训练任务创建成功！')
      navigate(`/training/monitor/${experimentId}`)
    } catch (err) {
      alert('创建训练任务失败，请重试')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练配置</h1>
        <div className="card">
          <div className="loading-container">
            <p className="text-gray-500 dark:text-gray-400">加载中...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/">
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回仪表板
          </Link>
        </Button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练配置</h1>
      </div>

      {/* 实验信息 */}
      <Card>
        <CardHeader>
          <CardTitle>实验信息</CardTitle>
          <CardDescription>基本信息和数据集选择</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">实验名称</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                placeholder="输入实验名称"
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">实验描述</label>
              <textarea
                value={config.description || ''}
                onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                placeholder="输入实验描述（可选）"
                rows={3}
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">任务类型</label>
              <div className="flex space-x-4">
                {TASK_TYPES.map(task => (
                  <div key={task.value} className="flex items-center space-x-2">
                    <input
                      type="radio"
                      id={`task-${task.value}`}
                      name="taskType"
                      checked={config.taskType === task.value}
                      onChange={() => handleTaskTypeChange(task.value as 'regression' | 'classification')}
                      className="w-4 h-4 text-blue-600"
                    />
                    <label htmlFor={`task-${task.value}`}>{task.label}</label>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">数据集</label>
              <select
                value={config.datasetId}
                onChange={(e) => handleDatasetChange(e.target.value)}
                className="w-full p-2 border rounded-md"
              >
                <option value="">选择数据集</option>
                {datasets.map(dataset => (
                  <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 数据配置 */}
      {selectedDataset && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="w-5 h-5 mr-2" />
              数据配置
            </CardTitle>
            <CardDescription>目标列和特征列选择</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">目标列</label>
                <select
                  value={config.targetColumn}
                  onChange={(e) => setConfig(prev => ({ ...prev, targetColumn: e.target.value }))}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="">选择目标列</option>
                  {selectedDataset.columns
                    .filter((col: any) => col.type === 'number')
                    .map((col: any) => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">特征列</label>
                <div className="space-y-2">
                  {selectedDataset.columns
                    .filter((col: any) => col.type === 'number' && col.name !== config.targetColumn)
                    .map((col: any) => (
                      <div key={col.name} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={config.featureColumns.includes(col.name)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setConfig(prev => ({
                                ...prev,
                                featureColumns: [...prev.featureColumns, col.name]
                              }))
                            } else {
                              setConfig(prev => ({
                                ...prev,
                                featureColumns: prev.featureColumns.filter(c => c !== col.name)
                              }))
                            }
                          }}
                          className="w-4 h-4 text-blue-600"
                        />
                        <label>{col.name}</label>
                      </div>
                    ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">测试集比例</label>
                  <input
                    type="number"
                    value={config.testSize}
                    onChange={(e) => setConfig(prev => ({ ...prev, testSize: parseFloat(e.target.value) }))}
                    min="0.1"
                    max="0.9"
                    step="0.1"
                    className="w-full p-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">随机种子</label>
                  <input
                    type="number"
                    value={config.randomSeed}
                    onChange={(e) => setConfig(prev => ({ ...prev, randomSeed: parseInt(e.target.value) }))}
                    min="0"
                    className="w-full p-2 border rounded-md"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* XGBoost 参数配置 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Sliders className="w-5 h-5 mr-2" />
            XGBoost 参数配置
          </CardTitle>
          <CardDescription>核心超参数设置</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">学习率 (learning_rate)</label>
              <input
                type="range"
                min="0.001"
                max="1"
                step="0.001"
                value={config.xgboostParams.learningRate}
                onChange={(e) => handleParamChange('learningRate', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0.001</span>
                <span>{config.xgboostParams.learningRate.toFixed(3)}</span>
                <span>1.0</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">最大深度 (max_depth)</label>
              <input
                type="range"
                min="1"
                max="30"
                step="1"
                value={config.xgboostParams.maxDepth}
                onChange={(e) => handleParamChange('maxDepth', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>1</span>
                <span>{config.xgboostParams.maxDepth}</span>
                <span>30</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Estimators 数量 (n_estimators)</label>
              <input
                type="range"
                min="10"
                max="1000"
                step="10"
                value={config.xgboostParams.nEstimators}
                onChange={(e) => handleParamChange('nEstimators', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>10</span>
                <span>{config.xgboostParams.nEstimators}</span>
                <span>1000</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">子样本比例 (subsample)</label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={config.xgboostParams.subsample}
                onChange={(e) => handleParamChange('subsample', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0.1</span>
                <span>{config.xgboostParams.subsample.toFixed(1)}</span>
                <span>1.0</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">特征采样比例 (colsample_bytree)</label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={config.xgboostParams.colsampleBytree}
                onChange={(e) => handleParamChange('colsampleBytree', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0.1</span>
                <span>{config.xgboostParams.colsampleBytree.toFixed(1)}</span>
                <span>1.0</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Gamma</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={config.xgboostParams.gamma}
                onChange={(e) => handleParamChange('gamma', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0</span>
                <span>{config.xgboostParams.gamma.toFixed(1)}</span>
                <span>10</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Alpha (L1正则化)</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={config.xgboostParams.alpha}
                onChange={(e) => handleParamChange('alpha', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0</span>
                <span>{config.xgboostParams.alpha.toFixed(1)}</span>
                <span>10</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Lambda (L2正则化)</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={config.xgboostParams.lambda}
                onChange={(e) => handleParamChange('lambda', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0</span>
                <span>{config.xgboostParams.lambda.toFixed(1)}</span>
                <span>10</span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">最小子节点权重 (min_child_weight)</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.1"
                value={config.xgboostParams.minChildWeight}
                onChange={(e) => handleParamChange('minChildWeight', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>0</span>
                <span>{config.xgboostParams.minChildWeight.toFixed(1)}</span>
                <span>10</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 早停配置 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            早停配置
          </CardTitle>
          <CardDescription>防止过拟合</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.earlyStopping.enabled}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  earlyStopping: {
                    ...prev.earlyStopping,
                    enabled: e.target.checked
                  }
                }))}
                className="w-4 h-4 text-blue-600"
              />
              <label>启用早停</label>
            </div>
            {config.earlyStopping.enabled && (
              <div className="space-y-4 pl-6">
                <div>
                  <label className="block text-sm font-medium mb-2">早停轮数</label>
                  <input
                    type="number"
                    value={config.earlyStopping.rounds}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      earlyStopping: {
                        ...prev.earlyStopping,
                        rounds: parseInt(e.target.value)
                      }
                    }))}
                    min="1"
                    className="w-full p-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">早停指标</label>
                  <select
                    value={config.earlyStopping.metric}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      earlyStopping: {
                        ...prev.earlyStopping,
                        metric: e.target.value
                      }
                    }))}
                    className="w-full p-2 border rounded-md"
                  >
                    {EARLY_STOPPING_METRICS.map(metric => (
                      <option key={metric.value} value={metric.value}>{metric.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        <Button variant="default" size="lg" onClick={handleStartTraining} className="flex items-center">
          <Play className="w-4 h-4 mr-2" />
          开始训练
        </Button>
        <Button variant="outline" size="lg" asChild>
          <Link to="/">
            取消
          </Link>
        </Button>
      </div>
    </div>
  )
}

export default TrainingConfig