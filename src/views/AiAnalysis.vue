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

    <!-- 风险预警 + 智能建议 -->
    <section class="section alert-suggest-row">
      <!-- 风险预警（左栏） -->
      <div class="panel risk-panel animate-fade-up-blur" data-delay="1">
        <h2 class="section-title">风险预警</h2>
        <div class="risk-list">
          <!-- 霉菌风险 -->
          <div
            class="risk-item"
            :class="moldRiskClass"
          >
            <span class="risk-icon">{{ moldRiskIcon }}</span>
            <div class="risk-info">
              <span class="risk-label">霉菌风险</span>
              <span class="risk-value">{{ moldRiskText }}</span>
            </div>
          </div>
          <!-- 燃气安全 -->
          <div
            class="risk-item"
            :class="gasRiskClass"
          >
            <span class="risk-icon">{{ gasRiskIcon }}</span>
            <div class="risk-info">
              <span class="risk-label">燃气安全</span>
              <span class="risk-value">{{ gasRiskText }}</span>
            </div>
          </div>
          <div
            v-for="risk in riskItems"
            :key="`${risk.field}-${risk.title}`"
            class="risk-item"
            :class="risk.level === 'critical' ? 'risk-critical' : 'risk-medium'"
          >
            <span class="risk-icon">{{ risk.level === 'critical' ? '\u26A0' : '!' }}</span>
            <div class="risk-info">
              <span class="risk-label">{{ risk.title }}</span>
              <span class="risk-value">{{ risk.message }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 智能建议（右栏） -->
      <div class="panel suggest-panel animate-fade-up-blur" data-delay="2">
        <h2 class="section-title">智能建议</h2>
        <div class="suggest-list">
          <div
            v-for="(item, idx) in suggestions"
            :key="idx"
            class="suggest-item"
          >
            <span class="suggest-icon">{{ item.icon }}</span>
            <div class="suggest-info">
              <span class="suggest-title">{{ item.title }}</span>
              <span class="suggest-desc">{{ item.desc }}</span>
            </div>
          </div>
        </div>
        <p class="ai-disclaimer">AI 生成，仅供参考</p>
      </div>
    </section>

    <!-- 本周环境周报 -->
    <section class="section report-section animate-fade-up-blur" data-delay="3">
      <div class="report-header">
        <h2 class="section-title">本周环境周报</h2>
        <el-button size="small" class="export-btn" @click="handleExportPdf">
          导出 PDF
        </el-button>
      </div>
      <div ref="weeklyChartRef" class="weekly-chart" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { useDeviceStore } from '@/store/device'
import { getLatestData } from '@/api/device'
import { getAiSuggestions, getEnvironmentScore, getRiskWarnings, getWeeklyReport } from '@/api/ai'
import { showInfoToast } from '@/utils/alert'

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
  temp: '\uD83C\uDF21',
  ok: '\u2713',
}

// ---------- 尝试从 store 获取传感器数据 ----------
async function fetchSensorData() {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return
  try {
    const data = await getLatestData(deviceId)
    if (data) {
      moldRisk.value = data.mold_risk ?? 0
      gasValue.value = data.gas ?? 0
    }
  } catch {
    // 使用模拟数据兜底
  }
}

async function fetchAiAnalysis() {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return
  try {
    const [scoreData, suggestionData] = await Promise.all([
      getEnvironmentScore(deviceId),
      getAiSuggestions(deviceId),
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
    }
  } catch {
    // 保留本地模拟建议作为兜底
  }
}

async function fetchRisksAndWeeklyReport() {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return
  try {
    const [riskData, weeklyData] = await Promise.all([
      getRiskWarnings(deviceId),
      getWeeklyReport(deviceId),
    ])
    riskItems.value = riskData.risks || []
    if (weeklyData.days?.length) {
      const labels = weeklyData.days.map((item) => item.date.slice(5))
      const temperature = weeklyData.days.map((item) => item.temperature ?? 0)
      const humidity = weeklyData.days.map((item) => item.humidity ?? 0)
      const aqi = weeklyData.days.map((item) => item.aqi ?? 0)
      updateWeeklyChart(labels, temperature, humidity, aqi)
    }
  } catch {
    // 周报和风险接口失败时保留页面兜底数据
  }
}

// ---------- 环形进度图（ECharts gauge） ----------
const gaugeChartRef = ref<HTMLElement>()
let gaugeChart: echarts.ECharts | null = null

function getScoreColor(score: number): string {
  if (score >= 70) return '#10B981'
  if (score >= 40) return '#F59E0B'
  return '#EF4444'
}

function initGaugeChart() {
  if (!gaugeChartRef.value) return
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
let weeklyChart: echarts.ECharts | null = null

// 模拟 7 天数据
const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const mockWeeklyData = {
  temperature: [24.2, 25.1, 23.8, 26.0, 25.6, 24.5, 25.3],
  humidity: [55, 60, 58, 65, 68, 62, 57],
  aqi: [35, 42, 38, 50, 45, 40, 36],
}

function initWeeklyChart() {
  if (!weeklyChartRef.value) return
  weeklyChart = echarts.init(weeklyChartRef.value)
  updateWeeklyChart(weekDays, mockWeeklyData.temperature, mockWeeklyData.humidity, mockWeeklyData.aqi)
}

function updateWeeklyChart(
  labels: string[],
  temperature: number[],
  humidity: number[],
  aqi: number[],
) {
  if (!weeklyChart) return
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
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
onMounted(() => {
  initGaugeChart()
  initWeeklyChart()
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

<style scoped>
.ai-analysis-page {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-card);
}

.section {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.058), rgba(255, 255, 255, 0.012)),
    var(--bg-card);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: var(--border-glass);
  border-radius: var(--radius-card);
  padding: var(--spacing-card);
  box-shadow: var(--shadow-card);
}

.section::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-violet), var(--color-cube-primary), var(--color-cube-accent));
  background-size: 200% 100%;
  opacity: 0.7;
  animation: border-flow 5s linear infinite;
}

.section-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-module);
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 17px;
  border-radius: var(--radius-full);
  background: linear-gradient(180deg, var(--color-cube-violet), var(--color-cube-primary));
  box-shadow: 0 0 14px rgba(139, 92, 246, 0.38);
}

/* ---- 环境综合评分 ---- */
.score-section {
  text-align: center;
}

.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.gauge-chart {
  width: 280px;
  height: 220px;
}

.score-comment {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 400px;
}

/* ---- 风险预警 + 智能建议 双栏 ---- */
.alert-suggest-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-card);
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  overflow: visible;
}

.alert-suggest-row::before {
  display: none;
}

.panel {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.012)),
    var(--bg-card);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: var(--border-glass);
  border-radius: var(--radius-card);
  padding: var(--spacing-card);
  box-shadow: var(--shadow-card);
}

/* ---- 风险预警 ---- */
.risk-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-element);
}

.risk-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-element);
  padding: 12px 16px;
  border-radius: var(--radius-button);
  border: 1px solid rgba(255, 255, 255, 0.055);
  transition:
    transform var(--transition-base),
    background var(--transition-fast),
    border-color var(--transition-base);
}

.risk-item:hover {
  transform: translateX(3px);
  border-color: rgba(6, 182, 212, 0.24);
}

.risk-item.risk-low {
  background: var(--color-success-dim);
}
.risk-item.risk-medium {
  background: var(--color-warning-dim);
}
.risk-item.risk-high {
  background: rgba(239, 68, 68, 0.12);
}
.risk-item.risk-critical {
  background: rgba(239, 68, 68, 0.18);
}

.risk-icon {
  font-size: 18px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.risk-low .risk-icon { color: var(--color-success); }
.risk-medium .risk-icon { color: var(--color-warning); }
.risk-high .risk-icon { color: var(--color-danger); }
.risk-critical .risk-icon { color: var(--color-danger); }

.risk-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.risk-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-display);
}

.risk-value {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

/* ---- 智能建议 ---- */
.suggest-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-element);
}

.suggest-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-element);
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: var(--radius-button);
  transition:
    transform var(--transition-base),
    background var(--transition-fast),
    border-color var(--transition-base);
}

.suggest-item:hover {
  transform: translateX(3px);
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.22);
}

.suggest-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 1px;
}

.suggest-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suggest-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-display);
}

.suggest-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.ai-disclaimer {
  margin-top: 12px;
  font-size: 11px;
  color: var(--text-disabled);
  text-align: right;
  font-style: italic;
}

/* ---- 本周环境周报 ---- */
.report-section {
  padding-bottom: var(--spacing-card);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-module);
}

.report-header .section-title {
  margin-bottom: 0;
}

.export-btn {
  font-size: 13px;
}

.weekly-chart {
  width: 100%;
  height: 300px;
}

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .alert-suggest-row {
    grid-template-columns: 1fr;
  }

  .gauge-chart {
    width: 220px;
    height: 180px;
  }

  .weekly-chart {
    height: 250px;
  }
}
</style>
