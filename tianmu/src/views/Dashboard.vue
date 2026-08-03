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

    <section
      v-if="controlModeDevice"
      class="dashboard-control-mode"
      :class="{ 'dashboard-control-mode--revealed': controlContentVisible }"
    >
      <MineradioParticleStage
        class="dashboard-control-mode__particles"
        embedded
        variant="hero"
        :air-data="airParticleData"
        :density="0.18"
        :fps="24"
        :intensity="controlModeDevice.status === 'online' ? 0.36 : 0.18"
        :show-labels="false"
      />

      <button class="dashboard-control-back" title="返回控制台" @click="leaveInlineControl">
        <span class="dashboard-control-back__arrow">‹</span>
        <span>控制台</span>
      </button>

      <header class="dashboard-control-titlebar">
        <div>
          <span class="dashboard-control-titlebar__eyebrow">数字孪生控制面板</span>
          <h2>{{ controlModeDevice.device_name }}</h2>
          <small>{{ controlModeDevice.device_id }}</small>
        </div>
        <div class="dashboard-control-titlebar__status">
          <span :class="['dashboard-control-titlebar__dot', controlModeDevice.status === 'online' ? 'is-online' : 'is-offline']"></span>
          {{ controlModeDevice.status === 'online' ? '在线同步' : '离线占位' }}
        </div>
      </header>

      <main class="dashboard-control-stage">
        <aside class="dashboard-control-panel dashboard-control-panel--legend">
          <div class="dashboard-control-panel__header">
            <span>空气成分</span>
            <small>轻量粒子层</small>
          </div>
          <div class="dashboard-air-legend">
            <div v-for="item in airLegend" :key="item.label" class="dashboard-air-legend__item">
              <span class="dashboard-air-legend__dot" :style="{ background: item.color }"></span>
              <strong>{{ item.label }}</strong>
              <span>{{ item.name }}</span>
            </div>
          </div>
        </aside>

        <div class="dashboard-control-twin">
          <div class="dashboard-control-twin__halo"></div>
          <div
            class="dashboard-control-twin__model control-twin-lite"
            :class="{
              'dashboard-control-twin__model--flight-hidden': twinFlightActive,
              'control-twin-lite--offline': controlModeDevice.status !== 'online',
            }"
            :aria-label="controlModeDevice.device_name"
          >
            <div class="control-twin-lite__glow" aria-hidden="true"></div>
            <div class="control-twin-lite__visual">
              <img class="control-twin-lite__image" src="/smart-cube-transparent.png" alt="智能桌面魔方模型预览" />
              <div class="control-twin-lite__screen" aria-label="魔方屏幕实时数据">
                <HardwareTwinScreen :data="sensorData" :online="controlModeDevice.status === 'online'" :focus="controlState.focus" />
              </div>
            </div>
            <div class="control-twin-lite__label">
              <span>{{ controlModeDevice.device_name }}</span>
              <small>{{ controlModeDevice.status === 'online' ? 'LIGHTWEIGHT TWIN' : 'OFFLINE' }}</small>
            </div>
          </div>
        </div>

        <aside class="dashboard-control-panel dashboard-control-panel--actions">
          <div class="dashboard-control-panel__header">
            <span>设备控制</span>
            <small>{{ controlModeDevice.status === 'online' ? '可操作' : '已置灰' }}</small>
          </div>
          <div class="dashboard-control-actions" :class="{ 'dashboard-control-actions--disabled': controlModeDevice.status !== 'online' }">
            <ControlToggle
              v-model="controlState.light"
              label="灯光"
              :disabled="controlModeDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('light', val)"
            />
            <ControlToggle
              v-model="controlState.wechatNotify"
              label="微信通知"
              :disabled="controlModeDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('wechat_notify', val)"
            />
            <ControlToggle
              v-model="controlState.focus"
              label="专注模式"
              :disabled="controlModeDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('focus_mode', val)"
            />
            <div class="dashboard-control-metrics">
              <div>
                <span>温度</span>
                <strong>{{ sensorData.temperature || '--' }}℃</strong>
              </div>
              <div>
                <span>湿度</span>
                <strong>{{ sensorData.humidity || '--' }}%</strong>
              </div>
              <div>
                <span>AQI</span>
                <strong>{{ sensorData.aqi || '--' }}</strong>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </section>

    <template v-else>
    <section class="dashboard-hero">
      <MineradioParticleStage
        class="dashboard-hero__particles"
        embedded
        variant="hero"
        :air-data="airParticleData"
        :density="0.52"
        :intensity="heroParticleIntensity"
      />
      <div class="dashboard-hero__copy">
        <div class="dashboard-hero__mark">
          <span class="dashboard-hero__cube"></span>
          <span>Smart Desktop Cube</span>
        </div>
        <h1 class="dashboard-hero__title">智能桌面魔方</h1>
        <p class="dashboard-hero__desc">
          {{ heroSummary }}
        </p>
        <div class="dashboard-hero__stats">
          <div class="dashboard-hero__stat">
            <strong>{{ onlineDeviceCount }}</strong>
            <span>在线设备</span>
          </div>
          <div class="dashboard-hero__stat">
            <strong>{{ selectedDevice?.status === 'online' ? 'ONLINE' : 'IDLE' }}</strong>
            <span>{{ selectedDevice?.device_name || '等待设备' }}</span>
          </div>
          <div class="dashboard-hero__stat">
            <strong>{{ alertList.length }}</strong>
            <span>当前提醒</span>
          </div>
        </div>
      </div>
      <MascotCompanion
        class="dashboard-hero__mascot"
        :state="mascotState"
        title="小眠"
        :message="mascotMessage"
        :metrics="mascotMetrics"
      />
    </section>

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
          :launching="launchingDeviceId === device.device_id"
          :muted="Boolean(launchingDeviceId && launchingDeviceId !== device.device_id)"
          :transition-name="!controlModeDeviceId && selectedDeviceId === device.device_id ? 'active-twin' : undefined"
          :twin-hidden="twinFlightActive && selectedDeviceId === device.device_id"
          :refreshing="refreshingDeviceId === device.device_id"
          @click="handleDeviceClick"
          @refresh-data="handleDeviceDataRefresh"
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

        <!-- 主指标卡：温度、湿度、AQI、PM2.5 -->
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
          <SensorCard
            title="PM2.5"
            :value="formatPm25(sensorData.pm25)"
            unit="μg/m³"
            icon="•"
            :status="getPm25Status(sensorData.pm25)"
            :trend-data="trendData.pm25"
            color="#94A3B8"
          />
        </div>
        <p class="pm25-reference-note">
          PM2.5 为机器学习估算值，仅供参考，不代表 100% 精确检测结果。
        </p>

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
              v-model="controlState.wechatNotify"
              label="微信通知"
              :disabled="!selectedDevice || selectedDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('wechat_notify', val)"
            />
            <ControlToggle
              v-model="controlState.focus"
              label="专注模式"
              :disabled="!selectedDevice || selectedDevice.status !== 'online'"
              @update:model-value="(val: boolean) => handleControl('focus_mode', val)"
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
    </template>

    <div
      v-if="twinFlightVisible"
      ref="twinFlightRef"
      class="dashboard-twin-flight"
      :class="{
        'dashboard-twin-flight--playing': twinFlightPlaying,
        'dashboard-twin-flight--return': twinFlightDirection === 'return',
      }"
      :style="twinFlightStyle"
      aria-hidden="true"
    >
      <CubeSpinGifPreview
        :label="twinFlightLabel"
        :offline="twinFlightOffline"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, defineAsyncComponent, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import DeviceOverviewCard from '@/components/DeviceOverviewCard.vue'
import SensorCard from '@/components/SensorCard.vue'
import SensorMiniCard from '@/components/SensorMiniCard.vue'
import ControlToggle from '@/components/ControlToggle.vue'
import GasAlertBanner from '@/components/GasAlertBanner.vue'
import { getDeviceList, bindDevice, getLatestData, sendControlCommand, type SensorData } from '@/api/device'
import { useWebSocket } from '@/composables/useWebSocket'
import { useDashboardTrendChart } from '@/composables/useDashboardTrendChart'
import { useDashboardTwinTransition } from '@/composables/useDashboardTwinTransition'
import { useDeviceStore } from '@/stores/device'
import { BEIJING_TIME_ZONE } from '@/utils/format'
import {
  formatPm25,
  getAqiStatus,
  getEco2Status,
  getHumidityStatus,
  getMoldRiskStatus,
  getPm25Status,
  getTemperatureStatus,
  getTvocStatus,
} from '@/utils/sensorStatus'

const MascotCompanion = defineAsyncComponent(() => import('@/components/brand/MascotCompanion.vue'))
const MineradioParticleStage = defineAsyncComponent(() => import('@/components/brand/MineradioParticleStage.vue'))
const CubeSpinGifPreview = defineAsyncComponent(() => import('@/components/brand/CubeSpinGifPreview.vue'))
const HardwareTwinScreen = defineAsyncComponent(() => import('@/components/brand/HardwareTwinScreen.vue'))

defineOptions({ name: 'DashboardPage' })

const deviceStore = useDeviceStore()

// ============================================================
// 状态定义
// ============================================================

const showBindDialog = ref(false)
const bindLoading = ref(false)

const selectedDeviceId = ref('')
const {
  chartRef,
  timeRanges,
  activeTimeRange,
  initChart,
  loadTrendData,
  switchTimeRange,
  disposeChart,
} = useDashboardTrendChart(selectedDeviceId)
const {
  twinFlightRef,
  twinFlightVisible,
  twinFlightActive,
  twinFlightPlaying,
  twinFlightDirection,
  twinFlightStyle,
  twinFlightLabel,
  twinFlightOffline,
  runSamePageTransition,
  prefersReducedMotion,
  readTwinRect,
  readDeviceTwinRect,
  prepareTwinFlight,
  animateTwinFlight,
  waitForPaintFrames,
  finishTwinFlight,
} = useDashboardTwinTransition()
const launchingDeviceId = ref('')
const returningDeviceId = ref('')
const controlModeDeviceId = ref('')
const refreshingDeviceId = ref('')
const controlContentVisible = ref(false)
let sensorPollingTimer = 0
let deviceCardPollingTimer = 0
let trendRefreshTimer = 0
let latestDataRequestId = 0
const subscribedDeviceIds = new Set<string>()
const latestTimestampByDevice = new Map<string, number>()

const airLegend = [
  { label: 'O2', name: '氧气', color: '#a3e635' },
  { label: 'CO2', name: '二氧化碳', color: '#60a5fa' },
  { label: 'H2O', name: '水汽', color: '#22d3ee' },
  { label: 'PM2.5', name: '细颗粒物', color: '#9ca3af' },
  { label: 'TVOC', name: '挥发物', color: '#fbbf24' },
  { label: 'CH2O', name: '甲醛', color: '#fb7185' },
]

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
  pm25: 0,
  tvoc: 0,
  eco2: 0,
  formaldehyde: 0,
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
  pm25: [] as number[],
})

// 快捷控制状态
const controlState = reactive({
  light: false,
  wechatNotify: false,
  focus: false,
})

function applyHardwareControlState(data: Partial<SensorData> | Record<string, unknown> | null | undefined) {
  if (!data) return
  if (typeof data.light === 'boolean') controlState.light = data.light
  if (typeof data.wechat_notify === 'boolean') controlState.wechatNotify = data.wechat_notify
  if (typeof data.focus_mode === 'boolean') controlState.focus = data.focus_mode
}

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

const controlModeDevice = computed(() => {
  return deviceStore.devices.find((d) => d.device_id === controlModeDeviceId.value)
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
      time: formatSensorTime(sensorData.timestamp),
      level: 'danger',
    })
  }
  if (sensorData.temperature > 28) {
    alerts.push({
      icon: '🌡',
      description: `温度偏高：${sensorData.temperature}℃`,
      time: formatSensorTime(sensorData.timestamp),
      level: 'warning',
    })
  }
  if (sensorData.aqi > 100) {
    alerts.push({
      icon: '🌫',
      description: `空气质量差：AQI ${sensorData.aqi}`,
      time: formatSensorTime(sensorData.timestamp),
      level: 'warning',
    })
  }
  if (sensorData.pm25 > 35) {
    alerts.push({
      icon: '•',
      description: `PM2.5 估算偏高：${formatPm25(sensorData.pm25)} μg/m³（仅供参考）`,
      time: formatSensorTime(sensorData.timestamp),
      level: sensorData.pm25 > 75 ? 'danger' : 'warning',
    })
  }
  if (sensorData.eco2 > 800) {
    alerts.push({
      icon: '💨',
      description: `CO2浓度偏高：${sensorData.eco2}ppm`,
      time: formatSensorTime(sensorData.timestamp),
      level: 'warning',
    })
  }

  return alerts.slice(0, 5)
})

const onlineDeviceCount = computed(
  () => deviceStore.devices.filter((device) => device.status === 'online').length,
)

const mascotState = computed<'normal' | 'focus' | 'celebrate' | 'remind'>(() => {
  if (alertList.value.length > 0) return 'remind'
  if (controlState.focus) return 'focus'
  if (
    selectedDevice.value?.status === 'online' &&
    sensorData.aqi <= 80 &&
    sensorData.temperature <= 28 &&
    sensorData.humidity <= 70
  ) {
    return 'celebrate'
  }
  return 'normal'
})

const mascotMessage = computed(() => {
  if (mascotState.value === 'remind')
    return alertList.value[0]?.description || '有几项指标值得留意一下。'
  if (mascotState.value === 'focus') return '专注模式已开启，小眠会帮你守住安静的环境。'
  if (mascotState.value === 'celebrate') return '空气质量和设备状态都很漂亮，适合继续保持。'
  return selectedDevice.value
    ? `${selectedDevice.value.device_name} 正在稳定运行。`
    : '绑定设备后，小眠会在这里陪你看护状态。'
})

const heroSummary = computed(() => {
  if (alertList.value.length > 0) return alertList.value[0]?.description || '当前环境需要留意。'
  if (selectedDevice.value)
    return `${selectedDevice.value.device_name} 已接入，实时感知温湿度、空气质量和设备状态。`
  return '连接你的桌面魔方后，实时环境状态会在这里汇聚成一眼可读的控制台。'
})

const heroParticleIntensity = computed(() => {
  if (alertList.value.length > 0) return 1.06
  if (controlState.focus) return 0.66
  return selectedDevice.value?.status === 'online' ? 0.88 : 0.62
})

const formatFixedMetric = (value: number, unit: string) => {
  if (!Number.isFinite(value) || value === 0) return `--${unit}`
  return `${value.toFixed(1)}${unit}`
}

const mascotMetrics = computed(() => [
  { label: '温度', value: formatFixedMetric(sensorData.temperature, '℃') },
  { label: '湿度', value: formatFixedMetric(sensorData.humidity, '%') },
  { label: 'AQI', value: sensorData.aqi || '--' },
])

const airParticleData = computed(() => ({
  aqi: sensorData.aqi,
  eco2: sensorData.eco2,
  formaldehyde: sensorData.formaldehyde,
  humidity: sensorData.humidity,
  pm25: sensorData.pm25,
  tvoc: sensorData.tvoc,
}))

// ============================================================
// 辅助函数
// ============================================================

function formatSensorTime(timestamp?: string): string {
  const date = timestamp ? new Date(timestamp) : null
  if (!date || Number.isNaN(date.getTime())) return '--:--'
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  })
}

function getDeviceTemp(deviceId: string): number | null {
  return deviceDataCache[deviceId]?.temperature ?? null
}

function getDeviceHumidity(deviceId: string): number | null {
  return deviceDataCache[deviceId]?.humidity ?? null
}

// ============================================================
// 数据获取
// ============================================================

async function fetchDevices() {
  try {
    const list = await getDeviceList()
    deviceStore.setDevices(list)
    subscribeDevices(list)

    // 默认选中第一个在线设备
    if (!selectedDeviceId.value && list.length > 0) {
      const firstOnline = list.find((d) => d.status === 'online')
      const target = firstOnline || list[0]
      if (target) {
        selectedDeviceId.value = target.device_id
        deviceStore.selectDevice(target.device_id)
        fetchLatestData(target.device_id)
      }
    }
    fetchDeviceCardData(list)
  } catch {
    ElMessage.error('获取设备列表失败')
  }
}

function subscribeDevices(devices = deviceStore.devices) {
  devices.forEach((device) => {
    if (device.device_id && !subscribedDeviceIds.has(device.device_id)) {
      subscribedDeviceIds.add(device.device_id)
      ws.send('subscribe', { device_id: device.device_id })
    }
  })
}

async function fetchDeviceCardData(devices = deviceStore.devices) {
  const onlineDevices = devices.filter((device) => (
    device.status === 'online' &&
    device.device_id &&
    device.device_id !== selectedDeviceId.value
  ))

  await Promise.all(onlineDevices.map(async (device) => {
    try {
      const data = await getLatestData(device.device_id)
      if (!data) return
      const timestamp = data.timestamp ? new Date(data.timestamp).getTime() : Date.now()
      const latestTimestamp = latestTimestampByDevice.get(device.device_id) ?? 0
      if (Number.isFinite(timestamp) && timestamp < latestTimestamp) return
      latestTimestampByDevice.set(device.device_id, timestamp)
      const cachedData = deviceDataCache[device.device_id] ?? (
        deviceDataCache[device.device_id] = { temperature: null, humidity: null }
      )
      cachedData.temperature = data.temperature
      cachedData.humidity = data.humidity
    } catch {
      // 单个设备暂无数据时不影响其它设备卡片显示。
    }
  }))
}

async function fetchLatestData(deviceId: string, showError = false) {
  const requestId = ++latestDataRequestId
  try {
    const data = await getLatestData(deviceId)
    if (data && requestId === latestDataRequestId && deviceId === selectedDeviceId.value) {
      const timestamp = data.timestamp ? new Date(data.timestamp).getTime() : Date.now()
      const latestTimestamp = latestTimestampByDevice.get(deviceId) ?? 0
      if (Number.isFinite(timestamp) && timestamp < latestTimestamp) return false
      latestTimestampByDevice.set(deviceId, timestamp)
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined) Object.assign(sensorData, { [key]: value })
      })
      applyHardwareControlState(data)

      // 更新设备数据缓存
      if (!deviceDataCache[deviceId]) {
        deviceDataCache[deviceId] = { temperature: null, humidity: null }
      }
      deviceDataCache[deviceId].temperature = data.temperature
      deviceDataCache[deviceId].humidity = data.humidity

      // 更新趋势数据
      pushTrendData()
      return true
    }
    if (showError) ElMessage.warning('该设备暂无最新数据')
    return false
  } catch {
    if (showError) ElMessage.error('刷新设备数据失败')
    return false
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
  trendData.pm25.push(sensorData.pm25)

  if (trendData.temperature.length > maxLen) trendData.temperature.shift()
  if (trendData.humidity.length > maxLen) trendData.humidity.shift()
  if (trendData.aqi.length > maxLen) trendData.aqi.shift()
  if (trendData.pm25.length > maxLen) trendData.pm25.shift()
}

// ============================================================
// ECharts 趋势图
// ============================================================

// ============================================================
// 事件处理
// ============================================================

function setNavigationHighlight(path: string | null) {
  window.dispatchEvent(
    new CustomEvent('cube:navigation-highlight', {
      detail: { path },
    }),
  )
}

async function enterInlineControl(deviceId: string, startRect?: DOMRect) {
  const flightStartRect = startRect || readDeviceTwinRect(deviceId)
  const device = deviceStore.devices.find((item) => item.device_id === deviceId)
  selectedDeviceId.value = deviceId
  deviceStore.selectDevice(deviceId)
  setNavigationHighlight('/teen/control')
  fetchLatestData(deviceId)
  launchingDeviceId.value = deviceId
  controlContentVisible.value = false
  if (flightStartRect && !prefersReducedMotion()) {
    prepareTwinFlight(flightStartRect, device, 'enter')
  }

  const updateToControlMode = async () => {
    disposeChart()
    controlModeDeviceId.value = deviceId
    await nextTick()
  }
  const shouldUseTwinFlight = Boolean(flightStartRect && !prefersReducedMotion())
  const usedNativeTransition = shouldUseTwinFlight
    ? false
    : await runSamePageTransition(updateToControlMode)
  if (shouldUseTwinFlight) {
    await updateToControlMode()
  }
  if (!usedNativeTransition && flightStartRect) {
    await nextTick()
    await animateTwinFlight(flightStartRect, readTwinRect('.dashboard-control-twin__model'))
    await finishTwinFlight()
  } else {
    await finishTwinFlight()
  }

  launchingDeviceId.value = ''
  window.setTimeout(() => {
    if (controlModeDeviceId.value === deviceId) {
      controlContentVisible.value = true
    }
  }, 80)
}

function handleDeviceClick(device: { device_id: string }, rect?: DOMRect) {
  void enterInlineControl(device.device_id, rect || readDeviceTwinRect(device.device_id))
}

async function handleDeviceDataRefresh(device: { device_id: string; status?: string }) {
  if (!device.device_id || refreshingDeviceId.value) return

  refreshingDeviceId.value = device.device_id
  selectedDeviceId.value = device.device_id
  deviceStore.selectDevice(device.device_id)
  try {
    const ok = await fetchLatestData(device.device_id, true)
    if (ok) {
      ElMessage.success('设备数据已刷新')
    }
  } finally {
    refreshingDeviceId.value = ''
  }
}

function goToControl(deviceId: string) {
  void enterInlineControl(deviceId)
}

async function leaveInlineControl() {
  const deviceId = controlModeDeviceId.value
  const device = controlModeDevice.value
  const startRect = readTwinRect('.dashboard-control-twin__model')
  if (startRect && !prefersReducedMotion()) {
    prepareTwinFlight(startRect, device, 'return')
  }
  returningDeviceId.value = deviceId
  controlContentVisible.value = false
  await nextTick()
  const updateToDashboardMode = async () => {
    controlModeDeviceId.value = ''
    await nextTick()
  }
  const shouldUseTwinFlight = Boolean(startRect && !prefersReducedMotion())
  const usedNativeTransition = shouldUseTwinFlight
    ? false
    : await runSamePageTransition(updateToDashboardMode)
  if (shouldUseTwinFlight) {
    await updateToDashboardMode()
  }
  if (!usedNativeTransition) {
    await nextTick()
    await waitForPaintFrames(2)
    await animateTwinFlight(startRect, readDeviceTwinRect(deviceId))
    await finishTwinFlight()
  } else {
    await finishTwinFlight()
  }

  returningDeviceId.value = ''
  setNavigationHighlight(null)
  await nextTick()
  await waitForPaintFrames(1)
  await initChart()
  await loadTrendData()
}

async function handleControl(command: string, value: boolean) {
  if (!selectedDeviceId.value) return
  try {
    await sendControlCommand(selectedDeviceId.value, {
      command,
      value: value ? 'on' : 'off',
    })
    ElMessage.success(
      `${command === 'light' ? '灯光' : command === 'wechat_notify' ? '微信通知' : '专注模式'}已${value ? '开启' : '关闭'}`,
    )
  } catch {
    ElMessage.error('控制指令发送失败')
    // 恢复开关状态
    if (command === 'light') controlState.light = !value
    if (command === 'wechat_notify') controlState.wechatNotify = !value
    if (command === 'focus_mode') controlState.focus = !value
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
  if (newId && refreshingDeviceId.value !== newId) {
    fetchLatestData(newId)
    void loadTrendData(newId)
  }
})

onMounted(() => {
  fetchDevices()
  nextTick(() => {
    void initChart().then(() => loadTrendData())
  })

  ws.on('auth_result', () => {
    subscribedDeviceIds.clear()
    subscribeDevices()
  })

  // 订阅传感器数据推送
  ws.on('sensor_data', (data: Record<string, unknown>) => {
    const deviceId = data.device_id as string
    const timestamp = typeof data.timestamp === 'string'
      ? new Date(data.timestamp).getTime()
      : Date.now()
    latestTimestampByDevice.set(deviceId, Number.isFinite(timestamp) ? timestamp : Date.now())
    if (deviceId === selectedDeviceId.value) {
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined) Object.assign(sensorData, { [key]: value })
      })
      applyHardwareControlState(data)
      pushTrendData()
    }

    // 更新设备数据缓存（无论是否选中）
    if (!deviceDataCache[deviceId]) {
      deviceDataCache[deviceId] = { temperature: null, humidity: null }
    }
    deviceDataCache[deviceId].temperature = (data.temperature as number) ?? null
    deviceDataCache[deviceId].humidity = (data.humidity as number) ?? null
  })

  ws.on('device_heartbeat', (data: Record<string, unknown>) => {
    if (data.device_id === selectedDeviceId.value) {
      applyHardwareControlState(data)
    }
  })

  // 订阅设备状态变更
  ws.on('device_status', (data: Record<string, unknown>) => {
    const deviceId = typeof data.device_id === 'string' ? data.device_id : ''
    const status = data.status === 'online' ? 'online' : data.status === 'offline' ? 'offline' : null
    if (!deviceId || !status) return
    deviceStore.setDevices(deviceStore.devices.map((device) => (
      device.device_id === deviceId ? { ...device, status } : device
    )))
  })

  // 建立 WebSocket 连接
  ws.connect()

  sensorPollingTimer = window.setInterval(() => {
    if (selectedDeviceId.value && !refreshingDeviceId.value) {
      fetchLatestData(selectedDeviceId.value)
    }
  }, 5000)
  deviceCardPollingTimer = window.setInterval(() => {
    void fetchDeviceCardData()
  }, 30000)
  trendRefreshTimer = window.setInterval(() => {
    void loadTrendData()
  }, 60000)
})

onUnmounted(() => {
  window.clearInterval(sensorPollingTimer)
  window.clearInterval(deviceCardPollingTimer)
  window.clearInterval(trendRefreshTimer)
  setNavigationHighlight(null)
  ws.disconnect()
  disposeChart()
})
</script>

<style scoped src="./styles/Dashboard.css"></style>
