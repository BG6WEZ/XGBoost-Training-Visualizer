import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { ArrowLeft, Eye, Database, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { formatFileSize } from '@xgboost-vis/utils'

interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
  unique: boolean
  missingCount: number
  missingPercentage: number
  min?: number
  max?: number
  mean?: number
}

const DatasetPreview: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [dataset, setDataset] = useState<any>(null)
  const [previewData, setPreviewData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      fetchDataset()
      fetchPreviewData()
    }
  }, [id])

  const fetchDataset = async () => {
    try {
      setLoading(true)
      // 模拟 API 调用
      const mockData = {
        id,
        name: 'Building Energy Data',
        fileType: 'csv',
        fileSize: 1048576,
        rowCount: 1000,
        columnCount: 5,
        columns: [
          { name: 'timestamp', type: 'datetime', nullable: false, unique: true, missingCount: 0, missingPercentage: 0 },
          { name: 'building_id', type: 'string', nullable: false, unique: false, missingCount: 0, missingPercentage: 0 },
          { name: 'energy_consumption', type: 'number', nullable: false, unique: false, missingCount: 0, missingPercentage: 0 },
          { name: 'temperature', type: 'number', nullable: true, unique: false, missingCount: 5, missingPercentage: 0.5 },
          { name: 'humidity', type: 'number', nullable: true, unique: false, missingCount: 3, missingPercentage: 0.3 }
        ],
        status: 'completed',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      setDataset(mockData)
    } catch (err) {
      setError('Failed to fetch dataset information')
    } finally {
      setLoading(false)
    }
  }

  const fetchPreviewData = async () => {
    try {
      // 模拟 API 调用
      const mockPreview = {
        columns: ['timestamp', 'building_id', 'energy_consumption', 'temperature', 'humidity'],
        rows: [
          ['2024-01-01 00:00:00', 'B001', 120.5, 22.5, 45],
          ['2024-01-01 01:00:00', 'B001', 118.2, 22.3, 46],
          ['2024-01-01 02:00:00', 'B001', 115.8, 22.1, 47],
          ['2024-01-01 03:00:00', 'B001', 112.3, 21.9, 48],
          ['2024-01-01 04:00:00', 'B001', 110.1, 21.8, 49]
        ],
        totalRows: 1000,
        sampleSize: 5
      }
      setPreviewData(mockPreview)
    } catch (err) {
      setError('Failed to fetch preview data')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据预览</h1>
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据预览</h1>
        <div className="card">
          <div className="error-state">
            <AlertCircle className="w-10 h-10 text-red-500 mb-4" />
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据预览</h1>
      </div>

      {/* 数据集信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Database className="w-5 h-5 mr-2" />
            数据集信息
          </CardTitle>
          <CardDescription>基本信息和统计数据</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">数据集名称</p>
              <p className="font-medium text-gray-900 dark:text-white">{dataset?.name}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">文件类型</p>
              <p className="font-medium text-gray-900 dark:text-white">{dataset?.fileType.toUpperCase()}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">文件大小</p>
              <p className="font-medium text-gray-900 dark:text-white">{formatFileSize(dataset?.fileSize || 0)}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400">数据行数</p>
              <p className="font-medium text-gray-900 dark:text-white">{dataset?.rowCount.toLocaleString()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 列信息 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            列信息
          </CardTitle>
          <CardDescription>字段类型和统计信息</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr>
                  <th>列名</th>
                  <th>类型</th>
                  <th>可空</th>
                  <th>唯一</th>
                  <th>缺失值</th>
                  <th>缺失百分比</th>
                </tr>
              </thead>
              <tbody>
                {dataset?.columns.map((column: ColumnInfo, index: number) => (
                  <tr key={index}>
                    <td className="font-medium">{column.name}</td>
                    <td>{column.type}</td>
                    <td>
                      {column.nullable ? (
                        <span className="text-yellow-600 dark:text-yellow-400">是</span>
                      ) : (
                        <span className="text-green-600 dark:text-green-400">否</span>
                      )}
                    </td>
                    <td>
                      {column.unique ? (
                        <span className="text-green-600 dark:text-green-400">是</span>
                      ) : (
                        <span className="text-gray-600 dark:text-gray-400">否</span>
                      )}
                    </td>
                    <td>
                      {column.missingCount > 0 ? (
                        <span className="text-red-600 dark:text-red-400">{column.missingCount}</span>
                      ) : (
                        <span className="text-green-600 dark:text-green-400">0</span>
                      )}
                    </td>
                    <td>
                      {column.missingPercentage > 0 ? (
                        <span className="text-red-600 dark:text-red-400">{column.missingPercentage}%</span>
                      ) : (
                        <span className="text-green-600 dark:text-green-400">0%</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 数据预览 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Eye className="w-5 h-5 mr-2" />
            数据预览
          </CardTitle>
          <CardDescription>前 {previewData?.sampleSize} 行数据</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr>
                  {previewData?.columns.map((column: string, index: number) => (
                    <th key={index}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData?.rows.map((row: any[], index: number) => (
                  <tr key={index}>
                    {row.map((value: any, colIndex: number) => (
                      <td key={colIndex}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
            共 {previewData?.totalRows.toLocaleString()} 行数据，显示前 {previewData?.sampleSize} 行
          </p>
        </CardContent>
      </Card>

      {/* 数据质量报告 */}
      <Card>
        <CardHeader>
          <CardTitle>数据质量报告</CardTitle>
          <CardDescription>数据质量评估结果</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-gray-900 dark:text-white">数据格式正确</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-gray-900 dark:text-white">字段类型识别成功</span>
            </div>
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              <span className="text-gray-900 dark:text-white">存在少量缺失值（建议处理）</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-gray-900 dark:text-white">数据完整性良好</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center space-x-4">
        <Button variant="default" asChild>
          <Link to={`/data/${id}/split`}>
            进行数据集切分
          </Link>
        </Button>
        <Button variant="default" asChild>
          <Link to={`/data/${id}/features`}>
            特征工程
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

export default DatasetPreview