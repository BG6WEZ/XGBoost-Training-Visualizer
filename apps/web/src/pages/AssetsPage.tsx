import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { RefreshCw, Database, Plus, Loader2, CheckCircle } from 'lucide-react'
import { assetsApi, datasetsApi, ScannedAsset, DatasetListResponse } from '../lib/api'

export function AssetsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'scan' | 'registered'>('scan')

  // 扫描结果
  const { data: scanResult, isLoading: isScanning, refetch: doScan } = useQuery({
    queryKey: ['assets-scan'],
    queryFn: assetsApi.scan,
    enabled: false,
  })

  // 已注册数据集
  const { data: datasets, isLoading: isLoadingDatasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsApi.list,
  })

  // 注册数据资产
  const registerMutation = useMutation({
    mutationFn: (asset: ScannedAsset) =>
      assetsApi.register({
        asset_name: asset.name,
        source_type: asset.source_type,
        path: asset.path,
        path_type: asset.path_type,
        is_raw: asset.is_raw,
        description: asset.description,
        member_files: asset.member_files,
        auto_detect_columns: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      queryClient.invalidateQueries({ queryKey: ['assets-scan'] })
    },
  })

  const handleScan = () => {
    doScan()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">数据资产管理</h2>
          <p className="text-gray-600">扫描、登记和管理训练数据集</p>
        </div>
        <button
          onClick={() => setActiveTab(activeTab === 'scan' ? 'registered' : 'scan')}
          className="px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          切换到{activeTab === 'scan' ? '已登记数据集' : '扫描数据资产'}
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('scan')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'scan'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            扫描数据资产
          </button>
          <button
            onClick={() => setActiveTab('registered')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'registered'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            已登记数据集 ({datasets?.length || 0})
          </button>
        </nav>
      </div>

      {activeTab === 'scan' && (
        <div className="space-y-4">
          <button
            onClick={handleScan}
            disabled={isScanning}
            className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isScanning ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            {isScanning ? '扫描中...' : '扫描 dataset/ 目录'}
          </button>

          {scanResult && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-700">
                发现 <strong>{scanResult.total_assets}</strong> 个可登记的数据资产
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {scanResult?.assets.map((asset, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{asset.name}</h3>
                    <p className="text-sm text-gray-500">{asset.source_name}</p>
                  </div>
                  {asset.registered ? (
                    <span className="flex items-center text-sm text-green-600">
                      <CheckCircle className="w-4 h-4 mr-1" />
                      已登记
                    </span>
                  ) : (
                    <button
                      onClick={() => registerMutation.mutate(asset)}
                      disabled={registerMutation.isPending}
                      className="flex items-center px-3 py-1 text-sm text-blue-600 border border-blue-600 rounded hover:bg-blue-50 disabled:opacity-50"
                    >
                      {registerMutation.isPending ? (
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      ) : (
                        <Plus className="w-3 h-3 mr-1" />
                      )}
                      登记
                    </button>
                  )}
                </div>
                <div className="mt-3 space-y-1 text-sm text-gray-600">
                  <p>路径类型: {asset.path_type === 'directory' ? '目录' : '文件'}</p>
                  <p>数据状态: {asset.is_raw ? '原始数据' : '清洗后'}</p>
                  <p>文件数量: {asset.member_files.length}</p>
                </div>
                {asset.description && (
                  <p className="mt-2 text-sm text-gray-500">{asset.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'registered' && (
        <div className="space-y-4">
          {isLoadingDatasets ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : datasets && datasets.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {datasets.map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <Database className="w-12 h-12 mx-auto text-gray-400" />
              <p className="mt-4 text-gray-500">暂无已登记的数据集</p>
              <button
                onClick={() => setActiveTab('scan')}
                className="mt-4 text-blue-600 hover:text-blue-700 text-sm"
              >
                点击扫描数据资产
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function DatasetCard({ dataset }: { dataset: DatasetListResponse }) {
  return (
    <Link
      to={`/assets/${dataset.id}`}
      className="block bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
          {dataset.description && (
            <p className="text-sm text-gray-500 mt-1">{dataset.description}</p>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {new Date(dataset.created_at).toLocaleDateString('zh-CN')}
        </span>
      </div>
      <div className="mt-3 flex items-center space-x-4 text-sm text-gray-600">
        <span>{dataset.total_row_count.toLocaleString()} 行</span>
        <span>{dataset.total_column_count} 列</span>
        <span>{dataset.file_count} 文件</span>
      </div>
    </Link>
  )
}