import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, BarChart3, Download, Trash2, Save, LineChart } from 'lucide-react'
import { Bar, Line, Pie } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

interface ModelMetrics {
  rmse: number
  mae: number
  r2: number
  mse: number
  mape: number
}

interface FeatureImportance {
  feature: string
  importance: number
}

interface PredictionData {
  actual: number
  predicted: number
  index: number
}

interface ExperimentResult {
  id: string
  name: string
  description: string
  taskType: 'regression' | 'classification'
  datasetId: string
  datasetName: string
  targetColumn: string
  featureColumns: string[]
  trainingTime: number
  metrics: {
    train: ModelMetrics
    val: ModelMetrics
    test: ModelMetrics
  }
  featureImportance: FeatureImportance[]
  predictions: PredictionData[]
  modelInfo: {
    version: string
    parameters: Record<string, any>
    timestamp: string
  }
}

const TrainingResults: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<ExperimentResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchResults()
  }, [id])

  const fetchResults = async () => {
    try {
      setLoading(true)
      // 模拟 API 调用
      const mockResult: ExperimentResult = {
        id: id || 'exp-123',
        name: '建筑能耗预测实验',
        description: '使用 XGBoost 预测建筑能耗',
        taskType: 'regression',
        datasetId: '1',
        datasetName: 'Building Energy Data',
        targetColumn: 'energy_consumption',
        featureColumns: ['temperature', 'humidity', 'wind_speed', 'precipitation'],
        trainingTime: 125,
        metrics: {
          train: {
            rmse: 0.45,
            mae: 0.32,
            r2: 0.92,
            mse: 0.20,
            mape: 5.2
          },
          val: {
            rmse: 0.52,
            mae: 0.38,
            r2: 0.89,
            mse: 0.27,
            mape: 6.1
          },
          test: {
            rmse: 0.55,
            mae: 0.40,
            r2: 0.88,
            mse: 0.30,
            mape: 6.5
          }
        },
        featureImportance: [
          { feature: 'temperature', importance: 0.45 },
          { feature: 'humidity', importance: 0.25 },
          { feature: 'wind_speed', importance: 0.15 },
          { feature: 'precipitation', importance: 0.10 },
          { feature: 'hour_of_day', importance: 0.05 }
        ],
        predictions: Array.from({ length: 50 }, (_, i) => ({
          actual: 100 + Math.random() * 100,
          predicted: 100 + Math.random() * 100 - 5 + Math.random() * 10,
          index: i + 1
        })),
        modelInfo: {
          version: '1.0.0',
          parameters: {
            learning_rate: 0.1,
            max_depth: 6,
            n_estimators: 100,
            subsample: 0.8,
            colsample_bytree: 0.8
          },
          timestamp: '2024-01-01 10:30:00'
        }
      }
      setResult(mockResult)
    } catch (err) {
      console.error('Failed to fetch results', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练结果</h1>
        <div className="card">
          <div className="loading-container">
            <p className="text-gray-500 dark:text-gray-400">加载中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练结果</h1>
        <div className="card">
          <div className="empty-state">
            <p className="text-gray-500 dark:text-gray-400">未找到训练结果</p>
            <p className="text-gray-500 dark:text-gray-400 mt-2">实验 ID: {id}</p>
          </div>
        </div>
      </div>
    )
  }

  // 特征重要性图表数据
  const featureImportanceData = {
    labels: result.featureImportance.map(item => item.feature),
    datasets: [
      {
        label: '特征重要性',
        data: result.featureImportance.map(item => item.importance),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      }
    ]
  }

  // 预测与实际值对比图表数据
  const predictionData = {
    labels: result.predictions.slice(0, 20).map(item => item.index.toString()),
    datasets: [
      {
        label: '实际值',
        data: result.predictions.slice(0, 20).map(item => item.actual),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1
      },
      {
        label: '预测值',
        data: result.predictions.slice(0, 20).map(item => item.predicted),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1
      }
    ]
  }

  // 指标对比饼图数据
  const metricsData = {
    labels: ['RMSE', 'MAE', 'R²', 'MAPE'],
    datasets: [
      {
        label: '测试集指标',
        data: [
          result.metrics.test.rmse,
          result.metrics.test.mae,
          result.metrics.test.r2,
          result.metrics.test.mape
        ],
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(239, 68, 68, 0.7)'
        ],
        borderColor: [
          'rgb(59, 130, 246)',
          'rgb(16, 185, 129)',
          'rgb(245, 158, 11)',
          'rgb(239, 68, 68)'
        ],
        borderWidth: 1
      }
    ]
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const
      },
      title: {
        display: true,
        text: ''
      }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/">
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回仪表板
            </Link>
          </Button>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练结果</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="default" size="sm" className="flex items-center">
            <Download className="w-4 h-4 mr-2" />
            导出结果
          </Button>
          <Button variant="outline" size="sm" className="flex items-center">
            <Save className="w-4 h-4 mr-2" />
            保存模型
          </Button>
        </div>
      </div>

      {/* 实验信息 */}
      <Card>
        <CardHeader>
          <CardTitle>实验信息</CardTitle>
          <CardDescription>基本信息和配置</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">实验详情</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">实验名称</span>
                  <span>{result.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">实验描述</span>
                  <span>{result.description}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">任务类型</span>
                  <span>{result.taskType === 'regression' ? '回归' : '分类'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">数据集</span>
                  <span>{result.datasetName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">目标列</span>
                  <span>{result.targetColumn}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">训练时间</span>
                  <span>{result.trainingTime} 秒</span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="font-medium mb-2">模型参数</h3>
              <div className="space-y-2">
                {Object.entries(result.modelInfo.parameters).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-500">{key}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 性能指标 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            性能指标
          </CardTitle>
          <CardDescription>训练、验证和测试集的性能指标</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-2">训练集</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>RMSE</span>
                  <span className="font-semibold">{result.metrics.train.rmse.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAE</span>
                  <span className="font-semibold">{result.metrics.train.mae.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>R²</span>
                  <span className="font-semibold">{result.metrics.train.r2.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAPE</span>
                  <span className="font-semibold">{result.metrics.train.mape.toFixed(2)}%</span>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-2">验证集</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>RMSE</span>
                  <span className="font-semibold">{result.metrics.val.rmse.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAE</span>
                  <span className="font-semibold">{result.metrics.val.mae.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>R²</span>
                  <span className="font-semibold">{result.metrics.val.r2.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAPE</span>
                  <span className="font-semibold">{result.metrics.val.mape.toFixed(2)}%</span>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-500 mb-2">测试集</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>RMSE</span>
                  <span className="font-semibold">{result.metrics.test.rmse.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAE</span>
                  <span className="font-semibold">{result.metrics.test.mae.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>R²</span>
                  <span className="font-semibold">{result.metrics.test.r2.toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span>MAPE</span>
                  <span className="font-semibold">{result.metrics.test.mape.toFixed(2)}%</span>
                </div>
              </div>
            </div>
          </div>
          <div className="h-80">
            <Pie data={metricsData} options={{
              ...chartOptions,
              plugins: {
                ...chartOptions.plugins,
                title: {
                  ...chartOptions.plugins?.title,
                  text: '测试集性能指标'
                }
              }
            }} />
          </div>
        </CardContent>
      </Card>

      {/* 特征重要性 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            特征重要性
          </CardTitle>
          <CardDescription>各特征对模型预测的贡献程度</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Bar data={featureImportanceData} options={{
              ...chartOptions,
              plugins: {
                ...chartOptions.plugins,
                title: {
                  ...chartOptions.plugins?.title,
                  text: '特征重要性排序'
                }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: '重要性值'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: '特征'
                  }
                }
              }
            }} />
          </div>
        </CardContent>
      </Card>

      {/* 预测与实际值对比 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <LineChart className="w-5 h-5 mr-2" />
            预测与实际值对比
          </CardTitle>
          <CardDescription>模型预测值与实际值的对比</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Line data={predictionData} options={{
              ...chartOptions,
              plugins: {
                ...chartOptions.plugins,
                title: {
                  ...chartOptions.plugins?.title,
                  text: '预测值 vs 实际值'
                }
              },
              scales: {
                y: {
                  beginAtZero: false,
                  title: {
                    display: true,
                    text: '值'
                  }
                },
                x: {
                  title: {
                    display: true,
                    text: '样本索引'
                  }
                }
              }
            }} />
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        <Button variant="default" size="lg" asChild>
          <Link to="/experiments">
            查看所有实验
          </Link>
        </Button>
        <Button variant="outline" size="lg" asChild>
          <Link to={`/training/config`}>
            重新训练
          </Link>
        </Button>
        <Button variant="destructive" size="lg" className="flex items-center">
          <Trash2 className="w-4 h-4 mr-2" />
          删除实验
        </Button>
      </div>
    </div>
  )
}

export default TrainingResults