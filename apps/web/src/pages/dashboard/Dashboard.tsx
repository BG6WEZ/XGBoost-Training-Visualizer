import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Link } from 'react-router-dom'
import { Upload, Settings, BarChart3, GitCompare } from 'lucide-react'

interface Experiment {
  id: string
  name: string
  status: string
}

const Dashboard: React.FC = () => {
  const stats = [
    {
      title: '总数据集',
      value: 0,
      icon: Upload,
      color: 'bg-blue-100 text-blue-600',
      link: '/data'
    },
    {
      title: '训练实验',
      value: 0,
      icon: BarChart3,
      color: 'bg-green-100 text-green-600',
      link: '/experiments'
    },
    {
      title: '模型版本',
      value: 0,
      icon: Settings,
      color: 'bg-purple-100 text-purple-600',
      link: '/experiments'
    },
    {
      title: '对比分析',
      value: 0,
      icon: GitCompare,
      color: 'bg-orange-100 text-orange-600',
      link: '/compare'
    }
  ]

  const recentExperiments: Experiment[] = []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">仪表板</h1>
        <div className="space-x-2">
          <Button asChild>
            <Link to="/data">上传数据</Link>
          </Button>
          <Button asChild>
            <Link to="/training/config">新建训练</Link>
          </Button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index} className="card-shadow hover:card-shadow-hover transition-all">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  {stat.title}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </div>
                  <div className={`p-2 rounded-full ${stat.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                </div>
                <div className="mt-4">
                  <Button variant="ghost" size="sm" className="w-full justify-start">
                    查看详情 →
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 最近实验 */}
      <Card className="card-shadow">
        <CardHeader>
          <CardTitle>最近实验</CardTitle>
        </CardHeader>
        <CardContent>
          {recentExperiments.length === 0 ? (
            <div className="empty-state">
              <p className="text-gray-500 dark:text-gray-400">暂无实验数据</p>
              <Button asChild className="mt-4">
                <Link to="/training/config">创建第一个实验</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentExperiments.map((experiment, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {experiment.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {experiment.status}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm">
                    查看
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 快捷操作 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="card-shadow hover:card-shadow-hover transition-all">
          <CardHeader>
            <CardTitle>数据管理</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              上传、预览和管理数据集
            </p>
            <Button asChild className="w-full">
              <Link to="/data">前往数据管理</Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="card-shadow hover:card-shadow-hover transition-all">
          <CardHeader>
            <CardTitle>模型训练</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              配置参数并启动训练
            </p>
            <Button asChild className="w-full">
              <Link to="/training/config">配置训练</Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="card-shadow hover:card-shadow-hover transition-all">
          <CardHeader>
            <CardTitle>迁移学习</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              跨数据集迁移模型
            </p>
            <Button asChild className="w-full">
              <Link to="/transfer">迁移学习</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard