import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Database,
  FileText,
  Calendar,
  Target,
  Clock,
  BarChart3,
  PieChart
} from 'lucide-react'
import { datasetsApi, QualityScoreResponse } from '../lib/api'

/**
 * 数据质量报告页面
 * 显示数据集的四维评分、问题清单、建议和统计摘要
 */
export function QualityReportPage() {
  const { id } = useParams<{ id: string }>()

  const { data: qualityData, isLoading, error } = useQuery<QualityScoreResponse>({
    queryKey: ['quality-score', id],
    queryFn: () => datasetsApi.getQualityScore(id!),
    enabled: !!id,
  })

  // Loading 状态
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  // Error 状态处理
  if (error) {
    const errorMessage = error instanceof Error ? error.message : '未知错误'

    // 404 错误
    if (errorMessage.includes('not found') || errorMessage.includes('404')) {
      return (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">数据集不存在</h3>
          <p className="text-gray-600 mb-4">请求的数据集 ID 无效或已被删除</p>
          <Link to="/assets" className="text-blue-600 hover:text-blue-700">
            返回数据资产列表
          </Link>
        </div>
      )
    }

    // 422 错误（无主文件或文件不可访问）
    if (errorMessage.includes('422') || errorMessage.includes('NO_PRIMARY_FILE') || errorMessage.includes('FILE_NOT_ACCESSIBLE')) {
      return (
        <div className="text-center py-12">
          <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">无法生成质量报告</h3>
          <p className="text-gray-600 mb-4">{errorMessage}</p>
          <Link to={`/assets/${id}`} className="text-blue-600 hover:text-blue-700">
            返回数据集详情
          </Link>
        </div>
      )
    }

    // 其他错误（500 等）
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
        <p className="text-gray-600 mb-4">{errorMessage}</p>
        <Link to="/assets" className="text-blue-600 hover:text-blue-700">
          返回数据资产列表
        </Link>
      </div>
    )
  }

  // 空数据处理
  if (!qualityData) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">暂无质量数据</h3>
        <p className="text-gray-600 mb-4">无法获取数据质量评分信息</p>
        <Link to={`/assets/${id}`} className="text-blue-600 hover:text-blue-700">
          返回数据集详情
        </Link>
      </div>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50 border-green-200'
    if (score >= 60) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  const getSeverityIcon = (severity: string) => {
    if (severity === 'error') {
      return <AlertCircle className="w-5 h-5 text-red-500" />
    }
    return <AlertTriangle className="w-5 h-5 text-yellow-500" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Link to={`/assets/${id}`} className="text-gray-400 hover:text-gray-600">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">数据质量报告</h2>
          <p className="text-sm text-gray-600">数据集 ID: {id}</p>
        </div>
      </div>

      {/* 总分区 */}
      <div className={`bg-white border rounded-lg p-6 ${getScoreBgColor(qualityData.overall_score)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`text-6xl font-bold ${getScoreColor(qualityData.overall_score)}`}>
              {qualityData.overall_score}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">总体质量评分</h3>
              <p className="text-sm text-gray-600">
                {qualityData.overall_score >= 80 ? '优秀' : qualityData.overall_score >= 60 ? '良好' : '需要改进'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center text-sm text-gray-600">
              <Calendar className="w-4 h-4 mr-1" />
              评估时间
            </div>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {new Date(qualityData.evaluated_at).toLocaleString('zh-CN')}
            </p>
          </div>
        </div>
      </div>

      {/* 四维评分卡区 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          四维评分详情
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 完整性 */}
          <div className={`border rounded-lg p-4 ${getScoreBgColor(qualityData.dimension_scores.completeness)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">完整性</span>
              <Database className="w-4 h-4 text-gray-400" />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(qualityData.dimension_scores.completeness)}`}>
              {qualityData.dimension_scores.completeness}
            </div>
            <p className="text-xs text-gray-500 mt-1">权重: {(qualityData.weights.completeness * 100).toFixed(0)}%</p>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${qualityData.dimension_scores.completeness >= 80 ? 'bg-green-500' : qualityData.dimension_scores.completeness >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${qualityData.dimension_scores.completeness}%` }}
              />
            </div>
          </div>

          {/* 准确性 */}
          <div className={`border rounded-lg p-4 ${getScoreBgColor(qualityData.dimension_scores.accuracy)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">准确性</span>
              <Target className="w-4 h-4 text-gray-400" />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(qualityData.dimension_scores.accuracy)}`}>
              {qualityData.dimension_scores.accuracy}
            </div>
            <p className="text-xs text-gray-500 mt-1">权重: {(qualityData.weights.accuracy * 100).toFixed(0)}%</p>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${qualityData.dimension_scores.accuracy >= 80 ? 'bg-green-500' : qualityData.dimension_scores.accuracy >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${qualityData.dimension_scores.accuracy}%` }}
              />
            </div>
          </div>

          {/* 一致性 */}
          <div className={`border rounded-lg p-4 ${getScoreBgColor(qualityData.dimension_scores.consistency)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">一致性</span>
              <Clock className="w-4 h-4 text-gray-400" />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(qualityData.dimension_scores.consistency)}`}>
              {qualityData.dimension_scores.consistency}
            </div>
            <p className="text-xs text-gray-500 mt-1">权重: {(qualityData.weights.consistency * 100).toFixed(0)}%</p>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${qualityData.dimension_scores.consistency >= 80 ? 'bg-green-500' : qualityData.dimension_scores.consistency >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${qualityData.dimension_scores.consistency}%` }}
              />
            </div>
          </div>

          {/* 分布 */}
          <div className={`border rounded-lg p-4 ${getScoreBgColor(qualityData.dimension_scores.distribution)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">分布</span>
              <PieChart className="w-4 h-4 text-gray-400" />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(qualityData.dimension_scores.distribution)}`}>
              {qualityData.dimension_scores.distribution}
            </div>
            <p className="text-xs text-gray-500 mt-1">权重: {(qualityData.weights.distribution * 100).toFixed(0)}%</p>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${qualityData.dimension_scores.distribution >= 80 ? 'bg-green-500' : qualityData.dimension_scores.distribution >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${qualityData.dimension_scores.distribution}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 问题清单区 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 错误列表 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
            错误 ({qualityData.errors.length})
          </h3>
          {qualityData.errors.length === 0 ? (
            <div className="flex items-center text-sm text-gray-500">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              无错误
            </div>
          ) : (
            <div className="space-y-3">
              {qualityData.errors.map((error, index) => (
                <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-start">
                    {getSeverityIcon(error.severity)}
                    <div className="ml-3 flex-1">
                      <p className="text-sm font-medium text-red-800">{error.message}</p>
                      <p className="text-xs text-red-600 mt-1">错误代码: {error.code}</p>
                      {error.details && (
                        <div className="mt-2 text-xs text-red-700 bg-red-100 rounded p-2">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(error.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 警告列表 */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-yellow-500" />
            警告 ({qualityData.warnings.length})
          </h3>
          {qualityData.warnings.length === 0 ? (
            <div className="flex items-center text-sm text-gray-500">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              无警告
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {qualityData.warnings.map((warning, index) => (
                <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start">
                    {getSeverityIcon(warning.severity)}
                    <div className="ml-3 flex-1">
                      <p className="text-sm font-medium text-yellow-800">{warning.message}</p>
                      <p className="text-xs text-yellow-600 mt-1">警告代码: {warning.code}</p>
                      {warning.details && (
                        <div className="mt-2 text-xs text-yellow-700 bg-yellow-100 rounded p-2">
                          <pre className="whitespace-pre-wrap">
                            {JSON.stringify(warning.details, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 建议区 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-blue-500" />
          改进建议 ({qualityData.recommendations.length})
        </h3>
        {qualityData.recommendations.length === 0 ? (
          <div className="flex items-center text-sm text-gray-500">
            <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
            数据质量良好，无需改进
          </div>
        ) : (
          <div className="space-y-2">
            {qualityData.recommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium">
                  {index + 1}
                </div>
                <p className="ml-3 text-sm text-blue-800">{recommendation}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 统计摘要区 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2 text-gray-500" />
          统计摘要
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {qualityData.stats && Object.entries(qualityData.stats).map(([key, value]) => {
            // 过滤掉复杂的嵌套对象，只显示基本统计信息
            if (typeof value === 'object' && value !== null) {
              return null
            }

            // 格式化显示
            let displayValue = value
            let displayKey = key

            // 特殊字段格式化
            if (key.includes('rate') || key.includes('ratio')) {
              displayValue = `${(Number(value) * 100).toFixed(2)}%`
            } else if (key.includes('size')) {
              displayValue = `${Number(value).toFixed(2)} MB`
            } else if (typeof value === 'number') {
              displayValue = Number(value).toLocaleString()
            }

            // 字段名称映射
            const keyMap: Record<string, string> = {
              'total_rows': '总行数',
              'total_columns': '总列数',
              'sample_rows_used': '采样行数',
              'file_size_mb': '文件大小',
              'global_missing_rate': '全局缺失率',
              'missing_cells': '缺失单元格数',
              'total_cells': '总单元格数',
            }

            displayKey = keyMap[key] || key.replace(/_/g, ' ')

            return (
              <div key={key} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{displayKey}</p>
                <p className="text-lg font-semibold text-gray-900">{String(displayValue)}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* 返回按钮 */}
      <div className="flex justify-end">
        <Link
          to={`/assets/${id}`}
          className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          返回数据集详情
        </Link>
      </div>
    </div>
  )
}
