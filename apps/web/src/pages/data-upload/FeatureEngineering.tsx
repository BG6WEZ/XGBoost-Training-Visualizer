import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, Calendar, Clock, LineChart, X } from 'lucide-react'

interface FeatureConfig {
  timeFeatures: {
    enabled: boolean
    columns: string[]
    features: {
      hour: boolean
      dayOfWeek: boolean
      dayOfMonth: boolean
      month: boolean
      year: boolean
    }
  }
  lagFeatures: {
    enabled: boolean
    features: LagFeature[]
  }
  rollingFeatures: {
    enabled: boolean
    features: RollingFeature[]
  }
}

interface LagFeature {
  column: string
  lags: number[]
}

interface RollingFeature {
  column: string
  windows: number[]
  functions: ('mean' | 'sum' | 'min' | 'max' | 'std')[]
}

const FeatureEngineering: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [dataset, setDataset] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [featureConfig, setFeatureConfig] = useState<FeatureConfig>({
    timeFeatures: {
      enabled: true,
      columns: ['timestamp'],
      features: {
        hour: true,
        dayOfWeek: true,
        dayOfMonth: false,
        month: true,
        year: false
      }
    },
    lagFeatures: {
      enabled: true,
      features: [
        {
          column: 'energy_consumption',
          lags: [1, 2, 24]
        }
      ]
    },
    rollingFeatures: {
      enabled: true,
      features: [
        {
          column: 'energy_consumption',
          windows: [24, 48],
          functions: ['mean', 'max', 'min']
        }
      ]
    }
  })

  useEffect(() => {
    if (id) {
      fetchDataset()
    }
  }, [id])

  const fetchDataset = async () => {
    try {
      setLoading(true)
      // 模拟 API 调用
      const mockData = {
        id,
        name: 'Building Energy Data',
        columns: [
          { name: 'timestamp', type: 'datetime' },
          { name: 'building_id', type: 'string' },
          { name: 'energy_consumption', type: 'number' },
          { name: 'temperature', type: 'number' },
          { name: 'humidity', type: 'number' }
        ]
      }
      setDataset(mockData)
    } catch (err) {
      setError('Failed to fetch dataset information')
    } finally {
      setLoading(false)
    }
  }

  const handleAddLagFeature = () => {
    setFeatureConfig(prev => ({
      ...prev,
      lagFeatures: {
        ...prev.lagFeatures,
        features: [...prev.lagFeatures.features, {
          column: 'energy_consumption',
          lags: [1]
        }]
      }
    }))
  }

  const handleRemoveLagFeature = (index: number) => {
    setFeatureConfig(prev => ({
      ...prev,
      lagFeatures: {
        ...prev.lagFeatures,
        features: prev.lagFeatures.features.filter((_, i) => i !== index)
      }
    }))
  }

  const handleAddRollingFeature = () => {
    setFeatureConfig(prev => ({
      ...prev,
      rollingFeatures: {
        ...prev.rollingFeatures,
        features: [...prev.rollingFeatures.features, {
          column: 'energy_consumption',
          windows: [24],
          functions: ['mean']
        }]
      }
    }))
  }

  const handleRemoveRollingFeature = (index: number) => {
    setFeatureConfig(prev => ({
      ...prev,
      rollingFeatures: {
        ...prev.rollingFeatures,
        features: prev.rollingFeatures.features.filter((_, i) => i !== index)
      }
    }))
  }

  const handleApplyFeatures = async () => {
    try {
      // 模拟 API 调用
      console.log('Applying feature engineering with config:', featureConfig)
      
      // 模拟成功响应
      alert('特征工程应用成功！')
    } catch (err) {
      alert('应用失败，请重试')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">特征工程</h1>
        <div className="card">
          <div className="loading-container">
            <p className="text-gray-500 dark:text-gray-400">加载中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">特征工程</h1>
        <div className="card">
          <div className="error-state">
            <p className="text-red-600 dark:text-red-400">{error}</p>
            <Button variant="default" className="mt-4" onClick={() => window.location.reload()}>
              重试
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/data">
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回数据管理
          </Link>
        </Button>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">特征工程</h1>
      </div>

      {/* 时间特征 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            时间特征
          </CardTitle>
          <CardDescription>从时间列提取特征</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={featureConfig.timeFeatures.enabled}
                onChange={(e) => setFeatureConfig(prev => ({
                  ...prev,
                  timeFeatures: {
                    ...prev.timeFeatures,
                    enabled: e.target.checked
                  }
                }))}
                className="w-4 h-4 text-blue-600"
              />
              <label className="cursor-pointer">启用时间特征</label>
            </div>
            
            {featureConfig.timeFeatures.enabled && (
              <div className="space-y-4 pl-6">
                <div>
                  <label className="block text-sm font-medium mb-2">时间列</label>
                  <select
                    value={featureConfig.timeFeatures.columns[0]}
                    onChange={(e) => setFeatureConfig(prev => ({
                      ...prev,
                      timeFeatures: {
                        ...prev.timeFeatures,
                        columns: [e.target.value]
                      }
                    }))}
                    className="w-full p-2 border rounded-md"
                  >
                    {dataset?.columns.filter((col: any) => col.type === 'datetime').map((col: any) => (
                      <option key={col.name} value={col.name}>{col.name}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">提取特征</label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={featureConfig.timeFeatures.features.hour}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          timeFeatures: {
                            ...prev.timeFeatures,
                            features: {
                              ...prev.timeFeatures.features,
                              hour: e.target.checked
                            }
                          }
                        }))}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label className="cursor-pointer">小时</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={featureConfig.timeFeatures.features.dayOfWeek}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          timeFeatures: {
                            ...prev.timeFeatures,
                            features: {
                              ...prev.timeFeatures.features,
                              dayOfWeek: e.target.checked
                            }
                          }
                        }))}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label className="cursor-pointer">星期</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={featureConfig.timeFeatures.features.dayOfMonth}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          timeFeatures: {
                            ...prev.timeFeatures,
                            features: {
                              ...prev.timeFeatures.features,
                              dayOfMonth: e.target.checked
                            }
                          }
                        }))}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label className="cursor-pointer">日期</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={featureConfig.timeFeatures.features.month}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          timeFeatures: {
                            ...prev.timeFeatures,
                            features: {
                              ...prev.timeFeatures.features,
                              month: e.target.checked
                            }
                          }
                        }))}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label className="cursor-pointer">月份</label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={featureConfig.timeFeatures.features.year}
                        onChange={(e) => setFeatureConfig(prev => ({
                          ...prev,
                          timeFeatures: {
                            ...prev.timeFeatures,
                            features: {
                              ...prev.timeFeatures.features,
                              year: e.target.checked
                            }
                          }
                        }))}
                        className="w-4 h-4 text-blue-600"
                      />
                      <label className="cursor-pointer">年份</label>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 滞后特征 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            滞后特征
          </CardTitle>
          <CardDescription>创建历史值特征</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={featureConfig.lagFeatures.enabled}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    lagFeatures: {
                      ...prev.lagFeatures,
                      enabled: e.target.checked
                    }
                  }))}
                  className="w-4 h-4 text-blue-600"
                />
                <label className="cursor-pointer">启用滞后特征</label>
              </div>
              {featureConfig.lagFeatures.enabled && (
                <Button variant="outline" size="sm" onClick={handleAddLagFeature}>
                  + 添加滞后特征
                </Button>
              )}
            </div>
            
            {featureConfig.lagFeatures.enabled && (
              <div className="space-y-4 pl-6">
                {featureConfig.lagFeatures.features.map((feature, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <select
                        value={feature.column}
                        onChange={(e) => {
                          const newConfig = { ...featureConfig }
                          newConfig.lagFeatures.features[index].column = e.target.value
                          setFeatureConfig(newConfig)
                        }}
                        className="p-2 border rounded-md"
                      >
                        {dataset?.columns.filter((col: any) => col.type === 'number').map((col: any) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleRemoveLagFeature(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">滞后阶数</label>
                      <div className="flex flex-wrap gap-2">
                        {[1, 2, 3, 6, 12, 24].map(lag => (
                          <div key={lag} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={feature.lags.includes(lag)}
                              onChange={(e) => {
                                const newConfig = { ...featureConfig }
                                if (e.target.checked) {
                                  newConfig.lagFeatures.features[index].lags.push(lag)
                                } else {
                                  newConfig.lagFeatures.features[index].lags = 
                                    newConfig.lagFeatures.features[index].lags.filter(l => l !== lag)
                                }
                                setFeatureConfig(newConfig)
                              }}
                            />
                            <label className="ml-1">{lag}小时</label>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 滚动统计特征 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <LineChart className="w-5 h-5 mr-2" />
            滚动统计特征
          </CardTitle>
          <CardDescription>创建滑动窗口统计特征</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={featureConfig.rollingFeatures.enabled}
                  onChange={(e) => setFeatureConfig(prev => ({
                    ...prev,
                    rollingFeatures: {
                      ...prev.rollingFeatures,
                      enabled: e.target.checked
                    }
                  }))}
                  className="w-4 h-4 text-blue-600"
                />
                <label className="cursor-pointer">启用滚动统计特征</label>
              </div>
              {featureConfig.rollingFeatures.enabled && (
                <Button variant="outline" size="sm" onClick={handleAddRollingFeature}>
                  + 添加滚动特征
                </Button>
              )}
            </div>
            
            {featureConfig.rollingFeatures.enabled && (
              <div className="space-y-4 pl-6">
                {featureConfig.rollingFeatures.features.map((feature, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <select
                        value={feature.column}
                        onChange={(e) => {
                          const newConfig = { ...featureConfig }
                          newConfig.rollingFeatures.features[index].column = e.target.value
                          setFeatureConfig(newConfig)
                        }}
                        className="p-2 border rounded-md"
                      >
                        {dataset?.columns.filter((col: any) => col.type === 'number').map((col: any) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleRemoveRollingFeature(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">窗口大小</label>
                        <div className="flex flex-wrap gap-2">
                          {[6, 12, 24, 48, 72].map(window => (
                            <div key={window} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={feature.windows.includes(window)}
                                onChange={(e) => {
                                  const newConfig = { ...featureConfig }
                                  if (e.target.checked) {
                                    newConfig.rollingFeatures.features[index].windows.push(window)
                                  } else {
                                    newConfig.rollingFeatures.features[index].windows = 
                                      newConfig.rollingFeatures.features[index].windows.filter(w => w !== window)
                                  }
                                  setFeatureConfig(newConfig)
                                }}
                              />
                              <label className="ml-1">{window}小时</label>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">统计函数</label>
                        <div className="flex flex-wrap gap-2">
                          {(['mean', 'sum', 'min', 'max', 'std'] as const).map(func => (
                            <div key={func} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={feature.functions.includes(func)}
                                onChange={(e) => {
                                  const newConfig = { ...featureConfig }
                                  if (e.target.checked) {
                                    newConfig.rollingFeatures.features[index].functions.push(func)
                                  } else {
                                    newConfig.rollingFeatures.features[index].functions = 
                                      newConfig.rollingFeatures.features[index].functions.filter(f => f !== func)
                                  }
                                  setFeatureConfig(newConfig)
                                }}
                              />
                              <label className="ml-1">
                                {func === 'mean' && '平均值'}
                                {func === 'sum' && '总和'}
                                {func === 'min' && '最小值'}
                                {func === 'max' && '最大值'}
                                {func === 'std' && '标准差'}
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        <Button variant="default" onClick={handleApplyFeatures}>
          应用特征工程
        </Button>
        <Button variant="outline" asChild>
          <Link to={`/data/${id}/preview`}>
            返回预览
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link to="/data">
            返回列表
          </Link>
        </Button>
      </div>
    </div>
  )
}

export default FeatureEngineering