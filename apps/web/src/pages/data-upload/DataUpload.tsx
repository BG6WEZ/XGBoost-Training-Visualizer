import React, { useState, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Upload, FileText, X, Check, AlertCircle, Clock } from 'lucide-react'
import { formatFileSize } from '@xgboost-vis/utils'

interface FileUpload {
  id: string
  name: string
  size: number
  progress: number
  status: 'uploading' | 'completed' | 'failed' | 'pending'
  error?: string
}

const DataUpload: React.FC = () => {
  const [files, setFiles] = useState<FileUpload[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files
    if (selectedFiles) {
      const newFiles: FileUpload[] = Array.from(selectedFiles).map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        progress: 0,
        status: 'pending'
      }))
      setFiles([...files, ...newFiles])
      // 模拟上传过程
      newFiles.forEach(file => {
        simulateUpload(file.id)
      })
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    const droppedFiles = event.dataTransfer.files
    if (droppedFiles) {
      const newFiles: FileUpload[] = Array.from(droppedFiles).map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        progress: 0,
        status: 'pending'
      }))
      setFiles([...files, ...newFiles])
      // 模拟上传过程
      newFiles.forEach(file => {
        simulateUpload(file.id)
      })
    }
  }

  const simulateUpload = (fileId: string) => {
    setFiles(prev => prev.map(file => 
      file.id === fileId ? { ...file, status: 'uploading' } : file
    ))

    let progress = 0
    const interval = setInterval(() => {
      progress += 5
      setFiles(prev => prev.map(file => 
        file.id === fileId ? { ...file, progress } : file
      ))
      if (progress >= 100) {
        clearInterval(interval)
        setFiles(prev => prev.map(file => 
          file.id === fileId ? { ...file, status: 'completed' } : file
        ))
      }
    }, 200)
  }

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const clearAllFiles = () => {
    setFiles([])
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">数据上传</h1>
        {files.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearAllFiles}>
            清空全部
          </Button>
        )}
      </div>

      {/* 拖拽上传区域 */}
      <Card className={`transition-all ${isDragging ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : ''}`}>
        <CardContent className="p-8">
          <div
            className="border-2 border-dashed rounded-lg p-10 text-center cursor-pointer"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".csv,.xlsx,.xls,.json"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="flex flex-col items-center space-y-4">
              <div className={`p-4 rounded-full ${isDragging ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}>
                <Upload className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">拖拽文件到此处或点击上传</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  支持 CSV、Excel、JSON 文件，单个文件最大 1GB
                </p>
              </div>
              <Button variant="default">
                选择文件
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 上传队列 */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>上传队列</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {files.map(file => (
                <div key={file.id} className="flex items-center space-x-4 p-3 border rounded-lg">
                  <div className="flex-shrink-0">
                    <FileText className="w-5 h-5 text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900 dark:text-white truncate">
                        {file.name}
                      </p>
                      <button
                        onClick={() => removeFile(file.id)}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {formatFileSize(file.size)}
                      </span>
                      <span className="text-sm">
                        {file.status === 'uploading' && (
                          <span className="text-blue-600 dark:text-blue-400 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            上传中 {file.progress}%
                          </span>
                        )}
                        {file.status === 'completed' && (
                          <span className="text-green-600 dark:text-green-400 flex items-center">
                            <Check className="w-3 h-3 mr-1" />
                            已完成
                          </span>
                        )}
                        {file.status === 'failed' && (
                          <span className="text-red-600 dark:text-red-400 flex items-center">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            失败
                          </span>
                        )}
                        {file.status === 'pending' && (
                          <span className="text-gray-500 dark:text-gray-400">
                            等待中
                          </span>
                        )}
                      </span>
                    </div>
                    {file.status === 'uploading' && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 上传说明 */}
      <Card>
        <CardHeader>
          <CardTitle>上传说明</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-start">
              <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>支持 CSV、Excel、JSON 格式文件</span>
            </li>
            <li className="flex items-start">
              <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>单个文件最大 1GB，超过 1GB 会自动切分</span>
            </li>
            <li className="flex items-start">
              <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>支持同时上传多个文件</span>
            </li>
            <li className="flex items-start">
              <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>支持上传整个文件夹</span>
            </li>
            <li className="flex items-start">
              <Check className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
              <span>上传完成后会自动进行数据验证和预览</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

export default DataUpload