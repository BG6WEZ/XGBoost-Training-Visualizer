import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, SplitSquareHorizontal, Calendar, Building, Layers, X } from 'lucide-react'

interface SplitDefinition {
  name: string
  purpose: 'train' | 'test' | 'compare' | 'transfer_source' | 'transfer_target'
  timeRange?: {
    start: string
    end: string
  }
  spaceValues?: string[]
  rowCount: number
  percentage: number
}

const DatasetSplit: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [dataset, setDataset] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [splitType, setSplitType] = useState<'time' | 'space' | 'mixed'>('time')
  const [timeColumn, setTimeColumn] = useState('timestamp')
  const [idColumn, setIdColumn] = useState('building_id')
  const [splits, setSplits] = useState<SplitDefinition[]>([
    {
      name: '训练集',
      purpose: 'train',
      timeRange: {
        start: '2024-01-01',
        end: '2024-01-20'
      },
      rowCount: 720,
      percentage: 72
    },
    {
      name: '测试集',
      purpose: 'test',
      timeRange: {
        start: '2024-01-21',
        end: '2024-01-27'
      },
      rowCount: 216,
      percentage: 21.6
    },
    {
      name: '验证集',
      purpose: 'compare',
      timeRange: {
        start: '2024-01-28',
        end: '2024-01-31'
      },
      rowCount: 64,
      percentage: 6.4
    }
  ])

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
        rowCount: 1000,
        columns: [
          { name: 'timestamp', type: 'datetime' },
          { name: 'building_id', type: 'string' },
          { name: 'energy_consumption', type: 'number' },
          { name: 'temperature', type: 'number' },
          { name: 'humidity', type: 'number' }
        ],
        timeRange: {
          start: '2024-01-01',
          end: '2024-01-31'
        },
        buildingIds: ['B001', 'B002', 'B003', 'B004', 'B005']
      }
      setDataset(mockData)
    } catch (err) {
      setError('Failed to fetch dataset information')
    } finally {
      setLoading(false)
    }
  }

  const handleAddSplit = () => {
    setSplits([...splits, {
      name: `新子集${splits.length + 1}`,
      purpose: 'train',
      timeRange: {
        start: dataset?.timeRange.start || '',
        end: dataset?.timeRange.end || ''
      },
      rowCount: 0,
      percentage: 0
    }])
  }

  const handleRemoveSplit = (index: number) => {
    setSplits(splits.filter((_, i) => i !== index))
  }

  const handleSplitTypeChange = (type: 'time' | 'space' | 'mixed') => {
    setSplitType(type)
  }

  const handleCreateSplit = async () => {
    try {
      // 模拟 API 调用
      console.log('Creating split with config:', {
        type: splitType,
        timeColumn: splitType === 'time' || splitType === 'mixed' ? timeColumn : undefined,
        idColumn: splitType === 'space' || splitType === 'mixed' ? idColumn : undefined,
        splits
      })
      
      // 模拟成功响应
      alert('数据集切分成功！')
    } catch (err) {
      alert('切分失败，请重试')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据集切分</h1>
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据集切分</h1>
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据集切分</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <SplitSquareHorizontal className="w-5 h-5 mr-2" />
            切分配置
          </CardTitle>
          <CardDescription>为 "{dataset?.name}" 创建子数据集</CardDescription>
        </CardHeader>
        <CardContent>
          {/* 切分类型选择 */}
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">切分方式</h3>
              <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                <div className="flex items-center space-x-2 flex-1">
                  <input
                    type="radio"
                    id="time-split"
                    name="split-type"
                    checked={splitType === 'time'}
                    onChange={() => handleSplitTypeChange('time')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <label htmlFor="time-split" className="flex items-center cursor-pointer">
                    <Calendar className="w-4 h-4 mr-2" />
                    按时间切分
                  </label>
                </div>
                <div className="flex items-center space-x-2 flex-1">
                  <input
                    type="radio"
                    id="space-split"
                    name="split-type"
                    checked={splitType === 'space'}
                    onChange={() => handleSplitTypeChange('space')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <label htmlFor="space-split" className="flex items-center cursor-pointer">
                    <Building className="w-4 h-4 mr-2" />
                    按空间切分
                  </label>
                </div>
                <div className="flex items-center space-x-2 flex-1">
                  <input
                    type="radio"
                    id="mixed-split"
                    name="split-type"
                    checked={splitType === 'mixed'}
                    onChange={() => handleSplitTypeChange('mixed')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <label htmlFor="mixed-split" className="flex items-center cursor-pointer">
                    <Layers className="w-4 h-4 mr-2" />
                    混合切分
                  </label>
                </div>
              </div>
            </div>

            {/* 时间列选择 */}
            {(splitType === 'time' || splitType === 'mixed') && (
              <div>
                <label className="block text-sm font-medium mb-2">时间列</label>
                <select
                  value={timeColumn}
                  onChange={(e) => setTimeColumn(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {dataset?.columns.filter((col: any) => col.type === 'datetime').map((col: any) => (
                    <option key={col.name} value={col.name}>{col.name}</option>
                  ))}
                </select>
              </div>
            )}

            {/* ID列选择 */}
            {(splitType === 'space' || splitType === 'mixed') && (
              <div>
                <label className="block text-sm font-medium mb-2">空间列</label>
                <select
                  value={idColumn}
                  onChange={(e) => setIdColumn(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {dataset?.columns.filter((col: any) => col.type === 'string').map((col: any) => (
                    <option key={col.name} value={col.name}>{col.name}</option>
                  ))}
                </select>
              </div>
            )}

            {/* 子数据集配置 */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium">子数据集配置</h3>
                <Button variant="outline" size="sm" onClick={handleAddSplit}>
                  + 添加子数据集
                </Button>
              </div>
              
              <div className="space-y-4">
                {splits.map((split, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <input
                          type="text"
                          value={split.name}
                          onChange={(e) => {
                            const newSplits = [...splits]
                            newSplits[index].name = e.target.value
                            setSplits(newSplits)
                          }}
                          className="p-2 border rounded-md mr-2"
                        />
                        <select
                          value={split.purpose}
                          onChange={(e) => {
                            const newSplits = [...splits]
                            newSplits[index].purpose = e.target.value as any
                            setSplits(newSplits)
                          }}
                          className="p-2 border rounded-md"
                        >
                          <option value="train">训练集</option>
                          <option value="test">测试集</option>
                          <option value="compare">对比集</option>
                          <option value="transfer_source">迁移源</option>
                          <option value="transfer_target">迁移目标</option>
                        </select>
                      </div>
                      <button
                        onClick={() => handleRemoveSplit(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                    
                    {splitType === 'time' && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">开始时间</label>
                          <input
                            type="date"
                            value={split.timeRange?.start}
                            onChange={(e) => {
                              const newSplits = [...splits]
                              if (!newSplits[index].timeRange) {
                                newSplits[index].timeRange = { start: '', end: '' }
                              }
                              newSplits[index].timeRange.start = e.target.value
                              setSplits(newSplits)
                            }}
                            className="w-full p-2 border rounded-md"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-1">结束时间</label>
                          <input
                            type="date"
                            value={split.timeRange?.end}
                            onChange={(e) => {
                              const newSplits = [...splits]
                              if (!newSplits[index].timeRange) {
                                newSplits[index].timeRange = { start: '', end: '' }
                              }
                              newSplits[index].timeRange.end = e.target.value
                              setSplits(newSplits)
                            }}
                            className="w-full p-2 border rounded-md"
                          />
                        </div>
                      </div>
                    )}
                    
                    {splitType === 'space' && (
                      <div>
                        <label className="block text-sm font-medium mb-2">选择值</label>
                        <div className="flex flex-wrap gap-2">
                          {dataset?.buildingIds.map((buildingId: string) => (
                            <div key={buildingId} className="flex items-center">
                              <input
                                type="checkbox"
                                id={`building-${buildingId}`}
                                checked={split.spaceValues?.includes(buildingId)}
                                onChange={(e) => {
                                  const newSplits = [...splits]
                                  if (!newSplits[index].spaceValues) {
                                    newSplits[index].spaceValues = []
                                  }
                                  if (e.target.checked) {
                                    newSplits[index].spaceValues.push(buildingId)
                                  } else {
                                    newSplits[index].spaceValues = newSplits[index].spaceValues.filter(id => id !== buildingId)
                                  }
                                  setSplits(newSplits)
                                }}
                              />
                              <label htmlFor={`building-${buildingId}`} className="ml-1">
                                {buildingId}
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                      预计行数: {split.rowCount} ({split.percentage}%)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        <Button variant="default" onClick={handleCreateSplit}>
          创建子数据集
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

export default DatasetSplit