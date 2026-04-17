import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { RefreshCw, Database, Plus, Loader2, CheckCircle, Upload, X } from 'lucide-react'
import { assetsApi, datasetsApi, ScannedAsset, DatasetListResponse, UploadResponse } from '../lib/api'

const ALLOWED_UPLOAD_EXTENSIONS = new Set(['.csv', '.xlsx', '.xls', '.parquet'])

function getFileDisplayPath(file: File): string {
  return (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name
}

function getFileKey(file: File): string {
  return `${getFileDisplayPath(file)}__${file.size}__${file.lastModified}`
}

function isAllowedUploadFile(file: File): boolean {
  const name = file.name.toLowerCase()
  const dotIndex = name.lastIndexOf('.')
  if (dotIndex < 0) {
    return false
  }
  const extension = name.slice(dotIndex)
  return ALLOWED_UPLOAD_EXTENSIONS.has(extension)
}

export function AssetsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'upload' | 'scan' | 'registered'>('upload')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploadResults, setUploadResults] = useState<UploadResponse[]>([])
  const [datasetName, setDatasetName] = useState('')
  const [datasetDescription, setDatasetDescription] = useState('')
  const [timeColumn, setTimeColumn] = useState('')
  const [targetColumn, setTargetColumn] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [createError, setCreateError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [showInvalidOnly, setShowInvalidOnly] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const folderInputRef = useRef<HTMLInputElement | null>(null)
  const invalidSelectedCount = selectedFiles.filter((file) => !isAllowedUploadFile(file)).length
  const displayedSelectedFiles = showInvalidOnly
    ? selectedFiles.filter((file) => !isAllowedUploadFile(file))
    : selectedFiles

  const resetUploadStates = () => {
    setUploadResults([])
    setUploadError('')
    setCreateError('')
    setSuccessMessage('')
  }

  const mergeSelectedFiles = (incomingFiles: File[]) => {
    setSelectedFiles((prev) => {
      const map = new Map<string, File>()
      for (const file of prev) {
        map.set(getFileKey(file), file)
      }
      for (const file of incomingFiles) {
        map.set(getFileKey(file), file)
      }
      return Array.from(map.values())
    })
    resetUploadStates()
  }

  const clearSelectedFiles = () => {
    setSelectedFiles([])
    setShowInvalidOnly(false)
    resetUploadStates()

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    if (folderInputRef.current) {
      folderInputRef.current.value = ''
    }
  }

  const removeSelectedFile = (targetFile: File) => {
    const targetKey = getFileKey(targetFile)
    setSelectedFiles((prev) => prev.filter((file) => getFileKey(file) !== targetKey))
    resetUploadStates()
  }

  const removeInvalidFormatFiles = () => {
    setSelectedFiles((prev) => prev.filter((file) => isAllowedUploadFile(file)))
    setShowInvalidOnly(false)
    resetUploadStates()
  }

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

  const createDatasetMutation = useMutation({
    mutationFn: () => {
      if (uploadResults.length === 0) {
        throw new Error('请先完成文件上传（可批量）')
      }
      if (!datasetName.trim()) {
        throw new Error('请填写数据集名称')
      }

      return datasetsApi.create({
        name: datasetName.trim(),
        description: datasetDescription.trim() || undefined,
        files: uploadResults.map((file, index) => ({
          file_path: file.file_path,
          file_name: file.file_name,
          role: index === 0 ? 'primary' : 'supplementary',
          row_count: file.row_count,
          column_count: file.column_count,
          file_size: file.file_size,
        })),
        time_column: timeColumn || undefined,
        target_column: targetColumn || undefined,
      })
    },
    onSuccess: (created) => {
      setCreateError('')
      setSuccessMessage(`数据集创建成功：${created.name}`)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      setActiveTab('registered')
    },
    onError: (error: Error) => {
      setCreateError(error.message)
      setSuccessMessage('')
    },
  })

  const handleScan = () => {
    doScan()
  }

  const handleUpload = () => {
    if (selectedFiles.length === 0) {
      setUploadError('请先选择要上传的文件（支持多选）')
      return
    }

    if (invalidSelectedCount > 0) {
      setUploadError(`当前有 ${invalidSelectedCount} 个非法格式文件，请先删除后再上传`) 
      return
    }

    void (async () => {
      setIsUploading(true)
      setUploadResults([])
      setUploadError('')
      setCreateError('')
      setSuccessMessage('')

      try {
        const results: UploadResponse[] = []
        for (const file of selectedFiles) {
          const uploaded = await datasetsApi.uploadFile(file)
          results.push(uploaded)
        }

        setUploadResults(results)
        if (!datasetName && selectedFiles.length > 0) {
          setDatasetName(selectedFiles[0].name.replace(/\.[^/.]+$/, ''))
        }

        const firstColumns = results[0]?.columns_info || []
        const timeCandidate = firstColumns.find((col) => col.is_datetime)?.name || ''
        const numericCandidate = firstColumns.find((col) => col.is_numeric)?.name || ''
        setTimeColumn(timeCandidate)
        setTargetColumn(numericCandidate)
      } catch (error) {
        const message = error instanceof Error ? error.message : '批量上传失败'
        setUploadResults([])
        setUploadError(message)
      } finally {
        setIsUploading(false)
      }
    })()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">数据资产管理</h2>
          <p className="text-gray-600">上传导入（推荐）与扫描登记（批量）双通道管理数据集</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'upload'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            上传导入
          </button>
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

      {activeTab === 'upload' && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900">上传导入（推荐）</h3>
              <p className="text-sm text-gray-600 mt-1">
                适用于个人或临时数据。无需准备容器内路径，上传后可直接创建数据集。
              </p>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx,.xls,.parquet"
                onChange={(e) => {
                  const files = Array.from(e.target.files || [])
                  if (files.length > 0) {
                    mergeSelectedFiles(files)
                  }
                  e.currentTarget.value = ''
                }}
                className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-3 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <input
                ref={folderInputRef}
                type="file"
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files || [])
                  if (files.length > 0) {
                    mergeSelectedFiles(files)
                  }
                  e.currentTarget.value = ''
                }}
                className="hidden"
                // Chromium browsers support folder selection via webkitdirectory.
                {...({ webkitdirectory: '', directory: '' } as unknown as Record<string, string>)}
              />
              <button
                type="button"
                onClick={() => folderInputRef.current?.click()}
                className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100"
              >
                选择文件夹
              </button>
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                {isUploading ? '上传中...' : '批量上传文件'}
              </button>
            </div>

            {selectedFiles.length > 0 && (
              <div className="text-sm text-gray-600">
                已选择 {selectedFiles.length} 个文件：
                {invalidSelectedCount > 0 && (
                  <div className="mt-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1 inline-block">
                    检测到 {invalidSelectedCount} 个非法格式文件（仅支持 .csv/.xlsx/.xls/.parquet）
                  </div>
                )}
                {invalidSelectedCount > 0 && (
                  <div className="mt-2">
                    <label className="inline-flex items-center gap-2 text-xs text-gray-700">
                      <input
                        type="checkbox"
                        checked={showInvalidOnly}
                        onChange={(e) => setShowInvalidOnly(e.target.checked)}
                      />
                      只显示非法文件
                    </label>
                  </div>
                )}
                <div className="mt-1 flex flex-wrap gap-2">
                  {displayedSelectedFiles.map((file) => (
                    <span
                      key={getFileKey(file)}
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs border ${
                        isAllowedUploadFile(file)
                          ? 'bg-gray-100 text-gray-700 border-gray-200'
                          : 'bg-red-50 text-red-700 border-red-200'
                      }`}
                    >
                      {getFileDisplayPath(file)}
                      <button
                        type="button"
                        onClick={() => removeSelectedFile(file)}
                        className="hover:opacity-80"
                        title="删除此文件"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
                {showInvalidOnly && displayedSelectedFiles.length === 0 && (
                  <div className="mt-1 text-xs text-gray-500">当前没有非法文件。</div>
                )}
                <div className="mt-2 flex items-center gap-3">
                  {invalidSelectedCount > 0 && (
                    <button
                      type="button"
                      onClick={removeInvalidFormatFiles}
                      className="text-xs text-red-600 hover:text-red-700 underline"
                    >
                      批量删除非法格式文件
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={clearSelectedFiles}
                    className="text-xs text-gray-500 hover:text-gray-700 underline"
                  >
                    清空已选文件
                  </button>
                </div>
              </div>
            )}

            {uploadError && (
              <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">
                上传失败：{uploadError}
              </div>
            )}

            {uploadResults.length > 0 && (
              <div className="space-y-4 border-t border-gray-100 pt-4">
                <div className="bg-green-50 text-green-700 border border-green-200 rounded-lg p-3 text-sm">
                  上传成功：共 {uploadResults.length} 个文件
                </div>

                <div className="space-y-2">
                  {uploadResults.map((item) => (
                    <div key={item.file_path} className="text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded px-3 py-2">
                      {item.file_name}（{item.row_count ?? '-'} 行 / {item.column_count ?? '-'} 列）
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">数据集名称 *</label>
                    <input
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      placeholder="请输入数据集名称"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">描述（可选）</label>
                    <input
                      value={datasetDescription}
                      onChange={(e) => setDatasetDescription(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      placeholder="数据集描述"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">时间列（可选）</label>
                    <select
                      value={timeColumn}
                      onChange={(e) => setTimeColumn(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    >
                      <option value="">不设置</option>
                      {(uploadResults[0]?.columns_info || []).map((col) => (
                        <option key={col.name} value={col.name}>{col.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">目标列（可选）</label>
                    <select
                      value={targetColumn}
                      onChange={(e) => setTargetColumn(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                    >
                      <option value="">不设置</option>
                      {(uploadResults[0]?.columns_info || []).map((col) => (
                        <option key={col.name} value={col.name}>{col.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {createError && (
                  <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">
                    创建失败：{createError}
                  </div>
                )}

                {successMessage && (
                  <div className="bg-green-50 text-green-700 border border-green-200 rounded-lg p-3 text-sm">
                    {successMessage}
                  </div>
                )}

                <button
                  onClick={() => createDatasetMutation.mutate()}
                  disabled={createDatasetMutation.isPending}
                  className="flex items-center px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                >
                  {createDatasetMutation.isPending ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4 mr-2" />
                  )}
                  {createDatasetMutation.isPending ? '创建中...' : '一键创建数据集'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'scan' && (
        <div className="space-y-4">
          <div className="bg-amber-50 p-3 rounded-lg border border-amber-200 text-sm text-amber-800">
            扫描登记适用于批量/预置数据（已在 dataset 目录）。若是临时文件，优先使用“上传导入”。
          </div>
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