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
import { showInfoToast } from '@/utils/alert'

defineOptions({ name: 'AiAnalysisPage' })

// ---------- Store ----------
const deviceStore = useDeviceStore()

// ---------- 模拟评分数据 ----------
const mockScore = 85

const scoreComment = computed(() => {
  if (mockScore >= 90) return '当前室内环境整体优秀，各项指标均处于最佳范围，非常适合工作与休息。'
  if (mockScore >= 70) return '当前室内环境整体舒适，空气质量极佳。'
  if (mockScore >= 40) return '当前室内环境一般，部分指标需要关注，建议适当调整。'
  return '当前室内环境较差，多项指标超标，请尽快改善通风和温控。'
})

const scoreRating = computed(() => {
  if (mockScore >= 90) return '优秀'
  if (mockScore >= 70) return '良好'
  if (mockScore >= 40) return '一般'
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

// ---------- 智能建议（模拟数据） ----------
const suggestions = ref([
  { icon: '\uD83D\uDCA1', title: '光照偏低 (500lx)', desc: '建议打开主灯或拉开窗帘' },
  { icon: '\uD83C\uDF2C\uFE0F', title: 'CO2 浓度上升中 (450ppm)', desc: '建议适当开窗通风 15 分钟' },
  { icon: '\uD83D\uDC55', title: '温度适宜 (25.6\u2103)', desc: '建议穿着轻薄长袖' },
  { icon: '\uD83D\uDCA7', title: '湿度偏高 (68%)', desc: '建议开启除湿功能' },
])

// ---------- 尝试从 store 获取传感器数据 ----------
async function fetchSensorData() {
  const deviceId = deviceStore.selectedDeviceId
  if (!deviceId) return
  try {
    const res = await getLatestData(deviceId)
    const data = res.data
    if (data) {
      moldRisk.value = data.mold_risk ?? 0
      gasValue.value = data.gas ?? 0
    }
  } catch {
    // 使用模拟数据兜底
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
  const color = getScoreColor(mockScore)
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
            value: mockScore,
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
      data: weekDays,
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
        data: mockWeeklyData.temperature,
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
        data: mockWeeklyData.humidity,
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
        data: mockWeeklyData.aqi,
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
  background: var(--bg-card);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: var(--border-default);
  border-radius: var(--radius-card);
  padding: var(--spacing-card);
}

.section-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-module);
  letter-spacing: 0.5px;
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
}

.panel {
  background: var(--bg-card);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: var(--border-default);
  border-radius: var(--radius-card);
  padding: var(--spacing-card);
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
  transition: background var(--transition-fast);
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
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-button);
  transition: background var(--transition-fast);
}

.suggest-item:hover {
  background: rgba(255, 255, 255, 0.04);
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
