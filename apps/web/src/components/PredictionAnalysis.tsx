import { useQuery } from '@tanstack/react-query'
import { resultsApi } from '../lib/api'
import { Loader2, AlertCircle, TrendingUp, BarChart3, ScatterChart } from 'lucide-react'
import {
  ScatterChart as RechartsScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Line,
} from 'recharts'

interface PredictionAnalysisProps {
  experimentId: string
}

export function PredictionAnalysis({ experimentId }: PredictionAnalysisProps) {
  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['prediction-analysis', experimentId],
    queryFn: () => resultsApi.getPredictionAnalysis(experimentId),
    enabled: !!experimentId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center text-red-700">
          <AlertCircle className="w-5 h-5 mr-2" />
          <span>加载预测分析数据失败</span>
        </div>
      </div>
    )
  }

  if (!analysis?.analysis_available) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 mr-3 text-amber-600 mt-0.5" />
          <div>
            <h4 className="text-amber-800 font-medium">预测分析不可用</h4>
            <p className="text-amber-700 text-sm mt-1">
              {analysis?.analysis_unavailable_reason || '当前实验缺少逐样本预测工件，无法生成该图表'}
            </p>
            <p className="text-amber-600 text-xs mt-2">
              提示：重新训练实验可生成预测分析数据
            </p>
          </div>
        </div>
      </div>
    )
  }

  const { data: analysisData } = analysis

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-blue-700 text-sm">
          <strong>残差定义:</strong> {analysis.residual_definition}
          <span className="ml-2 text-blue-600">
            （正值 = 预测偏低，负值 = 预测偏高）
          </span>
        </p>
      </div>

      <ResidualSummaryCard summary={analysisData!.residual_summary} sampleCount={analysisData!.sample_count} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PredictionVsActualChart data={analysisData!.prediction_scatter_points} />
        <ResidualHistogram bins={analysisData!.residual_histogram_bins} />
      </div>

      <ResidualVsPredictedChart data={analysisData!.residual_scatter_points} />
    </div>
  )
}

interface ResidualSummaryCardProps {
  summary: {
    mean: number
    std: number
    min: number
    max: number
    p50: number
    p95: number
  }
  sampleCount: number
}

function ResidualSummaryCard({ summary, sampleCount }: ResidualSummaryCardProps) {
  const stats = [
    { label: '样本数', value: sampleCount.toLocaleString(), color: 'text-gray-900' },
    { label: '均值', value: summary.mean.toFixed(4), color: summary.mean >= 0 ? 'text-green-600' : 'text-red-600' },
    { label: '标准差', value: summary.std.toFixed(4), color: 'text-gray-900' },
    { label: '中位数', value: summary.p50.toFixed(4), color: 'text-gray-900' },
    { label: '最小值', value: summary.min.toFixed(4), color: 'text-red-600' },
    { label: '最大值', value: summary.max.toFixed(4), color: 'text-green-600' },
    { label: '95分位', value: summary.p95.toFixed(4), color: 'text-amber-600' },
  ]

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
        残差摘要
      </h3>
      <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {stats.map((stat, index) => (
          <div key={index}>
            <p className="text-xs text-gray-500">{stat.label}</p>
            <p className={`text-lg font-semibold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

interface PredictionVsActualChartProps {
  data: Array<{ actual: number; predicted: number }>
}

function PredictionVsActualChart({ data }: PredictionVsActualChartProps) {
  const chartData = data.map((d) => ({
    x: d.actual,
    y: d.predicted,
  }))

  const allValues = [...data.map((d) => d.actual), ...data.map((d) => d.predicted)]
  const minVal = Math.min(...allValues)
  const maxVal = Math.max(...allValues)
  const idealLineMin = minVal
  const idealLineMax = maxVal

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <ScatterChart className="w-5 h-5 mr-2 text-blue-600" />
        预测 vs 实际
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              name="实际值"
              label={{ value: '实际值', position: 'bottom' }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="预测值"
              label={{ value: '预测值', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: number) => value.toFixed(4)}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Scatter
              name="样本点"
              data={chartData}
              fill="#3b82f6"
              fillOpacity={0.6}
            />
            <Line
              type="linear"
              data={[
                { x: idealLineMin, y: idealLineMin },
                { x: idealLineMax, y: idealLineMax },
              ]}
              stroke="#10b981"
              strokeDasharray="5 5"
              strokeWidth={2}
              dot={false}
              name="理想线 (y=x)"
              dataKey="y"
            />
          </RechartsScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        绿色虚线表示理想预测线 (y=x)，点越接近虚线表示预测越准确
      </p>
    </div>
  )
}

interface ResidualHistogramProps {
  bins: Array<{ bin_start: number; bin_end: number; count: number }>
}

function ResidualHistogram({ bins }: ResidualHistogramProps) {
  const chartData = bins.map((bin) => ({
    name: `${bin.bin_start.toFixed(2)}`,
    range: `${bin.bin_start.toFixed(2)} ~ ${bin.bin_end.toFixed(2)}`,
    count: bin.count,
    fill: bin.bin_start >= 0 ? '#10b981' : '#ef4444',
  }))

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
        残差分布
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={60}
              tick={{ fontSize: 10 }}
              label={{ value: '残差范围', position: 'bottom', offset: 40 }}
            />
            <YAxis
              label={{ value: '样本数', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: number, name: string) => [value, name === 'count' ? '样本数' : name]}
              labelFormatter={(label) => `残差: ${label}`}
            />
            <Bar dataKey="count" name="样本数">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        绿色表示正残差（预测偏低），红色表示负残差（预测偏高）
      </p>
    </div>
  )
}

interface ResidualVsPredictedChartProps {
  data: Array<{ predicted: number; residual: number }>
}

function ResidualVsPredictedChart({ data }: ResidualVsPredictedChartProps) {
  const chartData = data.map((d) => ({
    x: d.predicted,
    y: d.residual,
  }))

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
        残差 vs 预测值
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              name="预测值"
              label={{ value: '预测值', position: 'bottom' }}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="残差"
              label={{ value: '残差', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(value: number) => value.toFixed(4)}
              cursor={{ strokeDasharray: '3 3' }}
            />
            <Line
              type="linear"
              data={[
                { x: Math.min(...data.map((d) => d.predicted)), y: 0 },
                { x: Math.max(...data.map((d) => d.predicted)), y: 0 },
              ]}
              stroke="#6b7280"
              strokeDasharray="5 5"
              strokeWidth={1}
              dot={false}
              name="零线"
              dataKey="y"
            />
            <Scatter
              name="样本点"
              data={chartData}
              fill="#8b5cf6"
              fillOpacity={0.6}
            />
          </RechartsScatterChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">
        检查残差是否存在系统性偏差（如随预测值变化的趋势）
      </p>
    </div>
  )
}
