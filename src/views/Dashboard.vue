<!-- Dashboard.vue -->
<!-- 控制台首页 -->
<!-- 设备概览卡片组 + 实时数据面板/快捷控制 + ECharts 趋势图 -->
<template>
  <div class="dashboard-page">
    <!-- 燃气告警横幅 -->
    <GasAlertBanner
      :visible="sensorData.gas > 0"
      :device-name="selectedDevice?.device_name || '未知设备'"
      :device-id="selectedDeviceId"
      @view-detail="goToControl"
    />

    <!-- ====== 第一区域：设备概览卡片组 ====== -->
    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">我的设备</h2>
      </div>
      <div class="device-cards-scroll">
        <DeviceOverviewCard
          v-for="device in deviceStore.devices"
          :key="device.device_id"
          :device="device"
          :temperature="getDeviceTemp(device.device_id)"
          :humidity="getDeviceHumidity(device.device_id)"
          @click="handleDeviceClick"
        />
        <!-- + 添加设备按钮卡片 -->
        <div class="add-device-card" @click="showBindDialog = true">
          <div class="add-device-card__icon">+</div>
          <div class="add-device-card__text">添加设备</div>
        </div>
      </div>
    </section>

    <!-- ====== 第二区域：左右两栏 ====== -->
    <section class="dashboard-section dashboard-two-col">
      <!-- 左栏：实时数据面板（60%） -->
      <div class="dashboard-col dashboard-col--left">
        <div class="section-header">
          <h2 class="section-title">实时数据</h2>
          <span v-if="selectedDevice" class="section-subtitle">
            {{ selectedDevice.device_name }}
          </span>
        </div>

        <!-- 3 个主指标卡：温度、湿度、AQI -->
        <div class="sensor-cards-grid">
          <SensorCard
            title="温度"
            :value="sensorData.temperature"
            unit="℃"
            icon="🌡"
            :status="getTemperatureStatus(sensorData.temperature)"
            :trend-data="trendData.temperature"
            color="#EF4444"
          />
          <SensorCard
            title="湿度"
            :value="sensorData.humidity"
            unit="%RH"
            icon="💧"
            :status="getHumidityStatus(sensorData.humidity)"
            :trend-data="trendData.humidity"
            color="#3B82F6"
          />
          <SensorCard
            title="AQI"
            :value="sensorData.aqi"
            unit=""
            icon="🌫"
            :status="getAqiStatus(sensorData.aqi)"
            :trend-data="trendData.aqi"
            color="#10B981"
          />
        </div>

        <!-- 3 个次指标卡：TVOC、eCO2、霉菌风险 -->
        <div class="sensor-mini-cards-grid">
          <SensorMiniCard
            label="TVOC"
            :value="sensorData.tvoc"
            unit="ppb"
            :status="getTvocStatus(sensorData.tvoc)"
          />
          <SensorMiniCard
            label="eCO2"
            :value="sensorData.eco2"
            unit="ppm"
            :status="getEco2Status(sensorData.eco2)"
          />
          <SensorMiniCard
            label="霉菌风险"
            :value="moldRiskText"
            unit=""
            :status="getMoldRiskStatus(sensorData.mold_risk)"
          />
        </div>
      </div>

      <!-- 右栏：快捷控制 & 告警（40%） -->
      <div class="dashboard-col dashboard-col--right">
        <!-- 快捷控制面板 -->
        <div class="panel">
          <div class="section-header">
            <h2 class="section-title">快捷控制</h2>
          </div>
          <div class="control-list">
            <ControlToggle
              v-model="controlState.light"
              label="灯光"
              :disabled="!selectedDevice || selectedDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('light', val)"
            />
            <ControlToggle
              v-model="controlState.buzzer"
              label="蜂鸣器"
              :disabled="!selectedDevice || selectedDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('buzzer', val)"
            />
            <ControlToggle
              v-model="controlState.focus"
              label="专注模式"
              :disabled="!selectedDevice || selectedDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('focus', val)"
            />
          </div>
        </div>

        <!-- 最近告警列表 -->
        <div class="panel">
          <div class="section-header">
            <h2 class="section-title">最近告警</h2>
          </div>
          <div class="alert-list">
            <div
              v-for="(alert, index) in alertList"
              :key="index"
              class="alert-item"
              :class="`alert-item--${alert.level}`"
            >
              <span class="alert-item__icon">{{ alert.icon }}</span>
              <div class="alert-item__content">
                <span class="alert-item__desc">{{ alert.description }}</span>
                <span class="alert-item__time">{{ alert.time }}</span>
              </div>
            </div>
            <div v-if="alertList.length === 0" class="alert-empty">暂无告警</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 第三区域：ECharts 趋势图（跨全宽） ====== -->
    <section class="dashboard-section">
      <div class="section-header">
        <h2 class="section-title">趋势图</h2>
        <div class="time-range-buttons">
          <button
            v-for="range in timeRanges"
            :key="range.key"
            class="time-range-btn"
            :class="{ 'time-range-btn--active': activeTimeRange === range.key }"
            @click="switchTimeRange(range.key)"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
      <div class="chart-wrapper">
        <div ref="chartRef" class="chart-container"></div>
      </div>
    </section>

    <!-- ====== 绑定设备对话框 ====== -->
    <el-dialog
      v-model="showBindDialog"
      title="绑定设备"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="bindForm" label-width="80px">
        <el-form-item label="设备ID">
          <el-input v-model="bindForm.device_id" placeholder="请输入设备ID" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="bindForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" :loading="bindLoading" @click="handleBindDevice">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import DeviceOverviewCard from '@/components/DeviceOverviewCard.vue'
import SensorCard from '@/components/SensorCard.vue'
import SensorMiniCard from '@/components/SensorMiniCard.vue'
import ControlToggle from '@/components/ControlToggle.vue'
import GasAlertBanner from '@/components/GasAlertBanner.vue'
import { getDeviceList, bindDevice, getLatestData, sendControlCommand } from '@/api/device'
import { useWebSocket } from '@/composables/useWebSocket'
import { useDeviceStore } from '@/store/device'
import { isDemoMode } from '@/utils/demo'

defineOptions({ name: 'DashboardPage' })

const router = useRouter()
const deviceStore = useDeviceStore()

// ============================================================
// 状态定义
// ============================================================

const showBindDialog = ref(false)
const bindLoading = ref(false)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const selectedDeviceId = ref('')
const demoMode = ref(isDemoMode())

// 绑定设备表单
const bindForm = reactive({
  device_id: '',
  device_name: '',
})

// 传感器实时数据
const sensorData = reactive({
  temperature: 0,
  humidity: 0,
  illuminance: 0,
  aqi: 0,
  tvoc: 0,
  eco2: 0,
  mold_risk: 0,
  gas: 0,
  wifi_rssi: 0,
  timestamp: '',
})

// 迷你趋势线数据：最近 20 个数据点
const trendData = reactive({
  temperature: [] as number[],
  humidity: [] as number[],
  aqi: [] as number[],
})

// 快捷控制状态
const controlState = reactive({
  light: false,
  buzzer: false,
  focus: false,
})

// 时间范围配置
const timeRanges = [
  { key: '1H', label: '1H' },
  { key: '6H', label: '6H' },
  { key: '24H', label: '24H' },
  { key: '7D', label: '7D' },
]
const activeTimeRange = ref('1H')

// ECharts 趋势数据
const chartTimeData = ref<string[]>([])
const chartTempData = ref<number[]>([])
const chartHumidityData = ref<number[]>([])

// 设备温湿度缓存（用于设备概览卡片显示）
const deviceDataCache = reactive<
  Record<string, { temperature: number | null; humidity: number | null }>
>({})

// ============================================================
// 计算属性
// ============================================================

const selectedDevice = computed(() => {
  return deviceStore.devices.find((d) => d.device_id === selectedDeviceId.value)
})

const moldRiskText = computed(() => {
  const map: Record<number, string> = { 0: '低', 1: '中', 2: '高', 3: '极高' }
  return map[sensorData.mold_risk] || '低'
})

// 告警列表：根据传感器数据生成
const alertList = computed(() => {
  const alerts: Array<{
    icon: string
    description: string
    time: string
    level: 'danger' | 'warning' | 'info'
  }> = []

  if (sensorData.gas > 0) {
    alerts.push({
      icon: '🔥',
      description: '检测到燃气泄漏，请立即处理！',
      time: formatRelativeTime(),
      level: 'danger',
    })
  }
  if (sensorData.temperature > 28) {
    alerts.push({
      icon: '🌡',
      description: `温度偏高：${sensorData.temperature}℃`,
      time: formatRelativeTime(),
      level: 'warning',
    })
  }
  if (sensorData.aqi > 100) {
    alerts.push({
      icon: '🌫',
      description: `空气质量差：AQI ${sensorData.aqi}`,
      time: formatRelativeTime(),
      level: 'warning',
    })
  }
  if (sensorData.eco2 > 800) {
    alerts.push({
      icon: '💨',
      description: `CO2浓度偏高：${sensorData.eco2}ppm`,
      time: formatRelativeTime(),
      level: 'warning',
    })
  }

  return alerts.slice(0, 5)
})

// ============================================================
// 辅助函数
// ============================================================

function formatRelativeTime(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function getDeviceTemp(deviceId: string): number | null {
  return deviceDataCache[deviceId]?.temperature ?? null
}

function getDeviceHumidity(deviceId: string): number | null {
  return deviceDataCache[deviceId]?.humidity ?? null
}

// 传感器状态判断
function getTemperatureStatus(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 30) return 'danger'
  if (val > 28) return 'warning'
  return 'normal'
}

function getHumidityStatus(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 80) return 'danger'
  if (val > 70) return 'warning'
  return 'normal'
}

function getAqiStatus(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 150) return 'danger'
  if (val > 100) return 'warning'
  return 'normal'
}

function getTvocStatus(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 300) return 'danger'
  if (val > 200) return 'warning'
  return 'normal'
}

function getEco2Status(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 1000) return 'danger'
  if (val > 800) return 'warning'
  return 'normal'
}

function getMoldRiskStatus(val: number): 'normal' | 'warning' | 'danger' {
  if (val >= 3) return 'danger'
  if (val >= 2) return 'warning'
  return 'normal'
}

// ============================================================
// 数据获取
// ============================================================

async function fetchDevices() {
  try {
    const list = await getDeviceList()
    deviceStore.setDevices(list)

    // 默认选中第一个在线设备
    if (!selectedDeviceId.value && list.length > 0) {
      const firstOnline = list.find((d) => d.status === 'online')
      const target = firstOnline || list[0]
      if (target) {
        selectedDeviceId.value = target.device_id
        fetchLatestData(target.device_id)
      }
    }
  } catch {
    ElMessage.error('获取设备列表失败')
  }
}

async function fetchLatestData(deviceId: string) {
  try {
    const data = await getLatestData(deviceId)
    if (data) {
      Object.assign(sensorData, data)

      // 更新设备数据缓存
      if (!deviceDataCache[deviceId]) {
        deviceDataCache[deviceId] = { temperature: null, humidity: null }
      }
      deviceDataCache[deviceId].temperature = data.temperature
      deviceDataCache[deviceId].humidity = data.humidity

      // 更新趋势数据
      pushTrendData()
      // 更新图表
      updateChart()
    }
  } catch {
    // 设备可能无数据，忽略
  }
}

// ============================================================
// 趋势数据维护（最近 20 个数据点）
// ============================================================

function pushTrendData() {
  const maxLen = 20
  trendData.temperature.push(sensorData.temperature)
  trendData.humidity.push(sensorData.humidity)
  trendData.aqi.push(sensorData.aqi)

  if (trendData.temperature.length > maxLen) trendData.temperature.shift()
  if (trendData.humidity.length > maxLen) trendData.humidity.shift()
  if (trendData.aqi.length > maxLen) trendData.aqi.shift()
}

// ============================================================
// ECharts 趋势图
// ============================================================

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: 'rgba(51, 65, 102, 0.45)',
      textStyle: { color: '#e8ecf4' },
    },
    legend: {
      data: ['温度', '湿度'],
      textStyle: { color: '#8b95b0' },
      top: 0,
      right: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
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
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(51, 65, 102, 0.45)' } },
      axisLabel: { color: '#8b95b0' },
      splitLine: { lineStyle: { color: 'rgba(51, 65, 102, 0.25)' } },
    },
    series: [
      {
        name: '温度',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#EF4444', width: 2 },
        itemStyle: { color: '#EF4444' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(239, 68, 68, 0.25)' },
            { offset: 1, color: 'rgba(239, 68, 68, 0.02)' },
          ]),
        },
        animationDuration: 800,
      },
      {
        name: '湿度',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#3B82F6', width: 2 },
        itemStyle: { color: '#3B82F6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.25)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.02)' },
          ]),
        },
        animationDuration: 800,
      },
    ],
  }

  chart.setOption(option)
}

function updateChart() {
  if (!chart) return
  const now = new Date()
  const timeStr = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  chartTimeData.value.push(timeStr)
  chartTempData.value.push(sensorData.temperature)
  chartHumidityData.value.push(sensorData.humidity)

  // 最多保留 60 个数据点
  const maxPoints = 60
  if (chartTimeData.value.length > maxPoints) {
    chartTimeData.value.shift()
    chartTempData.value.shift()
    chartHumidityData.value.shift()
  }

  chart.setOption({
    xAxis: { data: chartTimeData.value },
    series: [{ data: chartTempData.value }, { data: chartHumidityData.value }],
  })
}

function switchTimeRange(range: string) {
  activeTimeRange.value = range
  // 清空图表数据，重新拉取（简化实现：清空后等待新数据填充）
  chartTimeData.value = []
  chartTempData.value = []
  chartHumidityData.value = []
  if (chart) {
    chart.setOption({
      xAxis: { data: [] },
      series: [{ data: [] }, { data: [] }],
    })
  }
}

// ============================================================
// 事件处理
// ============================================================

function handleDeviceClick(device: { device_id: string }) {
  selectedDeviceId.value = device.device_id
  fetchLatestData(device.device_id)
}

function goToControl(deviceId: string) {
  const query: Record<string, string> = { deviceId }
  if (demoMode.value) {
    query.demo = 'true'
  }
  router.push({ path: '/control', query })
}

async function handleControl(command: string, value: boolean) {
  if (!selectedDeviceId.value) return
  try {
    await sendControlCommand(selectedDeviceId.value, {
      command,
      value: value ? 'on' : 'off',
    })
    ElMessage.success(
      `${command === 'light' ? '灯光' : command === 'buzzer' ? '蜂鸣器' : '专注模式'}已${value ? '开启' : '关闭'}`,
    )
  } catch {
    ElMessage.error('控制指令发送失败')
    // 恢复开关状态
    if (command === 'light') controlState.light = !value
    if (command === 'buzzer') controlState.buzzer = !value
    if (command === 'focus') controlState.focus = !value
  }
}

async function handleBindDevice() {
  if (!bindForm.device_id) {
    ElMessage.warning('请输入设备ID')
    return
  }
  bindLoading.value = true
  try {
    await bindDevice({
      device_id: bindForm.device_id,
      device_name: bindForm.device_name || '未命名设备',
    })
    ElMessage.success('绑定成功')
    showBindDialog.value = false
    bindForm.device_id = ''
    bindForm.device_name = ''
    fetchDevices()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg = error.response?.data?.detail || error.response?.data?.message || '绑定失败'
    ElMessage.error(msg)
  } finally {
    bindLoading.value = false
  }
}

// ============================================================
// WebSocket 连接
// ============================================================

const ws = useWebSocket('/ws')

// ============================================================
// 生命周期
// ============================================================

watch(selectedDeviceId, (newId) => {
  if (newId) {
    fetchLatestData(newId)
  }
})

onMounted(() => {
  fetchDevices()
  nextTick(() => {
    initChart()
  })

  // 建立 WebSocket 连接
  ws.connect()

  // 订阅传感器数据推送
  ws.on('sensor_data', (data: Record<string, unknown>) => {
    const deviceId = data.device_id as string
    if (deviceId === selectedDeviceId.value) {
      Object.assign(sensorData, data)
      pushTrendData()
      updateChart()
    }

    // 更新设备数据缓存（无论是否选中）
    if (!deviceDataCache[deviceId]) {
      deviceDataCache[deviceId] = { temperature: null, humidity: null }
    }
    deviceDataCache[deviceId].temperature = (data.temperature as number) ?? null
    deviceDataCache[deviceId].humidity = (data.humidity as number) ?? null
  })

  // 订阅设备状态变更
  ws.on('device_status', () => {
    fetchDevices()
  })
})

onUnmounted(() => {
  ws.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
/* ============================================================
   页面容器
   ============================================================ */
.dashboard-page {
  padding: 4px;
  min-height: 100vh;
  background: transparent;
}

/* ============================================================
   通用区块
   ============================================================ */
.dashboard-section {
  margin-bottom: 26px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-family: var(--font-display, 'Plus Jakarta Sans', sans-serif);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: var(--radius-full, 9999px);
  background: linear-gradient(180deg, var(--color-cube-primary, #06b6d4), var(--color-cube-accent, #a3e635));
  box-shadow: 0 0 14px rgba(6, 182, 212, 0.45);
}

.section-subtitle {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary, #8b95b0);
  margin-left: 12px;
}

/* ============================================================
   第一区域：设备概览卡片组（横向滚动）
   ============================================================ */
.device-cards-scroll {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 2px 2px 12px;
  scrollbar-width: thin;
  scrollbar-color: rgba(6, 182, 212, 0.32) transparent;
}

.device-cards-scroll::-webkit-scrollbar {
  height: 6px;
}

.device-cards-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.device-cards-scroll::-webkit-scrollbar-thumb {
  background: linear-gradient(90deg, rgba(6, 182, 212, 0.42), rgba(163, 230, 53, 0.28));
  border-radius: 3px;
}

/* 设备概览卡片最小宽度 */
.device-cards-scroll :deep(.device-overview-card) {
  min-width: 180px;
  max-width: 220px;
  flex-shrink: 0;
}

/* + 添加设备按钮卡片 */
.add-device-card {
  min-width: 180px;
  max-width: 220px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.048), rgba(255, 255, 255, 0.01)),
    rgba(12, 18, 25, 0.58);
  border: 1px dashed rgba(163, 230, 53, 0.34);
  border-radius: var(--radius-card, var(--radius-md, 12px));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 14px;
  cursor: pointer;
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.add-device-card::before {
  content: '';
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: calc(var(--radius-card, 12px) - 4px);
  pointer-events: none;
}

.add-device-card:hover {
  border-color: rgba(163, 230, 53, 0.62);
  background: rgba(163, 230, 53, 0.055);
  transform: translateY(-5px);
  box-shadow: 0 0 24px rgba(163, 230, 53, 0.12), var(--shadow-card, 0 4px 12px rgba(0, 0, 0, 0.35));
}

.add-device-card__icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(163, 230, 53, 0.08);
  border: 1px solid rgba(163, 230, 53, 0.22);
  font-size: 28px;
  font-weight: 300;
  color: var(--color-cube-accent, #a3e635);
  line-height: 1;
  position: relative;
  z-index: 1;
}

.add-device-card__text {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary, #8b95b0);
  position: relative;
  z-index: 1;
}

/* ============================================================
   第二区域：左右两栏布局
   ============================================================ */
.dashboard-two-col {
  display: flex;
  gap: 24px;
}

.dashboard-col--left {
  flex: 0 0 60%;
  min-width: 0;
}

.dashboard-col--right {
  flex: 0 0 calc(40% - 24px);
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ============================================================
   传感器卡片网格（主指标 3 列）
   ============================================================ */
.sensor-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

/* ============================================================
   传感器迷你卡片网格（次指标 3 列）
   ============================================================ */
.sensor-mini-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

/* ============================================================
   右栏面板
   ============================================================ */
.panel {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.012)),
    var(--bg-card, rgba(15, 23, 42, 0.65));
  border: var(--border-glass, 1px solid rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 16px;
  box-shadow: var(--shadow-card, 0 4px 12px rgba(0, 0, 0, 0.35));
}

.panel::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-cube-primary, #06b6d4), transparent);
  opacity: 0.55;
}

.control-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ============================================================
   告警列表
   ============================================================ */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm, 8px);
  background: rgba(12, 18, 25, 0.56);
  border: 1px solid rgba(255, 255, 255, 0.065);
  transition:
    transform var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.alert-item:hover {
  transform: translateX(3px);
  border-color: rgba(6, 182, 212, 0.24);
  background: rgba(6, 182, 212, 0.06);
}

.alert-item--danger {
  background: rgba(220, 38, 38, 0.15);
  border-color: rgba(220, 38, 38, 0.4);
}

.alert-item--warning {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.3);
}

.alert-item__icon {
  font-size: 16px;
  flex-shrink: 0;
}

.alert-item__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alert-item__desc {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-item__time {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 11px;
  color: var(--text-secondary, #8b95b0);
}

.alert-empty {
  text-align: center;
  padding: 20px;
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary, #8b95b0);
}

/* ============================================================
   第三区域：趋势图
   ============================================================ */
.chart-wrapper {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.01)),
    var(--bg-card, rgba(15, 23, 42, 0.65));
  border: var(--border-glass, 1px solid rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 16px;
  box-shadow: var(--shadow-card, 0 4px 12px rgba(0, 0, 0, 0.35));
}

.chart-wrapper::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-primary, #06b6d4), var(--color-info, #3b82f6), var(--color-cube-accent, #a3e635));
  background-size: 200% 100%;
  animation: border-flow 5s linear infinite;
  opacity: 0.74;
}

.chart-container {
  height: 320px;
  width: 100%;
}

/* 时间范围切换按钮 */
.time-range-buttons {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}

.time-range-btn {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  font-weight: 500;
  min-width: 48px;
  padding: 5px 12px;
  border-radius: 7px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary, #8b95b0);
  cursor: pointer;
  transition: all var(--transition-fast, 150ms);
}

.time-range-btn:hover {
  border-color: rgba(6, 182, 212, 0.24);
  color: var(--text-primary, var(--text-main, #e8ecf4));
}

.time-range-btn--active {
  background: linear-gradient(135deg, var(--color-cube-primary, #06b6d4), var(--color-cube-accent, #a3e635));
  border-color: rgba(255, 255, 255, 0.1);
  color: #060a18;
  font-weight: 600;
  box-shadow: 0 0 18px rgba(6, 182, 212, 0.2);
}

/* ============================================================
   响应式布局
   ============================================================ */
@media (max-width: 1024px) {
  .dashboard-two-col {
    flex-direction: column;
  }

  .dashboard-col--left,
  .dashboard-col--right {
    flex: 1 1 100%;
  }

  .sensor-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .sensor-mini-cards-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .dashboard-page {
    padding: 0;
  }

  .sensor-cards-grid {
    grid-template-columns: 1fr;
  }

  .sensor-mini-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
