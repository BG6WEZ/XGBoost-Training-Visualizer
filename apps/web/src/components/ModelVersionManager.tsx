/**
 * 模型版本管理组件 (P1-T13)
 * 
 * 功能：
 * - 显示版本列表
 * - 版本比较
 * - 版本回滚
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { History, GitCompare, RotateCcw, Check, Loader2, Tag, X } from 'lucide-react'
import { versionsApi, ModelVersionListResponse, VersionCompareResponse } from '../lib/api'

interface ModelVersionManagerProps {
  experimentId: string
}

export function ModelVersionManager({ experimentId }: ModelVersionManagerProps) {
  const queryClient = useQueryClient()
  const [selectedVersions, setSelectedVersions] = useState<string[]>([])
  const [showCompare, setShowCompare] = useState(false)
  const [compareData, setCompareData] = useState<VersionCompareResponse | null>(null)
  const [rollbackConfirm, setRollbackConfirm] = useState<string | null>(null)

  const { data: versions, isLoading } = useQuery({
    queryKey: ['versions', experimentId],
    queryFn: () => versionsApi.list(experimentId),
    enabled: !!experimentId,
  })

  const rollbackMutation = useMutation({
    mutationFn: (versionId: string) => versionsApi.rollback(versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions', experimentId] })
      setRollbackConfirm(null)
    },
  })

  const handleCompare = async () => {
    if (selectedVersions.length < 2) return
    try {
      const data = await versionsApi.compare(selectedVersions)
      setCompareData(data)
      setShowCompare(true)
    } catch (error) {
      console.error('Compare failed:', error)
    }
  }

  const handleRollback = (versionId: string) => {
    rollbackMutation.mutate(versionId)
  }

  const toggleVersionSelection = (versionId: string) => {
    setSelectedVersions(prev => {
      if (prev.includes(versionId)) {
        return prev.filter(id => id !== versionId)
      }
      if (prev.length >= 3) {
        return prev
      }
      return [...prev, versionId]
    })
  }

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </div>
    )
  }

  if (!versions || versions.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <History className="w-5 h-5 mr-2 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">模型版本</h3>
        </div>
        <div className="text-center py-8 text-gray-500">
          <History className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">暂无版本记录</p>
          <p className="text-xs mt-1 text-gray-400">
            训练完成后将自动创建第一个版本快照
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <History className="w-5 h-5 mr-2" />
          模型版本
        </h3>
        {selectedVersions.length >= 2 && (
          <button
            onClick={handleCompare}
            className="flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
          >
            <GitCompare className="w-4 h-4 mr-1" />
            比较选中版本 ({selectedVersions.length})
          </button>
        )}
      </div>

      <div className="text-xs text-gray-500 mb-3">
        选择 2-3 个版本进行比较，点击回滚按钮切换激活版本
      </div>

      <div className="space-y-2">
        {versions.map((version) => (
          <VersionItem
            key={version.id}
            version={version}
            isSelected={selectedVersions.includes(version.id)}
            isRollingBack={rollbackMutation.isPending && rollbackConfirm === version.id}
            onSelect={() => toggleVersionSelection(version.id)}
            onRollback={() => setRollbackConfirm(version.id)}
            onConfirmRollback={() => handleRollback(version.id)}
            onCancelRollback={() => setRollbackConfirm(null)}
            showRollbackConfirm={rollbackConfirm === version.id}
          />
        ))}
      </div>

      {showCompare && compareData && (
        <VersionCompareModal
          data={compareData}
          onClose={() => {
            setShowCompare(false)
            setCompareData(null)
          }}
        />
      )}
    </div>
  )
}

interface VersionItemProps {
  version: ModelVersionListResponse
  isSelected: boolean
  isRollingBack: boolean
  onSelect: () => void
  onRollback: () => void
  onConfirmRollback: () => void
  onCancelRollback: () => void
  showRollbackConfirm: boolean
}

function VersionItem({
  version,
  isSelected,
  isRollingBack,
  onSelect,
  onRollback,
  onConfirmRollback,
  onCancelRollback,
  showRollbackConfirm,
}: VersionItemProps) {
  const metrics = version.metrics_snapshot || {}
  
  return (
    <div
      className={`flex items-center p-3 rounded-lg border ${
        isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
      } ${version.is_active ? 'ring-2 ring-green-500 ring-opacity-50' : ''}`}
    >
      <button
        onClick={onSelect}
        className={`w-5 h-5 rounded border flex items-center justify-center mr-3 ${
          isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
        }`}
      >
        {isSelected && <Check className="w-3 h-3 text-white" />}
      </button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-gray-900">{version.version_number}</span>
          {version.is_active && (
            <span className="px-2 py-0.5 text-xs font-medium text-green-700 bg-green-100 rounded-full">
              当前版本
            </span>
          )}
          {version.tags && version.tags.length > 0 && (
            <div className="flex items-center space-x-1">
              {version.tags.map((tag, i) => (
                <span
                  key={i}
                  className="inline-flex items-center px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                >
                  <Tag className="w-3 h-3 mr-1" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
          <span>创建于 {new Date(version.created_at).toLocaleString('zh-CN')}</span>
          {metrics.val_rmse !== undefined && (
            <span>Val RMSE: {Number(metrics.val_rmse).toFixed(4)}</span>
          )}
          {metrics.r2 !== undefined && (
            <span>R²: {Number(metrics.r2).toFixed(4)}</span>
          )}
        </div>
      </div>

      {!version.is_active && (
        <div className="ml-4">
          {showRollbackConfirm ? (
            <div className="flex items-center space-x-2">
              <button
                onClick={onConfirmRollback}
                disabled={isRollingBack}
                className="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 disabled:opacity-50"
              >
                {isRollingBack ? '回滚中...' : '确认'}
              </button>
              <button
                onClick={onCancelRollback}
                disabled={isRollingBack}
                className="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={onRollback}
              className="flex items-center px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              回滚
            </button>
          )}
        </div>
      )}
    </div>
  )
}

interface VersionCompareModalProps {
  data: VersionCompareResponse
  onClose: () => void
}

function VersionCompareModal({ data, onClose }: VersionCompareModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">版本比较</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto max-h-[calc(80vh-60px)]">
          {data.config_diffs.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">配置差异</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        参数
                      </th>
                      {data.versions.map((v) => (
                        <th
                          key={v.id}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                        >
                          {v.version_number}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.config_diffs.map((diff, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-sm font-medium text-gray-900">
                          {diff.param_name}
                        </td>
                        {data.versions.map((v) => (
                          <td key={v.id} className="px-4 py-2 text-sm text-gray-600">
                            {String(diff.values[v.version_number] ?? '-')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {data.metrics_diffs.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">指标差异</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        指标
                      </th>
                      {data.versions.map((v) => (
                        <th
                          key={v.id}
                          className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                        >
                          {v.version_number}
                        </th>
                      ))}
                      {data.versions.length > 1 && (
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          变化
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.metrics_diffs.map((diff, i) => (
                      <tr key={i}>
                        <td className="px-4 py-2 text-sm font-medium text-gray-900">
                          {diff.metric_name}
                        </td>
                        {data.versions.map((v) => (
                          <td key={v.id} className="px-4 py-2 text-sm text-gray-600">
                            {diff.values[v.version_number] !== undefined
                              ? Number(diff.values[v.version_number]).toFixed(4)
                              : '-'}
                          </td>
                        ))}
                        {data.versions.length > 1 && diff.change && (
                          <td className="px-4 py-2 text-sm">
                            {Object.entries(diff.change).map(([version, change]) => (
                              <span
                                key={version}
                                className={`mr-2 ${
                                  change > 0 ? 'text-red-600' : 'text-green-600'
                                }`}
                              >
                                {version}: {change > 0 ? '+' : ''}
                                {change.toFixed(2)}%
                              </span>
                            ))}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {data.config_diffs.length === 0 && data.metrics_diffs.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              选中版本之间没有差异
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
