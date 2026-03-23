import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, Clock, BarChart3, Activity, CheckCircle, XCircle, AlertTriangle, Eye } from 'lucide-react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface TrainingState {
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  currentIteration: number
  totalIterations: number
  metrics: {
    train: {
      rmse?: number
      mae?: number
      r2?: number
      auc?: number
      accuracy?: number
    }
    val: {
      rmse?: number
      mae?: number
      r2?: number
      auc?: number
      accuracy?: number
    }
  }
  lossHistory: {
    iteration: number
    trainLoss: number
    valLoss: number
  }[]
  logs: {
    timestamp: string
    message: string
    level: 'info' | 'warning' | 'error'
  }[]
}

const TrainingMonitor: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [trainingState, setTrainingState] = useState<TrainingState>({
    status: 'running',
    progress: 35,
    currentIteration: 35,
    totalIterations: 100,
    metrics: {
      train: { rmse: 0.85, mae: 0.62, r2: 0.78 },
      val: { rmse: 0.92, mae: 0.68, r2: 0.72 }
    },
    lossHistory: Array.from({ length: 35 }, (_, i) => ({
      iteration: i + 1,
      trainLoss: 1.2 - (i * 0.02),
      valLoss: 1.3 - (i * 0.015)
    })),
    logs: [
      { timestamp: '2024-01-01 10:00:00', message: '开始训练', level: 'info' },
      { timestamp: '2024-01-01 10:00:05', message: '加载数据集完成', level: 'info' },
      { timestamp: '2024-01-01 10:00:10', message: '初始化模型参数', level: 'info' },
      { timestamp: '2024-01-01 10:00:15', message: '开始第 1 轮训练', level: 'info' },
      { timestamp: '2024-01-01 10:00:30', message: '第 10 轮训练完成，训练损失: 1.02', level: 'info' },
      { timestamp: '2024-01-01 10:00:45', message: '第 20 轮训练完成，训练损失: 0.85', level: 'info' },
      { timestamp: '2024-01-01 10:01:00', message: '第 30 轮训练完成，训练损失: 0.72', level: 'info' }
    ]
  })
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    if (autoRefresh && trainingState.status === 'running') {
      const interval = setInterval(() => {
        updateTrainingState()
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, trainingState.status])

  const updateTrainingState = () => {
    setTrainingState(prev => {
      if (prev.status === 'running' && prev.progress < 100) {
        const newProgress = Math.min(prev.progress + 5, 100)
        const newIteration = Math.min(prev.currentIteration + 5, prev.totalIterations)
        const newLossHistory = [...prev.lossHistory]
        
        for (let i = prev.currentIteration + 1; i <= newIteration; i++) {
          newLossHistory.push({
            iteration: i,
            trainLoss: 1.2 - (i * 0.02),
            valLoss: 1.3 - (i * 0.015)
          })
        }
        
        const newLogs = [...prev.logs]
        if (newIteration % 10 === 0) {
          newLogs.push({
            timestamp: new Date().toLocaleString(),
            message: `第 ${newIteration} 轮训练完成，训练损失: ${(1.2 - (newIteration * 0.02)).toFixed(2)}`,
            level: 'info'
          })
        }
        
        const newStatus = newProgress === 100 ? 'completed' : 'running'
        
        return {
          ...prev,
          status: newStatus,
          progress: newProgress,
          currentIteration: newIteration,
          lossHistory: newLossHistory,
          logs: newLogs,
          metrics: {
            train: {
              rmse: 0.85 - (newProgress * 0.005),
              mae: 0.62 - (newProgress * 0.003),
              r2: 0.78 + (newProgress * 0.001)
            },
            val: {
              rmse: 0.92 - (newProgress * 0.004),
              mae: 0.68 - (newProgress * 0.0025),
              r2: 0.72 + (newProgress * 0.0008)
            }
          }
        }
      }
      return prev
    })
  }

  const chartData = {
    labels: trainingState.lossHistory.map(item => item.iteration.toString()),
    datasets: [
      {
        label: '训练损失',
        data: trainingState.lossHistory.map(item => item.trainLoss),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1
      },
      {
        label: '验证损失',
        data: trainingState.lossHistory.map(item => item.valLoss),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1
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
        text: '损失曲线'
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: '损失值'
        }
      },
      x: {
        title: {
          display: true,
          text: '迭代次数'
        }
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'running': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4" />
      case 'running': return <Activity className="w-4 h-4" />
      case 'completed': return <CheckCircle className="w-4 h-4" />
      case 'failed': return <XCircle className="w-4 h-4" />
      default: return <AlertTriangle className="w-4 h-4" />
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">训练监控</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? '暂停刷新' : '自动刷新'}
          </Button>
          {trainingState.status === 'completed' && (
            <Button variant="default" size="sm" asChild>
              <Link to={`/training/results/${id}`}>
                <Eye className="w-4 h-4 mr-2" />
                查看结果
              </Link>
            </Button>
          )}
        </div>
      </div>

      {/* 训练状态卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            训练状态
          </CardTitle>
          <CardDescription>实验 ID: {id}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${getStatusColor(trainingState.status)}`}>
                {getStatusIcon(trainingState.status)}
                <span className="font-medium">
                  {trainingState.status === 'pending' && '等待中'}
                  {trainingState.status === 'running' && '训练中'}
                  {trainingState.status === 'completed' && '已完成'}
                  {trainingState.status === 'failed' && '失败'}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                第 {trainingState.currentIteration} / {trainingState.totalIterations} 轮
              </div>
            </div>
            
            {/* 进度条 */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>训练进度</span>
                <span>{trainingState.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full" 
                  style={{ width: `${trainingState.progress}%` }}
                ></div>
              </div>
            </div>
            
            {/* 性能指标 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500">训练 RMSE</div>
                <div className="text-lg font-semibold">{trainingState.metrics.train.rmse?.toFixed(3)}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500">验证 RMSE</div>
                <div className="text-lg font-semibold">{trainingState.metrics.val.rmse?.toFixed(3)}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500">训练 MAE</div>
                <div className="text-lg font-semibold">{trainingState.metrics.train.mae?.toFixed(3)}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500">验证 MAE</div>
                <div className="text-lg font-semibold">{trainingState.metrics.val.mae?.toFixed(3)}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 损失曲线 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            损失曲线
          </CardTitle>
          <CardDescription>训练和验证损失随迭代次数的变化</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Line data={chartData} options={chartOptions} />
          </div>
        </CardContent>
      </Card>

      {/* 训练日志 */}
      <Card>
        <CardHeader>
          <CardTitle>训练日志</CardTitle>
          <CardDescription>实时训练过程日志</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-80 overflow-y-auto border rounded-md p-4">
            {trainingState.logs.map((log, index) => (
              <div key={index} className="mb-2">
                <div className="flex items-start space-x-2">
                  <span className="text-xs text-gray-500 min-w-[150px]">{log.timestamp}</span>
                  <span className={`text-xs px-2 py-1 rounded ${log.level === 'info' ? 'bg-blue-100 text-blue-800' : log.level === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
                    {log.level === 'info' && 'INFO'}
                    {log.level === 'warning' && 'WARNING'}
                    {log.level === 'error' && 'ERROR'}
                  </span>
                  <span className="text-sm">{log.message}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        {trainingState.status === 'running' && (
          <Button variant="default" size="lg">
            停止训练
          </Button>
        )}
        {trainingState.status === 'completed' && (
          <Button variant="default" size="lg" asChild>
            <Link to={`/training/results/${id}`}>
              <Eye className="w-4 h-4 mr-2" />
              查看训练结果
            </Link>
          </Button>
        )}
        <Button variant="outline" size="lg" asChild>
          <Link to="/">
            返回仪表板
          </Link>
        </Button>
      </div>
    </div>
  )
}

export default TrainingMonitor