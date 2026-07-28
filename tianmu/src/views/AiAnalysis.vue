<!-- AiAnalysis.vue -->
<!-- AI 分析页：环境综合评分、风险预警、智能建议、本周环境周报 -->
<template>
  <div class="ai-analysis-page">
    <!-- 环境综合评分 -->
    <section class="section score-section animate-fade-up-blur">
      <h2 class="section-title">环境综合评分</h2>
      <div class="score-content">
        <div ref="gaugeChartRef" class="gauge-chart" />
        <p class="score-comment">{{ scoreComment }}</p>
      </div>
    </section>

    <AiRiskSuggestionPanel
      :mold="{ text: moldRiskText, className: moldRiskClass, icon: moldRiskIcon }"
      :gas="{ text: gasRiskText, className: gasRiskClass, icon: gasRiskIcon }"
      :risks="riskItems"
      :suggestions="suggestions"
      :source="suggestionSource"
    />

    <!-- 本周环境周报 -->
    <section class="section report-section animate-fade-up-blur" data-delay="3">
      <div class="report-header">
        <h2 class="section-title">本周环境周报</h2>
        <el-button size="small" class="export-btn" @click="handleExportPdf">
          导出 PDF
        </el-button>
      </div>
      <p v-if="weeklySummary" class="weekly-summary">{{ weeklySummary }}</p>
      <div ref="weeklyChartRef" class="weekly-chart" />
    </section>

    <!-- AI 分析按钮 -->
    <section class="analyze-section animate-fade-up-blur">
      <el-button
        type="primary"
        size="large"
        :loading="analyzing"
        class="analyze-btn"
        @click="handleAnalyze"
      >
        {{ analyzing ? 'AI 分析中...' : '🔍 开始 AI 分析' }}
      </el-button>
      <p v-if="!deviceStore.selectedDeviceId" class="analyze-hint">
        未选中设备，点击后将自动使用第一个设备
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import type { EChartsType } from 'echarts/core'
import { useDeviceStore } from '@/stores/device'
import { getLatestData, getDeviceList } from '@/api/device'
import { getAiSuggestions, getEnvironmentScore, getRiskWarnings, getWeeklyReport } from '@/api/ai'
import { showErrorToast, showInfoToast, showSuccessToast, showWarningToast } from '@/utils/alert'
import AiRiskSuggestionPanel from '@/components/ai/AiRiskSuggestionPanel.vue'

defineOptions({ name: 'AiAnalysisPage' })

// ---------- Store ----------
const deviceStore = useDeviceStore()

// ---------- 评分数据 ----------
const environmentScore = ref(85)
const scoreSummary = ref('')

const scoreComment = computed(() => {
  if (scoreSummary.value) return scoreSummary.value
  if (environmentScore.value >= 90) return '当前室内环境整体优秀，各项指标均处于最佳范围，非常适合工作与休息。'
  if (environmentScore.value >= 70) return '当前室内环境整体舒适，空气质量极佳。'
  if (environmentScore.value >= 40) return '当前室内环境一般，部分指标需要关注，建议适当调整。'
  return '当前室内环境较差，多项指标超标，请尽快改善通风和温控。'
})

const scoreRating = computed(() => {
  if (environmentScore.value >= 90) return '优秀'
  if (environmentScore.value >= 70) return '良好'
  if (environmentScore.value >= 40) return '一般'
  return '差'
})

// ---------- 风险预警数据 ----------
const moldRisk = ref(0)   // 0-低/1-中/2-高/3-极高
const gasValue = ref(0)    // 0=正常

const moldRiskLabels: Record<number, string> = { 0: '低', 1: '中', 2: '高', 3: '极高' }
const moldRiskClasses: Record<number, string> = { 0: 'risk-low', 1: 'risk-medium', 2: 'risk-high', 3: 'risk-critical' }
const moldRiskIcons: Record<number, string> = { 0: '\u2713', 1: '\u26A0', 2: '\u26A0', 3: '\u26A0' }

const moldRiskText = computed(() => moldRiskLabels[moldRisk.value] ?? '低')
const moldRiskClass = computed(() => moldRiskClasses[moldRisk.value] ?? 'risk-low')
const moldRiskIcon = computed(() => moldRiskIcons[moldRisk.value] ?? '\u2713')

const gasRiskText = computed(() => (gasValue.value === 0 ? '正常' : '异常'))
const gasRiskClass = computed(() => (gasValue.value === 0 ? 'risk-low' : 'risk-critical'))
const gasRiskIcon = computed(() => (gasValue.value === 0 ? '\u2713' : '\u26A0'))
const riskItems = ref<Array<{ field: string; level: 'warning' | 'critical'; title: string; message: string }>>([])

// ---------- 智能建议（模拟数据） ----------
const suggestions = ref([
  { icon: '\uD83D\uDCA1', title: '光照偏低 (500lx)', desc: '建议打开主灯或拉开窗帘' },
  { icon: '\uD83C\uDF2C\uFE0F', title: 'CO2 浓度上升中 (450ppm)', desc: '建议适当开窗通风 15 分钟' },
  { icon: '\uD83D\uDC55', title: '温度适宜 (25.6\u2103)', desc: '建议穿着轻薄长袖' },
  { icon: '\uD83D\uDCA7', title: '湿度偏高 (68%)', desc: '建议开启除湿功能' },
])

const aiIconMap: Record<string, string> = {
  i: '\u2139',
  light: '\uD83D\uDCA1',
  wind: '\uD83C\uDF2C\uFE0F',
  water: '\uD83D\uDCA7',
  humidity: '\uD83D\uDCA7',
  temp: '\uD83C\uDF21',
  temperature: '\uD83C\uDF21',
  air: '\uD83C\uDF2C\uFE0F',
  aqi: '\uD83C\uDF2C\uFE0F',
  tvoc: '\uD83C\uDF2C\uFE0F',
  eco2: '\uD83C\uDF2C\uFE0F',
  gas: '\u26A0',
  mold: '\u26A0',
  mold_risk: '\u26A0',
  ok: '\u2713',
}

const suggestionSource = ref<'llm' | 'rule' | ''>('')
const weeklySummary = ref('')
const analyzing = ref(false)

// ---------- 手动触发 AI 分析 ----------
async function handleAnalyze() {
  if (analyzing.value) return
  if (!deviceStore.selectedDeviceId) {
    await ensureDeviceSelected()
  }
  if (!deviceStore.selectedDeviceId) {
    showWarningToast('请先绑定或选择一个设备')
    return
  }
  analyzing.value = true
  try {
    const results = await Promise.all([fetchSensorData(), fetchAiAnalysis(true), fetchRisksAndWeeklyReport(true)])
    if (results.every(Boolean)) {
      showSuccessToast('LLM 分析完成')
    } else {
      showWarningToast('LLM 未返回结果，当前展示规则分析或兜底数据')
    }
  } catch (err) {
    const message = getApiErrorMessage(err, 'AI 分析失败，请检查后端服务、LLM 配置或登录状态')
    if (!message.includes('当前处于演示模式')) {
      console.error('AI 分析失败', err)
    }
    showErrorToast(message)
  } finally {
    analyzing.value = false
  }
}

// ---------- 尝试从 store 获取传感器数据 ----------
async function fetchSensorData() {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return false
  try {
    const data = await getLatestData(deviceId)
    if (data) {
      moldRisk.value = data.mold_risk ?? 0
      gasValue.value = data.gas ?? 0
    }
    return true
  } catch (err) {
    console.error('获取传感器数据失败', err)
    // 使用模拟数据兜底
    return false
  }
}

async function fetchAiAnalysis(forceLlm = false) {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return false
  try {
    const [scoreData, suggestionData] = await Promise.all([
      getEnvironmentScore(deviceId),
      getAiSuggestions(deviceId, forceLlm),
    ])
    if (typeof scoreData.score === 'number') {
      environmentScore.value = scoreData.score
      scoreSummary.value = scoreData.summary || ''
      renderGaugeChart()
    }
    if (suggestionData.suggestions?.length) {
      suggestions.value = suggestionData.suggestions.map((item) => ({
        icon: aiIconMap[item.icon] || item.icon,
        title: item.title,
        desc: item.desc,
      }))
      suggestionSource.value = suggestionData.source || 'rule'
    }
    return forceLlm ? suggestionData.source === 'llm' : true
  } catch (err) {
    if (forceLlm) throw err
    console.error('获取 AI 建议失败', err)
    // 保留本地模拟建议作为兜底
    return false
  }
}

async function fetchRisksAndWeeklyReport(forceLlm = false) {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return false
  try {
    const [riskData, weeklyData] = await Promise.all([
      getRiskWarnings(deviceId),
      getWeeklyReport(deviceId, forceLlm),
    ])
    riskItems.value = riskData.risks || []
    if (weeklyData.days?.length) {
      const labels = weeklyData.days.map((item) => item.date.slice(5))
      const temperature = weeklyData.days.map((item) => item.temperature ?? 0)
      const humidity = weeklyData.days.map((item) => item.humidity ?? 0)
      const aqi = weeklyData.days.map((item) => item.aqi ?? 0)
      updateWeeklyChart(labels, temperature, humidity, aqi)
    }
    weeklySummary.value = weeklyData.summary || ''
    return forceLlm ? weeklyData.source === 'llm' : true
  } catch (err) {
    if (forceLlm) throw err
    console.error('获取风险和周报失败', err)
    // 周报和风险接口失败时保留页面兜底数据
    return false
  }
}

function getApiErrorMessage(err: unknown, fallback: string) {
  const error = err as { response?: { data?: { detail?: string; message?: string } }; message?: string }
  return error.response?.data?.detail || error.response?.data?.message || error.message || fallback
}

// ---------- 环形进度图（ECharts gauge） ----------
const gaugeChartRef = ref<HTMLElement>()
type EchartsModule = typeof import('@/utils/slimEcharts')
let echartsModule: EchartsModule | null = null
let echartsLoadPromise: Promise<EchartsModule> | null = null
let gaugeChart: EChartsType | null = null

async function loadEcharts() {
  echartsLoadPromise ??= import('@/utils/slimEcharts')
  echartsModule = await echartsLoadPromise
  return echartsModule
}

function getScoreColor(score: number): string {
  if (score >= 70) return '#10B981'
  if (score >= 40) return '#F59E0B'
  return '#EF4444'
}

async function initGaugeChart() {
  if (!gaugeChartRef.value) return
  const { echarts } = await loadEcharts()
  if (!gaugeChartRef.value || gaugeChart) return
  gaugeChart = echarts.init(gaugeChartRef.value)
  renderGaugeChart()
}

function renderGaugeChart() {
  if (!gaugeChart) return
  const color = getScoreColor(environmentScore.value)
  gaugeChart.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 220,
        endAngle: -40,
        min: 0,
        max: 100,
        splitNumber: 10,
        radius: '90%',
        center: ['50%', '55%'],
        axisLine: {
          lineStyle: {
            width: 18,
            color: [
              [0.4, '#EF4444'],
              [0.7, '#F59E0B'],
              [1, '#10B981'],
            ],
          },
        },
        pointer: {
          icon: 'circle',
          length: '12%',
          width: 30,
          offsetCenter: [0, '-60%'],
          itemStyle: {
            color: color,
          },
        },
        axisTick: {
          length: 6,
          lineStyle: { color: 'auto', width: 1.5 },
        },
        splitLine: {
          length: 12,
          lineStyle: { color: 'auto', width: 2 },
        },
        axisLabel: {
          color: '#9CA3AF',
          fontSize: 11,
          distance: 20,
          fontFamily: 'JetBrains Mono, monospace',
        },
        title: {
          offsetCenter: [0, '20%'],
          fontSize: 16,
          color: '#9CA3AF',
          fontFamily: 'Inter, sans-serif',
        },
        detail: {
          fontSize: 42,
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: 700,
          offsetCenter: [0, '-10%'],
          valueAnimation: true,
          formatter: (value: number) => `${value}`,
          color: color,
        },
        data: [
          {
            value: environmentScore.value,
            name: scoreRating.value,
          },
        ],
      },
    ],
  })
}

// ---------- 本周环境周报（ECharts 柱状+折线混合图） ----------
const weeklyChartRef = ref<HTMLElement>()
let weeklyChart: EChartsType | null = null

// 模拟 7 天数据
const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const mockWeeklyData = {
  temperature: [24.2, 25.1, 23.8, 26.0, 25.6, 24.5, 25.3],
  humidity: [55, 60, 58, 65, 68, 62, 57],
  aqi: [35, 42, 38, 50, 45, 40, 36],
}

async function initWeeklyChart() {
  if (!weeklyChartRef.value) return
  const { echarts } = await loadEcharts()
  if (!weeklyChartRef.value || weeklyChart) return
  weeklyChart = echarts.init(weeklyChartRef.value)
  updateWeeklyChart(weekDays, mockWeeklyData.temperature, mockWeeklyData.humidity, mockWeeklyData.aqi)
}

function updateWeeklyChart(
  labels: string[],
  temperature: number[],
  humidity: number[],
  aqi: number[],
) {
  if (!weeklyChart || !echartsModule) return
  weeklyChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(17, 24, 39, 0.9)',
      borderColor: 'rgba(255, 255, 255, 0.06)',
      textStyle: { color: '#F9FAFB', fontFamily: 'Inter, sans-serif' },
    },
    legend: {
      data: ['温度 (\u2103)', '湿度 (%)', 'AQI'],
      textStyle: { color: '#9CA3AF', fontFamily: 'Inter, sans-serif' },
      top: 0,
    },
    grid: {
      left: 50,
      right: 50,
      bottom: 30,
      top: 40,
    },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#9CA3AF', fontFamily: 'Inter, sans-serif' },
    },
    yAxis: [
      {
        type: 'value',
        name: '温度/\u2103',
        nameTextStyle: { color: '#9CA3AF', fontFamily: 'Inter, sans-serif' },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
        axisLabel: { color: '#9CA3AF', fontFamily: 'JetBrains Mono, monospace' },
      },
      {
        type: 'value',
        name: '湿度(%)/AQI',
        nameTextStyle: { color: '#9CA3AF', fontFamily: 'Inter, sans-serif' },
        axisLine: { show: false },
        splitLine: { show: false },
        axisLabel: { color: '#9CA3AF', fontFamily: 'JetBrains Mono, monospace' },
      },
    ],
    series: [
      {
        name: '温度 (\u2103)',
        type: 'bar',
        yAxisIndex: 0,
        data: temperature,
        barWidth: '20%',
        itemStyle: {
          color: new echartsModule.echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#06B6D4' },
            { offset: 1, color: 'rgba(6, 182, 212, 0.2)' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: '湿度 (%)',
        type: 'line',
        yAxisIndex: 1,
        data: humidity,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#3B82F6', width: 2 },
        itemStyle: { color: '#3B82F6' },
        areaStyle: {
          color: new echartsModule.echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.15)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' },
          ]),
        },
      },
      {
        name: 'AQI',
        type: 'line',
        yAxisIndex: 1,
        data: aqi,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 6,
        lineStyle: { color: '#10B981', width: 2 },
        itemStyle: { color: '#10B981' },
      },
    ],
  })
}

// ---------- 导出 PDF ----------
function handleExportPdf() {
  showInfoToast('功能开发中')
}

// ---------- 响应式处理 ----------
function handleResize() {
  gaugeChart?.resize()
  weeklyChart?.resize()
}

// ---------- 生命周期 ----------
async function ensureDeviceSelected() {
  if (deviceStore.selectedDeviceId) return
  try {
    const list = await getDeviceList()
    if (list?.length) {
      deviceStore.setDevices(list)
      const candidates = [
        ...list.filter((device) => device.status === 'online'),
        ...list.filter((device) => device.status !== 'online'),
      ]
      for (const device of candidates) {
        const data = await getLatestData(device.device_id).catch(() => null)
        if (data) {
          deviceStore.selectDevice(device.device_id)
          return
        }
      }
      if (candidates[0]) {
        deviceStore.selectDevice(candidates[0].device_id)
      }
    }
  } catch {
    // 拉取失败时保持 selectedDeviceId 为 null
  }
}

onMounted(async () => {
  await Promise.all([initGaugeChart(), initWeeklyChart()])
  await ensureDeviceSelected()
  fetchSensorData()
  fetchAiAnalysis()
  fetchRisksAndWeeklyReport()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  gaugeChart?.dispose()
  weeklyChart?.dispose()
})

// 监听选中设备变化，重新获取数据
watch(() => deviceStore.selectedDeviceId, () => {
  fetchSensorData()
  fetchAiAnalysis()
  fetchRisksAndWeeklyReport()
})
</script>

<style scoped src="./styles/AiAnalysis.css"></style>
