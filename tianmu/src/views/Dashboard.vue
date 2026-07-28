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
import type { EChartsType } from 'echarts/core'
import DeviceOverviewCard from '@/components/DeviceOverviewCard.vue'
import SensorCard from '@/components/SensorCard.vue'
import SensorMiniCard from '@/components/SensorMiniCard.vue'
import ControlToggle from '@/components/ControlToggle.vue'
import GasAlertBanner from '@/components/GasAlertBanner.vue'
import { getDeviceList, bindDevice, getLatestData, getTrendData, sendControlCommand, type SensorData } from '@/api/device'
import { useWebSocket } from '@/composables/useWebSocket'
import { useDeviceStore } from '@/store/device'
import { BEIJING_TIME_ZONE } from '@/utils/format'

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
const chartRef = ref<HTMLElement>()
type EchartsModule = typeof import('@/utils/slimEcharts')
let echartsModule: EchartsModule | null = null
let echartsLoadPromise: Promise<EchartsModule> | null = null
type EChartsOption = Parameters<EChartsType['setOption']>[0]
let chart: EChartsType | null = null

const selectedDeviceId = ref('')
const launchingDeviceId = ref('')
const returningDeviceId = ref('')
const controlModeDeviceId = ref('')
const refreshingDeviceId = ref('')
const controlContentVisible = ref(false)
const twinFlightRef = ref<HTMLElement>()
const twinFlightVisible = ref(false)
const twinFlightActive = ref(false)
const twinFlightPlaying = ref(false)
const twinFlightDirection = ref<'enter' | 'return'>('enter')
const twinFlightStyle = ref<Record<string, string>>({})
const twinFlightLabel = ref('Twin Model')
const twinFlightOffline = ref(false)
const twinFlightCleanupTimer = 0
let sensorPollingTimer = 0
let trendRefreshTimer = 0

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

// 时间范围配置
type TimeRangeKey = '1H' | '6H' | '24H' | '7D'

const timeRanges: Array<{ key: TimeRangeKey; label: string; hours: 1 | 6 | 24 | 168 }> = [
  { key: '1H', label: '1H', hours: 1 },
  { key: '6H', label: '6H', hours: 6 },
  { key: '24H', label: '24H', hours: 24 },
  { key: '7D', label: '7D', hours: 168 },
]
const activeTimeRange = ref<TimeRangeKey>('1H')
let trendRequestId = 0

// ECharts 趋势数据
const chartTimeData = ref<string[]>([])
const chartTempData = ref<Array<number | null>>([])
const chartHumidityData = ref<Array<number | null>>([])
const chartAqiData = ref<Array<number | null>>([])
const chartPm25Data = ref<Array<number | null>>([])
const chartTvocData = ref<Array<number | null>>([])
const chartEco2Data = ref<Array<number | null>>([])

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
  if (sensorData.pm25 > 35) {
    alerts.push({
      icon: '•',
      description: `PM2.5 估算偏高：${formatPm25(sensorData.pm25)} μg/m³（仅供参考）`,
      time: formatRelativeTime(),
      level: sensorData.pm25 > 75 ? 'danger' : 'warning',
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

function formatRelativeTime(): string {
  return new Date().toLocaleTimeString('zh-CN', {
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

function getPm25Status(val: number): 'normal' | 'warning' | 'danger' {
  if (val > 75) return 'danger'
  if (val > 35) return 'warning'
  return 'normal'
}

function formatPm25(val: number | undefined): string {
  if (!Number.isFinite(val) || !val) return '--'
  return val.toFixed(1)
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
    if (device.device_id) {
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
  try {
    const data = await getLatestData(deviceId)
    if (data) {
      Object.assign(sensorData, data)
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

async function loadEcharts() {
  echartsLoadPromise ??= import('@/utils/slimEcharts')
  echartsModule = await echartsLoadPromise
  return echartsModule
}

async function initChart() {
  if (!chartRef.value) return
  const { echarts } = await loadEcharts()
  if (!chartRef.value || chart) return
  const activeChart = echarts.init(chartRef.value)
  chart = activeChart

  const option: EChartsOption = {
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
      {
        name: 'AQI',
        type: 'line',
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#22C55E', width: 2 },
        itemStyle: { color: '#22C55E' },
        animationDuration: 800,
      },
      {
        name: 'PM2.5',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#94A3B8', width: 2 },
        itemStyle: { color: '#94A3B8' },
        animationDuration: 800,
      },
      {
        name: 'TVOC',
        type: 'line',
        yAxisIndex: 1,
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#FBBF24', width: 2 },
        itemStyle: { color: '#FBBF24' },
        animationDuration: 800,
      },
      {
        name: 'eCO2',
        type: 'line',
        yAxisIndex: 2,
        data: [],
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#A78BFA', width: 2 },
        itemStyle: { color: '#A78BFA' },
        animationDuration: 800,
      },
    ],
  }

  activeChart.setOption(option)
}

function renderTrendChart() {
  if (!chart) return
  chart.setOption({
    xAxis: { data: chartTimeData.value },
    series: [
      { data: chartTempData.value },
      { data: chartHumidityData.value },
      { data: chartAqiData.value },
      { data: chartPm25Data.value },
      { data: chartTvocData.value },
      { data: chartEco2Data.value },
    ],
  })
}

function formatTrendTime(timestamp: string | null) {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return '--'

  if (activeTimeRange.value === '7D') {
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

async function loadTrendData(
  deviceId = selectedDeviceId.value,
  range = activeTimeRange.value,
) {
  const requestId = ++trendRequestId
  if (!deviceId) {
    chartTimeData.value = []
    chartTempData.value = []
    chartHumidityData.value = []
    chartAqiData.value = []
    chartPm25Data.value = []
    chartTvocData.value = []
    chartEco2Data.value = []
    renderTrendChart()
    return
  }

  const rangeConfig = timeRanges.find((item) => item.key === range)
  if (!rangeConfig) return

  try {
    const records = await getTrendData(deviceId, rangeConfig.hours)
    if (
      requestId !== trendRequestId ||
      deviceId !== selectedDeviceId.value ||
      range !== activeTimeRange.value
    ) {
      return
    }

    chartTimeData.value = records.map((item) => formatTrendTime(item.timestamp))
    chartTempData.value = records.map((item) => item.temperature)
    chartHumidityData.value = records.map((item) => item.humidity)
    chartAqiData.value = records.map((item) => item.aqi)
    chartPm25Data.value = records.map((item) => item.pm25)
    chartTvocData.value = records.map((item) => item.tvoc)
    chartEco2Data.value = records.map((item) => item.eco2)
    renderTrendChart()
  } catch {
    if (requestId === trendRequestId) {
      ElMessage.error('趋势数据加载失败')
    }
  }
}

function switchTimeRange(range: TimeRangeKey) {
  activeTimeRange.value = range
  void loadTrendData(selectedDeviceId.value, range)
}

// ============================================================
// 事件处理
// ============================================================

type ViewTransitionHandle = {
  finished: Promise<void>
}

type SameDocumentTransition = Document & {
  startViewTransition?: (callback: () => void | Promise<void>) => ViewTransitionHandle
}

async function runSamePageTransition(update: () => void | Promise<void>) {
  const doc = document as SameDocumentTransition
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!doc.startViewTransition || reduceMotion) {
    await update()
    return false
  }

  const transition = doc.startViewTransition(update)
  await transition.finished.catch(() => undefined)
  return true
}

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function readTwinRect(selector: string) {
  const element = document.querySelector(selector) as HTMLElement | null
  return element?.getBoundingClientRect()
}

function readDeviceTwinRect(deviceId: string) {
  const cards = Array.from(document.querySelectorAll<HTMLElement>('[data-device-card]'))
  const card = cards.find((item) => item.dataset.deviceCard === deviceId)
  const twin = card?.querySelector('.digital-twin') as HTMLElement | null
  return twin?.getBoundingClientRect()
}

function prepareTwinFlight(
  rect: DOMRect,
  device: { device_name?: string; status?: string } | undefined,
  direction: 'enter' | 'return',
) {
  twinFlightDirection.value = direction
  twinFlightLabel.value = device?.device_name || 'Twin Model'
  twinFlightOffline.value = device?.status !== 'online'
  twinFlightStyle.value = {
    width: `${Math.max(1, rect.width)}px`,
    height: `${Math.max(1, rect.height)}px`,
    transform: `translate3d(${rect.left}px, ${rect.top}px, 0)`,
  }
  twinFlightPlaying.value = false
  twinFlightActive.value = true
  twinFlightVisible.value = true
}

async function animateTwinFlight(fromRect: DOMRect | undefined, toRect: DOMRect | undefined) {
  if (!fromRect || !toRect || prefersReducedMotion()) {
    return
  }

  const targetWidth = Math.max(1, toRect.width)
  const targetHeight = Math.max(1, toRect.height)
  const startScaleX = Math.max(0.08, fromRect.width / targetWidth)
  const startScaleY = Math.max(0.08, fromRect.height / targetHeight)

  twinFlightStyle.value = {
    width: `${targetWidth}px`,
    height: `${targetHeight}px`,
    '--twin-flight-from': `translate3d(${fromRect.left}px, ${fromRect.top}px, 0) scale(${startScaleX}, ${startScaleY})`,
    '--twin-flight-to': `translate3d(${toRect.left}px, ${toRect.top}px, 0) scale(1, 1)`,
    '--twin-flight-end-opacity': twinFlightDirection.value === 'return' ? '0.84' : '1',
  }
  twinFlightPlaying.value = true
  twinFlightVisible.value = true

  await nextTick()

  await new Promise<void>((resolve) => {
    window.setTimeout(resolve, 1080)
  })
}

async function waitForPaintFrames(count = 1) {
  for (let index = 0; index < count; index += 1) {
    await new Promise<void>((resolve) => {
      window.requestAnimationFrame(() => resolve())
    })
  }
}

async function finishTwinFlight() {
  window.clearTimeout(twinFlightCleanupTimer)
  twinFlightVisible.value = false
  await nextTick()
  twinFlightActive.value = false
  twinFlightPlaying.value = false
  twinFlightStyle.value = {}
}

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
    chart?.dispose()
    chart = null
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
    subscribeDevices()
  })

  // 订阅传感器数据推送
  ws.on('sensor_data', (data: Record<string, unknown>) => {
    const deviceId = data.device_id as string
    if (deviceId === selectedDeviceId.value) {
      Object.assign(sensorData, data)
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
  ws.on('device_status', () => {
    fetchDevices()
  })

  // 建立 WebSocket 连接
  ws.connect()

  sensorPollingTimer = window.setInterval(() => {
    if (selectedDeviceId.value && !refreshingDeviceId.value) {
      fetchLatestData(selectedDeviceId.value)
      fetchDeviceCardData()
    }
  }, 5000)
  trendRefreshTimer = window.setInterval(() => {
    void loadTrendData()
  }, 60000)
})

onUnmounted(() => {
  window.clearTimeout(twinFlightCleanupTimer)
  window.clearInterval(sensorPollingTimer)
  window.clearInterval(trendRefreshTimer)
  setNavigationHighlight(null)
  ws.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
/* ============================================================
   Liquid Glass Design System — CSS Variables
   ============================================================ */
:root {
  --glass-blur: 24px;
  --glass-saturation: 1.6;
  --glass-bg: rgba(255, 255, 255, 0.1);
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  --glass-inner-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15);
  --glass-radius: 20px;
  --color-cube-primary: #06b6d4;
  --color-cube-accent: #a3e635;
  --text-primary: #e8ecf4;
  --text-secondary: #8b95b0;
  --text-disabled: #475569;
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 420ms cubic-bezier(0.2, 0.9, 0.2, 1);
  --transition-fast: 150ms ease;
}

/* ============================================================
   Page Container
   ============================================================ */
.dashboard-page {
  padding: 4px;
  min-height: 100vh;
  background: transparent;
}

/* ============================================================
   Hero Brand Stage — Glass Panel
   ============================================================ */
.dashboard-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(380px, 0.9fr);
  gap: 24px;
  align-items: stretch;
  min-height: 292px;
  margin-bottom: 28px;
  padding: 24px;
  border: 1px solid rgba(181, 229, 255, 0.34);
  border-radius: 28px;
  background:
    linear-gradient(118deg, rgba(81, 198, 255, 0.11), rgba(4, 21, 47, 0.34) 43%, rgba(105, 73, 255, 0.1)),
    rgba(4, 19, 42, 0.28);
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  box-shadow:
    0 30px 76px rgba(0, 4, 22, 0.32),
    inset 0 1px 0 rgba(245, 253, 255, 0.48),
    inset 1px 0 0 rgba(80, 214, 255, 0.16),
    inset 0 -1px 0 rgba(104, 78, 255, 0.22);
  isolation: isolate;
}

/* Subtle top highlight — light reflecting off glass edge */
.dashboard-hero::before {
  content: '';
  position: absolute;
  top: 0;
  left: 2%;
  right: 2%;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.78) 26%,
    rgba(63, 212, 255, 0.6) 52%,
    rgba(151, 116, 255, 0.46) 78%,
    transparent
  );
  z-index: 1;
  pointer-events: none;
}

/* Subtle bottom ambient glow */
.dashboard-hero::after {
  content: '';
  position: absolute;
  bottom: -70px;
  left: 48%;
  right: -8%;
  height: 150px;
  height: 1px;
  background: radial-gradient(ellipse, rgba(80, 139, 255, 0.24), rgba(141, 67, 255, 0.08) 48%, transparent 72%);
  filter: blur(22px);
  opacity: 0.9;
  z-index: 1;
  pointer-events: none;
}

.dashboard-hero__particles {
  z-index: 0;
}

.dashboard-hero__copy,
.dashboard-hero__mascot {
  position: relative;
  z-index: 2;
}

.dashboard-hero__copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 10px 4px;
}

.dashboard-hero__mark {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  opacity: 0.72;
  animation: dashboard-title-sweep 880ms cubic-bezier(0.16, 1, 0.3, 1) 260ms both;
  will-change: transform, opacity;
}

.dashboard-hero__cube {
  position: relative;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background:
    linear-gradient(135deg, var(--color-cube-primary), var(--color-cube-accent));
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.46);
}

.dashboard-hero__title {
  margin: 18px 0 0;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: clamp(34px, 5vw, 64px);
  font-weight: 850;
  line-height: 1;
  letter-spacing: 0;
  animation: dashboard-title-sweep 1040ms cubic-bezier(0.16, 1, 0.3, 1) 380ms both;
  will-change: transform, opacity;
}

.dashboard-hero__desc {
  max-width: 660px;
  margin: 18px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.8;
  animation: dashboard-title-sweep 940ms cubic-bezier(0.16, 1, 0.3, 1) 540ms both;
  will-change: transform, opacity;
}

.dashboard-hero__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  max-width: 640px;
  margin-top: 26px;
}

.dashboard-hero__stat {
  min-width: 0;
  padding: 13px 14px;
  border: 1px solid rgba(190, 231, 255, 0.25);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(145, 218, 255, 0.12), rgba(15, 42, 82, 0.18));
  backdrop-filter: blur(18px) saturate(1.9);
  -webkit-backdrop-filter: blur(18px) saturate(1.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32), 0 12px 30px rgba(0, 4, 22, 0.16);
  animation: dashboard-block-rise 860ms cubic-bezier(0.16, 1, 0.3, 1) both;
  will-change: transform, opacity;
}

.dashboard-hero__stat:nth-child(1) { animation-delay: 700ms; }
.dashboard-hero__stat:nth-child(2) { animation-delay: 820ms; }
.dashboard-hero__stat:nth-child(3) { animation-delay: 940ms; }

.dashboard-hero__stat strong {
  display: block;
  overflow: hidden;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 20px;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-hero__stat span {
  display: block;
  overflow: hidden;
  margin-top: 6px;
  color: var(--text-disabled);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-hero__mascot {
  align-self: center;
}

/* ============================================================
   Common Section
   ============================================================ */
.dashboard-section {
  margin-bottom: 26px;
  animation: dashboard-block-rise 940ms cubic-bezier(0.16, 1, 0.3, 1) both;
  will-change: transform, opacity;
}

.dashboard-section:nth-of-type(2) { animation-delay: 780ms; }
.dashboard-section:nth-of-type(3) { animation-delay: 940ms; }
.dashboard-section:nth-of-type(4) { animation-delay: 1100ms; }

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
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 9999px;
  background: linear-gradient(
    180deg,
    var(--color-cube-primary),
    var(--color-cube-accent)
  );
  box-shadow: 0 0 14px rgba(6, 182, 212, 0.45);
}

.section-subtitle {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: 12px;
}

/* ============================================================
   Device Cards Scroll
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

/* Device card sizing */
.device-cards-scroll :deep(.device-overview-card) {
  min-width: 240px;
  max-width: 260px;
  flex-shrink: 0;
}

/* ============================================================
   Add Device Card — Glass
   ============================================================ */
.add-device-card {
  min-width: 200px;
  max-width: 220px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(80, 183, 255, 0.08), rgba(6, 23, 50, 0.28));
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  border: 1px dashed rgba(163, 230, 53, 0.34);
  border-radius: var(--glass-radius);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 14px;
  cursor: pointer;
  transition:
    transform var(--transition-spring),
    border-color var(--transition-base),
    box-shadow var(--transition-base),
    background var(--transition-base);
  box-shadow: var(--glass-inner-shadow);
}

/* Subtle top highlight — light reflecting off glass edge */
.add-device-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10px;
  right: 10px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.35),
    transparent
  );
  pointer-events: none;
}

.add-device-card:hover {
  border-color: rgba(163, 230, 53, 0.62);
  background: rgba(163, 230, 53, 0.055);
  transform: translateY(-5px);
  box-shadow:
    0 0 24px rgba(163, 230, 53, 0.12),
    var(--glass-shadow);
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
  color: var(--color-cube-accent);
  line-height: 1;
  position: relative;
  z-index: 1;
}

.add-device-card__text {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary);
  position: relative;
  z-index: 1;
}

/* ============================================================
   Two Column Layout
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
   Sensor Cards Grid (Main Metrics)
   ============================================================ */
.sensor-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 10px;
}

.pm25-reference-note {
  margin: 0 0 16px;
  padding: 9px 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 12px;
  color: rgba(226, 232, 240, 0.72);
  background: rgba(148, 163, 184, 0.055);
  font-size: 12px;
  line-height: 1.45;
}

/* ============================================================
   Sensor Mini Cards Grid (Secondary Metrics — 3 cols)
   ============================================================ */
.sensor-mini-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

/* ============================================================
   Right Column Panels — Glass
   ============================================================ */
.panel {
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(71, 171, 238, 0.075), rgba(4, 19, 42, 0.34));
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  border: 1px solid rgba(182, 226, 255, 0.2);
  border-radius: var(--glass-radius);
  padding: 16px;
  box-shadow:
    var(--glass-shadow),
    var(--glass-inner-shadow);
}

/* Subtle top highlight — light reflecting off glass */
.panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.5),
    transparent
  );
  pointer-events: none;
}

.control-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ============================================================
   Alert List
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
  border-radius: 12px;
  background: rgba(92, 183, 244, 0.055);
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  border: 1px solid rgba(182, 226, 255, 0.12);
  box-shadow: var(--glass-inner-shadow);
  transition:
    transform var(--transition-base),
    border-color var(--transition-base),
    background var(--transition-base);
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
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-item__time {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 11px;
  color: var(--text-secondary);
}

.alert-empty {
  text-align: center;
  padding: 20px;
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary);
}

/* ============================================================
   Chart Section — Glass
   ============================================================ */
.chart-wrapper {
  position: relative;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(69, 168, 235, 0.07), rgba(3, 17, 38, 0.34));
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  border: 1px solid rgba(182, 226, 255, 0.19);
  border-radius: var(--glass-radius);
  padding: 16px;
  box-shadow:
    var(--glass-shadow),
    var(--glass-inner-shadow);
}

/* Subtle top highlight — light reflecting off glass */
.chart-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.5),
    transparent
  );
  pointer-events: none;
}

.chart-container {
  height: 320px;
  width: 100%;
}

/* ============================================================
   Time Range Buttons — Glass
   ============================================================ */
.time-range-buttons {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: rgba(83, 178, 244, 0.07);
  backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturation));
  border: 1px solid rgba(182, 226, 255, 0.18);
  border-radius: 10px;
  box-shadow: var(--glass-inner-shadow);
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
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.time-range-btn:hover {
  border-color: rgba(6, 182, 212, 0.24);
  color: var(--text-primary);
}

.time-range-btn--active {
  background: linear-gradient(
    135deg,
    var(--color-cube-primary),
    var(--color-cube-accent)
  );
  border-color: rgba(255, 255, 255, 0.1);
  color: #060a18;
  font-weight: 600;
  box-shadow: 0 0 18px rgba(6, 182, 212, 0.2);
}

/* ============================================================
   Inline Digital Twin Control Mode
   ============================================================ */
:global(::view-transition-group(active-twin)) {
  animation-duration: 860ms;
  animation-timing-function: cubic-bezier(0.2, 0.9, 0.18, 1);
}

:global(::view-transition-old(root)),
:global(::view-transition-new(root)) {
  animation: none;
  mix-blend-mode: normal;
}

.dashboard-control-mode {
  position: relative;
  min-height: calc(100vh - 108px);
  padding: 22px;
  overflow: hidden;
  border: 1px solid rgba(216, 242, 255, 0.24);
  border-radius: 30px;
  background:
    radial-gradient(circle at 50% 45%, rgba(34, 211, 238, 0.18), transparent 42%),
    radial-gradient(circle at 78% 18%, rgba(163, 230, 53, 0.08), transparent 32%),
    linear-gradient(145deg, rgba(91, 184, 255, 0.1), rgba(4, 18, 42, 0.34));
  box-shadow:
    0 30px 76px rgba(0, 4, 22, 0.32),
    inset 0 1px 0 rgba(245, 253, 255, 0.42),
    inset 0 -1px 0 rgba(104, 78, 255, 0.18);
  backdrop-filter: blur(30px) saturate(1.8);
  -webkit-backdrop-filter: blur(30px) saturate(1.8);
  isolation: isolate;
}

.dashboard-control-mode__particles {
  z-index: 0;
}

.dashboard-control-back,
.dashboard-control-titlebar,
.dashboard-control-stage {
  position: relative;
  z-index: 2;
}

.dashboard-control-mode__particles,
.dashboard-control-back,
.dashboard-control-titlebar,
.dashboard-control-panel,
.dashboard-control-twin__halo,
.control-twin-lite {
  opacity: 0;
}

.dashboard-control-mode--revealed .dashboard-control-mode__particles {
  animation: control-fade-in 980ms ease both;
}

.dashboard-control-mode--revealed .dashboard-control-back {
  animation: control-back-load 780ms cubic-bezier(0.16, 1, 0.3, 1) 140ms both;
}

.dashboard-control-mode--revealed .dashboard-control-titlebar {
  animation: control-title-load 920ms cubic-bezier(0.16, 1, 0.3, 1) 260ms both;
}

.dashboard-control-mode--revealed .dashboard-control-twin__halo {
  animation:
    control-fade-in 880ms ease 420ms both,
    twin-platform-turn 18s linear 420ms infinite;
}

.dashboard-control-mode--revealed .control-twin-lite {
  animation: control-fade-in 880ms ease 420ms both;
}

.dashboard-control-mode--revealed .dashboard-control-panel {
  animation: control-panel-load 920ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

.dashboard-control-mode--revealed .dashboard-control-panel--legend {
  animation-delay: 520ms;
}

.dashboard-control-mode--revealed .dashboard-control-panel--actions {
  animation-delay: 680ms;
}

.dashboard-control-back {
  height: 38px;
  padding: 0 14px 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font: 600 13px/1 var(--font-body);
  border: 1px solid rgba(216, 242, 255, 0.28);
  border-radius: 13px;
  background: linear-gradient(145deg, rgba(124, 211, 255, 0.14), rgba(9, 26, 55, 0.46));
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  backdrop-filter: blur(26px) saturate(1.8);
  -webkit-backdrop-filter: blur(26px) saturate(1.8);
  cursor: pointer;
  transition:
    transform var(--transition-spring),
    border-color var(--transition-base),
    background var(--transition-base);
}

.dashboard-control-back:hover {
  transform: translateX(-3px);
  border-color: rgba(226, 250, 255, 0.5);
  background: var(--glass-bg-hover);
}

.dashboard-control-back__arrow {
  font-size: 22px;
  line-height: 1;
}

.dashboard-control-titlebar {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 18px;
  border: 1px solid rgba(216, 242, 255, 0.2);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.045);
  box-shadow: var(--glass-inner-shadow);
  backdrop-filter: blur(24px) saturate(1.7);
  -webkit-backdrop-filter: blur(24px) saturate(1.7);
}

.dashboard-control-titlebar__eyebrow {
  display: block;
  margin-bottom: 4px;
  color: rgba(163, 230, 53, 0.78);
  font-family: var(--font-mono);
  font-size: 10px;
}

.dashboard-control-titlebar h2 {
  margin: 0;
  color: var(--text-primary);
  font: 760 24px/1.15 var(--font-display);
}

.dashboard-control-titlebar small {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
}

.dashboard-control-titlebar__status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.dashboard-control-titlebar__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dashboard-control-titlebar__dot.is-online {
  background: var(--color-success);
  box-shadow: 0 0 14px rgba(52, 211, 153, 0.62);
}

.dashboard-control-titlebar__dot.is-offline {
  background: var(--text-disabled);
}

.dashboard-control-stage {
  min-height: 500px;
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(320px, 1fr) minmax(280px, 360px);
  align-items: center;
  gap: 18px;
}

.dashboard-control-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(216, 242, 255, 0.2);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(102, 198, 255, 0.1), rgba(5, 22, 49, 0.34));
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  backdrop-filter: blur(26px) saturate(1.8);
  -webkit-backdrop-filter: blur(26px) saturate(1.8);
  will-change: transform, opacity;
}

.dashboard-control-panel__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 16px 13px;
  border-bottom: 1px solid rgba(216, 242, 255, 0.12);
}

.dashboard-control-panel__header span {
  color: var(--text-primary);
  font: 700 14px/1 var(--font-display);
}

.dashboard-control-panel__header small {
  color: var(--text-disabled);
  font-family: var(--font-mono);
  font-size: 10px;
}

.dashboard-air-legend,
.dashboard-control-actions {
  display: grid;
  gap: 9px;
  padding: 14px;
}

.dashboard-air-legend__item {
  display: grid;
  grid-template-columns: 12px minmax(52px, auto) 1fr;
  align-items: center;
  gap: 8px;
  padding: 8px 9px;
  border: 1px solid rgba(216, 242, 255, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.045);
}

.dashboard-air-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.dashboard-air-legend__item strong {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 11px;
}

.dashboard-air-legend__item span:last-child {
  color: var(--text-secondary);
  font-size: 12px;
  text-align: right;
}

.dashboard-control-twin {
  position: relative;
  min-height: 470px;
  display: grid;
  place-items: center;
}

.dashboard-control-twin__halo {
  position: absolute;
  width: min(52vw, 560px);
  aspect-ratio: 1;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.15), transparent 60%),
    conic-gradient(from 120deg, transparent, rgba(163, 230, 53, 0.16), transparent, rgba(34, 211, 238, 0.14), transparent);
}

.dashboard-control-twin__model {
  position: relative;
  z-index: 2;
  width: min(50vw, 560px);
  aspect-ratio: 1;
  view-transition-name: active-twin;
  contain: layout;
  will-change: transform, opacity;
}

.dashboard-control-twin__model--flight-hidden {
  opacity: 0;
}

.control-twin-lite {
  position: relative;
  display: grid;
  place-items: center;
  isolation: isolate;
}

.control-twin-lite__glow {
  position: absolute;
  inset: 10%;
  z-index: -1;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.22), transparent 56%),
    radial-gradient(circle at 55% 64%, rgba(163, 230, 53, 0.12), transparent 50%);
  filter: blur(18px);
}

.control-twin-lite__visual {
  position: relative;
  width: 100%;
  display: grid;
  place-items: center;
}

.control-twin-lite__image {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
  filter: drop-shadow(0 26px 46px rgba(0, 0, 0, 0.26));
  transform: none;
}

.control-twin-lite__screen {
  position: absolute;
  left: 50.24%;
  top: 52.07%;
  width: 33.84%;
  min-width: 128px;
  aspect-ratio: 1.31;
  transform: translate(-50%, -50%);
  display: block;
  padding: 0;
  overflow: hidden;
  background: #0c1024;
  border: 0;
  border-radius: 3px;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.42);
  pointer-events: none;
}

.control-twin-lite__label {
  position: absolute;
  left: 50%;
  bottom: 5%;
  transform: translateX(-50%);
  display: grid;
  gap: 4px;
  justify-items: center;
  width: max-content;
  max-width: 80%;
  padding: 8px 12px;
  border: 1px solid rgba(216, 242, 255, 0.12);
  border-radius: 999px;
  color: var(--text-secondary);
  background: rgba(4, 18, 40, 0.24);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}

.control-twin-lite__label span {
  max-width: 18em;
  overflow: hidden;
  color: var(--text-primary);
  font: 600 12px/1 var(--font-body);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.control-twin-lite__label small {
  color: rgba(163, 230, 53, 0.72);
  font: 600 10px/1 var(--font-mono);
}

.control-twin-lite--offline {
  filter: grayscale(0.65);
  opacity: 0.66;
}

.dashboard-twin-flight {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 80;
  pointer-events: none;
  transform-origin: top left;
  will-change: transform, opacity, filter;
  contain: layout paint style;
  opacity: 0.78;
  filter: blur(0.8px) saturate(1.08);
  transform: var(--twin-flight-from, translate3d(0, 0, 0));
}

.dashboard-twin-flight--playing {
  animation: twin-flight-run 1050ms cubic-bezier(0.34, 0, 0.18, 1) both;
}

.dashboard-twin-flight :deep(.digital-twin) {
  --twin-size: 100%;
  width: 100%;
  height: 100%;
}

.dashboard-control-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 6px;
}

.dashboard-control-metrics div {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid rgba(216, 242, 255, 0.12);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.045);
}

.dashboard-control-metrics span,
.dashboard-control-metrics strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-control-metrics span {
  color: var(--text-secondary);
  font-size: 11px;
}

.dashboard-control-metrics strong {
  margin-top: 4px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
}

.dashboard-control-actions--disabled {
  opacity: 0.52;
}

@keyframes control-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes control-back-load {
  from {
    opacity: 0;
    transform: translateX(-18px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes control-title-load {
  from {
    opacity: 0;
    transform: translateX(34px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes control-panel-load {
  from {
    opacity: 0;
    transform: translateY(28px) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes twin-flight-run {
  0% {
    opacity: 0.78;
    filter: blur(0.8px) saturate(1.08);
    transform: var(--twin-flight-from, translate3d(0, 0, 0));
  }
  58% {
    opacity: 1;
    filter: blur(0.12px) saturate(1.18);
  }
  100% {
    opacity: var(--twin-flight-end-opacity, 1);
    filter: blur(0) saturate(1);
    transform: var(--twin-flight-to, translate3d(0, 0, 0));
  }
}

@keyframes twin-platform-turn {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes dashboard-title-sweep {
  from {
    opacity: 0;
    transform: translateX(34px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes dashboard-block-rise {
  from {
    opacity: 0;
    transform: translateY(28px) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard-hero__mark,
  .dashboard-hero__title,
  .dashboard-hero__desc,
  .dashboard-hero__stat,
  .dashboard-section,
  .dashboard-control-mode__particles,
  .dashboard-control-back,
  .dashboard-control-titlebar,
  .dashboard-control-panel,
  .dashboard-control-twin__halo {
    animation: none !important;
    filter: none !important;
    transform: none !important;
    opacity: 1 !important;
  }

  .dashboard-control-twin__model--flight-hidden {
    opacity: 1 !important;
  }
}

/* ============================================================
   Responsive Breakpoints
   ============================================================ */
@media (max-width: 1024px) {
  .dashboard-hero {
    grid-template-columns: 1fr;
  }

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

  .dashboard-hero {
    padding: 16px;
    border-radius: 14px;
  }

  .dashboard-hero__stats {
    grid-template-columns: 1fr;
  }

  .sensor-cards-grid {
    grid-template-columns: 1fr;
  }

  .sensor-mini-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
