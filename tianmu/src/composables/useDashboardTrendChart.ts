import { ref, type Ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import type { EChartsType } from 'echarts/core'
import { getTrendData } from '@/api/device'
import { BEIJING_TIME_ZONE } from '@/utils/format'

export type TimeRangeKey = '1H' | '6H' | '24H' | '7D'

export const dashboardTimeRanges: Array<{
  key: TimeRangeKey
  label: string
  hours: 1 | 6 | 24 | 168
}> = [
  { key: '1H', label: '1H', hours: 1 },
  { key: '6H', label: '6H', hours: 6 },
  { key: '24H', label: '24H', hours: 24 },
  { key: '7D', label: '7D', hours: 168 },
]

type EchartsModule = typeof import('@/utils/slimEcharts')
type EChartsOption = Parameters<EChartsType['setOption']>[0]

export function useDashboardTrendChart(selectedDeviceId: Ref<string>) {
  const chartRef = ref<HTMLElement>()
  const activeTimeRange = ref<TimeRangeKey>('1H')
  const chartTimeData = ref<string[]>([])
  const chartSeriesData = [
    ref<Array<number | null>>([]),
    ref<Array<number | null>>([]),
    ref<Array<number | null>>([]),
    ref<Array<number | null>>([]),
    ref<Array<number | null>>([]),
    ref<Array<number | null>>([]),
  ]
  let chart: EChartsType | null = null
  let echartsModule: EchartsModule | null = null
  let echartsLoadPromise: Promise<EchartsModule> | null = null
  let resizeObserver: ResizeObserver | null = null
  let requestId = 0

  function resizeChart() {
    chart?.resize()
  }

  async function loadEcharts() {
    echartsLoadPromise ??= import('@/utils/slimEcharts')
    echartsModule = await echartsLoadPromise
    return echartsModule
  }

  async function initChart() {
    if (!chartRef.value) return
    const { echarts } = await loadEcharts()
    if (!chartRef.value || chart) return
    chart = echarts.init(chartRef.value)
    chart.setOption(createChartOption(echarts))
    resizeObserver = new ResizeObserver(resizeChart)
    resizeObserver.observe(chartRef.value)
    window.addEventListener('resize', resizeChart, { passive: true })
  }

  function renderChart() {
    chart?.setOption({
      xAxis: { data: chartTimeData.value },
      series: chartSeriesData.map((series) => ({ data: series.value })),
    })
  }

  function clearChart() {
    chartTimeData.value = []
    chartSeriesData.forEach((series) => {
      series.value = []
    })
    renderChart()
  }

  async function loadTrendData(
    deviceId = selectedDeviceId.value,
    range = activeTimeRange.value,
  ) {
    const currentRequest = ++requestId
    if (!deviceId) {
      clearChart()
      return
    }
    const rangeConfig = dashboardTimeRanges.find((item) => item.key === range)
    if (!rangeConfig) return

    try {
      const records = await getTrendData(deviceId, rangeConfig.hours)
      if (
        currentRequest !== requestId
        || deviceId !== selectedDeviceId.value
        || range !== activeTimeRange.value
      ) {
        return
      }
      chartTimeData.value = records.map((item) => formatTrendTime(item.timestamp, range))
      chartSeriesData[0]!.value = records.map((item) => item.temperature)
      chartSeriesData[1]!.value = records.map((item) => item.humidity)
      chartSeriesData[2]!.value = records.map((item) => item.aqi)
      chartSeriesData[3]!.value = records.map((item) => item.pm25)
      chartSeriesData[4]!.value = records.map((item) => item.tvoc)
      chartSeriesData[5]!.value = records.map((item) => item.eco2)
      renderChart()
    } catch {
      if (currentRequest === requestId) {
        ElMessage.error('趋势数据加载失败')
      }
    }
  }

  function switchTimeRange(range: TimeRangeKey) {
    activeTimeRange.value = range
    void loadTrendData(selectedDeviceId.value, range)
  }

  function disposeChart() {
    requestId += 1
    resizeObserver?.disconnect()
    resizeObserver = null
    window.removeEventListener('resize', resizeChart)
    chart?.dispose()
    chart = null
  }

  return {
    chartRef,
    timeRanges: dashboardTimeRanges,
    activeTimeRange,
    initChart,
    loadTrendData,
    switchTimeRange,
    disposeChart,
  }
}

function formatTrendTime(timestamp: string | null, range: TimeRangeKey) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return '--'
  if (range === '7D') {
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: BEIJING_TIME_ZONE,
    })
  }
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: BEIJING_TIME_ZONE,
  })
}

function createChartOption(
  echarts: EchartsModule['echarts'],
): EChartsOption {
  const line = (
    name: string,
    color: string,
    yAxisIndex = 0,
    withArea = false,
  ) => ({
    name,
    type: 'line' as const,
    yAxisIndex,
    data: [],
    smooth: true,
    symbol: 'none',
    lineStyle: { color, width: 2 },
    itemStyle: { color },
    areaStyle: withArea
      ? {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${color}40` },
            { offset: 1, color: `${color}05` },
          ]),
        }
      : undefined,
    animationDuration: 800,
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(51, 65, 102, 0.45)',
      textStyle: { color: '#e8ecf4' },
    },
    legend: {
      type: 'scroll',
      data: ['温度', '湿度', 'AQI', 'PM2.5', 'TVOC', 'eCO2'],
      textStyle: { color: '#8b95b0' },
      top: 0,
      left: 0,
      right: 0,
      pageTextStyle: { color: '#8b95b0' },
      pageIconColor: '#38bdf8',
      pageIconInactiveColor: '#475569',
    },
    grid: {
      left: '3%',
      right: 110,
      bottom: '3%',
      top: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
      axisLine: { lineStyle: { color: 'rgba(51, 65, 102, 0.45)' } },
      axisLabel: { color: '#8b95b0' },
    },
    yAxis: [
      {
        type: 'value',
        axisLine: { show: true, lineStyle: { color: 'rgba(51, 65, 102, 0.45)' } },
        axisLabel: { color: '#8b95b0' },
        splitLine: { lineStyle: { color: 'rgba(51, 65, 102, 0.25)' } },
      },
      {
        type: 'value',
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#FBBF24' } },
        axisLabel: { color: '#FBBF24' },
        splitLine: { show: false },
      },
      {
        type: 'value',
        position: 'right',
        offset: 54,
        axisLine: { show: true, lineStyle: { color: '#A78BFA' } },
        axisLabel: { color: '#A78BFA' },
        splitLine: { show: false },
      },
    ],
    series: [
      line('温度', '#EF4444', 0, true),
      line('湿度', '#3B82F6', 0, true),
      line('AQI', '#22C55E'),
      line('PM2.5', '#94A3B8', 1),
      line('TVOC', '#FBBF24', 1),
      line('eCO2', '#A78BFA', 2),
    ],
  }
}
