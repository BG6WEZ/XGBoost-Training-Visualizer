import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Play, Trash2, Loader2, Split } from 'lucide-react'
import { datasetsApi } from '../lib/api'
import { useState } from 'react'

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [splitMethod, setSplitMethod] = useState<'random' | 'time'>('random')
  const [testSize, setTestSize] = useState(0.2)
  const [timeColumn, setTimeColumn] = useState('')
  const [trainEndDate, setTrainEndDate] = useState('')

  const { data: dataset, isLoading } = useQuery({
    queryKey: ['dataset', id],
    queryFn: () => datasetsApi.get(id!),
    enabled: !!id,
  })

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
        <button
          onClick={() => deleteMutation.mutate()}
          disabled={deleteMutation.isPending}
          className="flex items-center px-3 py-2 text-sm text-red-600 border border-red-600 rounded-lg hover:bg-red-50"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          删除
        </button>
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