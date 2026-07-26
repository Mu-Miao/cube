<!-- Control.vue -->
<!-- 控制面板页 -->
<!-- 左侧设备列表 + 右侧控制区（灯光/消息通知/系统控制/日志） -->
<!-- 设备离线时所有控件置灰，禁止操作 -->
<template>
  <div class="control-page">
    <button class="control-back" title="返回控制台" @click="goBackToDashboard">
      <ArrowLeft class="control-back__icon" />
      <span>控制台</span>
    </button>

    <div v-if="!currentDevice" class="control-empty">
      <el-icon :size="48" color="var(--text-disabled)"><Monitor /></el-icon>
      <div class="control-empty__text">请先选择一个设备</div>
    </div>

    <template v-else>
      <MineradioParticleStage
        class="control-air-stage"
        embedded
        variant="hero"
        :density="0.18"
        :fps="24"
        :intensity="isOnline ? 0.36 : 0.18"
        :show-labels="false"
      />

      <header class="control-titlebar">
        <div class="control-titlebar__info">
          <span class="control-titlebar__eyebrow">数字孪生控制面板</span>
          <h2>{{ currentDevice.device_name }}</h2>
          <span>{{ currentDevice.device_id }}</span>
        </div>
        <div class="control-titlebar__devices">
          <button
            v-for="device in deviceStore.devices"
            :key="device.device_id"
            class="device-chip"
            :class="{ 'device-chip--active': selectedDeviceId === device.device_id }"
            @click="selectDevice(device.device_id)"
          >
            <DeviceStatusDot :status="device.status" />
            <span>{{ device.device_name }}</span>
          </button>
        </div>
      </header>

      <div v-if="!isOnline" class="control-offline-tip">
        <el-icon :size="16"><WarningFilled /></el-icon>
        <span>设备已离线，无法控制</span>
      </div>

      <main class="control-stage">
        <section class="control-column control-column--left">
          <div class="control-panel control-panel--compact">
            <div class="control-panel__header">
              <span class="control-panel__title">空气成分图例</span>
              <span class="control-panel__subtitle">轻量粒子层</span>
            </div>
            <div class="air-legend">
              <div v-for="item in airLegend" :key="item.label" class="air-legend__item">
                <span class="air-legend__dot" :style="{ background: item.color }"></span>
                <span class="air-legend__label">{{ item.label }}</span>
                <span class="air-legend__name">{{ item.name }}</span>
              </div>
            </div>
          </div>

          <div class="control-panel control-panel--compact">
            <div class="control-panel__header">
              <span class="control-panel__title">孪生状态</span>
              <span class="control-panel__status">
                <DeviceStatusDot :status="isOnline ? 'online' : 'offline'" />
                {{ isOnline ? '同步中' : '离线' }}
              </span>
            </div>
            <div class="twin-metrics">
              <div class="twin-metric">
                <span>灯光</span>
                <strong>{{ lightState.on ? `${lightState.brightness}%` : 'OFF' }}</strong>
              </div>
              <div class="twin-metric">
                <span>微信通知</span>
                <strong>{{ wechatNotifyState ? 'ON' : 'OFF' }}</strong>
              </div>
              <div class="twin-metric">
                <span>专注模式</span>
                <strong>{{ focusMode ? 'ON' : 'OFF' }}</strong>
              </div>
            </div>
          </div>
        </section>

        <section class="control-twin-stage" :class="{ 'control-twin-stage--hidden': twinLaunchOverlay }">
          <div ref="centralTwinRef" class="control-twin-stage__model">
            <div class="control-twin-lite" :class="{ 'control-twin-lite--offline': !isOnline }" :aria-label="currentDevice.device_name">
              <div class="control-twin-lite__glow" aria-hidden="true"></div>
              <div class="control-twin-lite__visual">
                <img class="control-twin-lite__image" src="/smart-cube-transparent.png" alt="智能桌面魔方模型预览" />
                <div class="control-twin-lite__screen" aria-label="魔方屏幕实时数据">
                  <HardwareTwinScreen :data="latestSensorData" :online="isOnline" :focus="focusMode" />
                </div>
              </div>
              <div class="control-twin-lite__label">
                <span>{{ currentDevice.device_name }}</span>
                <small>{{ isOnline ? 'LIGHTWEIGHT TWIN' : 'OFFLINE' }}</small>
              </div>
            </div>
          </div>
        </section>

        <section class="control-column control-column--right" :class="{ 'control-panels--disabled': !isOnline }">
          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">灯光控制</span>
              <span class="control-panel__status">
                <DeviceStatusDot :status="lightState.on ? 'online' : 'offline'" />
                {{ lightState.on ? '开启' : '关闭' }}
              </span>
            </div>
            <div class="control-panel__body">
              <LightColorPicker
                :model-value="lightState"
                @update:model-value="Object.assign(lightState, $event)"
                :disabled="!isOnline"
                :loading="toggleLoading.light"
              />
            </div>
          </div>

          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">开关设置</span>
            </div>
            <div class="control-panel__body control-panel__body--toggles">
              <ControlToggle v-model="wechatNotifyState" label="微信消息通知" :disabled="!isOnline" :loading="toggleLoading.wechat_notify" />
              <ControlToggle v-model="autoScreenBrightness" label="自动屏幕亮度" :disabled="!isOnline" :loading="toggleLoading.auto_screen_brightness" />
            </div>
          </div>

          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">系统控制</span>
            </div>
            <div class="control-panel__body">
              <ControlToggle v-model="focusMode" label="专注模式" :disabled="!isOnline" :loading="toggleLoading.focus_mode" />
              <div class="slider-control">
                <span class="slider-control__label">屏幕亮度</span>
                <div class="slider-control__slider">
                  <el-slider v-model="screenBrightness" :min="0" :max="100" :disabled="!isOnline || autoScreenBrightness" :show-tooltip="true" @change="handleScreenBrightnessChange" />
                </div>
                <span class="slider-control__value">{{ autoScreenBrightness ? '自动' : `${screenBrightness}%` }}</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <section class="control-log-dock">
        <div class="control-panel">
          <div class="control-panel__header">
            <span class="control-panel__title">控制日志</span>
            <span class="control-panel__subtitle">近 3 天 · 最近 {{ maxLogs }} 条</span>
          </div>
          <div class="control-panel__body">
            <div v-if="controlLogs.length === 0" class="log-empty">暂无操作记录</div>
            <div v-else class="log-list">
              <div v-for="log in controlLogs" :key="log.id" class="log-item">
                <span class="log-item__time">{{ log.time }}</span>
                <span class="log-item__desc">{{ log.description }}</span>
                <el-tag :type="log.status === 'success' ? 'success' : 'danger'" size="small" effect="plain" class="log-item__tag">
                  {{ log.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <CubeSpinGifPreview
      v-if="twinLaunchOverlay"
      class="control-twin-launch"
      :class="{ 'control-twin-launch--settled': twinLaunchOverlay.settled }"
      :style="twinLaunchStyle"
      :label="currentDevice?.device_name || 'Twin Model'"
      :offline="!isOnline"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, defineAsyncComponent, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ArrowLeft, Monitor, WarningFilled } from '@element-plus/icons-vue'
import DeviceStatusDot from '@/components/DeviceStatusDot.vue'
import LightColorPicker from '@/components/LightColorPicker.vue'
import ControlToggle from '@/components/ControlToggle.vue'
import { useDeviceStore } from '@/store/device'
import { getDeviceList, getLatestData, sendControlCommand, type SensorData } from '@/api/device'
import { useWebSocket } from '@/composables/useWebSocket'
defineOptions({ name: 'ControlPage' })

const CubeSpinGifPreview = defineAsyncComponent(() => import('@/components/brand/CubeSpinGifPreview.vue'))
const HardwareTwinScreen = defineAsyncComponent(() => import('@/components/brand/HardwareTwinScreen.vue'))
const MineradioParticleStage = defineAsyncComponent(() => import('@/components/brand/MineradioParticleStage.vue'))

const route = useRoute()
const router = useRouter()
const deviceStore = useDeviceStore()

// 当前选中的设备 ID
const selectedDeviceId = ref('')
const centralTwinRef = ref<HTMLElement>()
const twinLaunchOverlay = ref<{
  from: { left: number; top: number; width: number; height: number }
  to: { left: number; top: number; width: number; height: number }
  settled: boolean
} | null>(null)

// 最大展示日志条数；完整记录会在本地保留 3 天
const maxLogs = 5
const LOG_RETENTION_MS = 3 * 24 * 60 * 60 * 1000
const CONTROL_LOG_STORAGE_PREFIX = 'tianmu:control-logs:'

const airLegend = [
  { label: 'O2', name: '氧气', color: '#a3e635' },
  { label: 'CO2', name: '二氧化碳', color: '#60a5fa' },
  { label: 'H2O', name: '水汽', color: '#22d3ee' },
  { label: 'PM2.5', name: '细颗粒物', color: '#9ca3af' },
  { label: 'TVOC', name: '挥发物', color: '#fbbf24' },
  { label: 'CH2O', name: '甲醛', color: '#fb7185' },
]

// 当前设备对象
const currentDevice = computed(() => {
  return deviceStore.devices.find((d) => d.device_id === selectedDeviceId.value) || null
})

// 设备是否在线
const isOnline = computed(() => {
  return currentDevice.value?.status === 'online'
})

const latestSensorData = ref<SensorData | null>(null)
let sensorRefreshTimer: ReturnType<typeof window.setInterval> | undefined
const ws = useWebSocket('/ws')
let syncingHardwareState = false

const twinLaunchStyle = computed(() => {
  if (!twinLaunchOverlay.value) return undefined
  const rect = twinLaunchOverlay.value.settled ? twinLaunchOverlay.value.to : twinLaunchOverlay.value.from
  return {
    left: `${rect.left}px`,
    top: `${rect.top}px`,
    width: `${rect.width}px`,
    height: `${rect.height}px`,
  }
})

// === 灯光状态 ===
interface LightValue {
  on: boolean
  colorTemperature: number
  brightness: number
}
const lightState = reactive<LightValue>({
  on: false,
  colorTemperature: 3000,
  brightness: 80,
})

// === 微信消息通知状态 ===
const wechatNotifyState = ref(false)

// === 系统控制 ===
const focusMode = ref(false)
const screenBrightness = ref(60)
const autoScreenBrightness = ref(false)

// === Toggle 加载状态 ===
const toggleLoading = reactive({
  light: false,
  wechat_notify: false,
  auto_screen_brightness: false,
  focus_mode: false,
})

// === 控制日志 ===
interface ControlLog {
  id: number
  timestamp: number
  time: string
  description: string
  status: 'success' | 'error'
}
const controlLogs = ref<ControlLog[]>([])
let logIdCounter = 0

function controlLogStorageKey(deviceId: string) {
  return `${CONTROL_LOG_STORAGE_PREFIX}${deviceId}`
}

function formatLogTime(timestamp: number) {
  const date = new Date(timestamp)
  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  return isToday
    ? date.toLocaleTimeString('zh-CN', { hour12: false })
    : date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      })
}

function normalizeLogs(rawLogs: unknown): ControlLog[] {
  if (!Array.isArray(rawLogs)) return []
  const cutoff = Date.now() - LOG_RETENTION_MS

  return rawLogs
    .map((log) => {
      const item = log as Partial<ControlLog>
      const timestamp =
        typeof item.timestamp === 'number' && Number.isFinite(item.timestamp)
          ? item.timestamp
          : 0

      if (!timestamp || timestamp < cutoff) return null

      return {
        id: typeof item.id === 'number' ? item.id : timestamp,
        timestamp,
        time: formatLogTime(timestamp),
        description: typeof item.description === 'string' ? item.description : '',
        status: item.status === 'error' ? 'error' : 'success',
      } satisfies ControlLog
    })
    .filter((log): log is ControlLog => Boolean(log && log.description))
    .sort((a, b) => b.timestamp - a.timestamp)
}

function readStoredControlLogs(deviceId: string): ControlLog[] {
  if (!deviceId) return []
  try {
    const raw = window.localStorage.getItem(controlLogStorageKey(deviceId))
    return normalizeLogs(raw ? JSON.parse(raw) : [])
  } catch {
    return []
  }
}

function saveStoredControlLogs(deviceId: string, logs: ControlLog[]) {
  if (!deviceId) return
  try {
    window.localStorage.setItem(controlLogStorageKey(deviceId), JSON.stringify(logs))
  } catch {
    // localStorage 满或不可用时，不影响控制功能
  }
}

function loadControlLogs(deviceId: string) {
  const logs = readStoredControlLogs(deviceId)
  controlLogs.value = logs.slice(0, maxLogs)
  logIdCounter = Math.max(logIdCounter, ...logs.map((log) => log.id), 0)
  saveStoredControlLogs(deviceId, logs)
}

/**
 * 添加控制日志
 */
function addLog(description: string, status: 'success' | 'error') {
  if (!selectedDeviceId.value) return
  const now = new Date()
  const timestamp = now.getTime()
  const nextLog: ControlLog = {
    id: ++logIdCounter,
    timestamp,
    time: formatLogTime(timestamp),
    description,
    status,
  }
  const logs = normalizeLogs([nextLog, ...readStoredControlLogs(selectedDeviceId.value)])
  controlLogs.value = logs.slice(0, maxLogs)
  saveStoredControlLogs(selectedDeviceId.value, logs)
}

function applyHardwareControlState(data: Partial<SensorData> | Record<string, unknown> | null | undefined) {
  if (!data) return
  syncingHardwareState = true

  if (typeof data.light === 'boolean') lightState.on = data.light
  if (typeof data.color_temperature === 'number') lightState.colorTemperature = data.color_temperature
  if (typeof data.light_brightness === 'number') lightState.brightness = data.light_brightness
  if (typeof data.wechat_notify === 'boolean') wechatNotifyState.value = data.wechat_notify
  if (typeof data.auto_screen_brightness === 'boolean') autoScreenBrightness.value = data.auto_screen_brightness
  if (typeof data.screen_brightness === 'number') screenBrightness.value = data.screen_brightness
  if (typeof data.focus_mode === 'boolean') focusMode.value = data.focus_mode

  nextTick(() => {
    syncingHardwareState = false
  })
}

/**
 * 发送控制指令（带响应码检查）
 */
async function sendCommand(command: string, value: string): Promise<boolean> {
  if (!selectedDeviceId.value) return false
  try {
    await sendControlCommand(selectedDeviceId.value, { command, value })
    return true
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg = error.response?.data?.detail || error.response?.data?.message || '指令发送失败'
    ElMessage.error(msg)
    return false
  }
}

// === 灯光控制监听 ===
watch(() => lightState.on, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  if (syncingHardwareState) return
  toggleLoading.light = true
  const command = newVal ? 'on' : 'off'
  const ok = await sendCommand('light', command)
  addLog(`${newVal ? '开启' : '关闭'}灯光`, ok ? 'success' : 'error')
  toggleLoading.light = false
})

watch(() => lightState.colorTemperature, async (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  if (syncingHardwareState) return
  const ok = await sendCommand('color_temperature', String(newVal))
  addLog(`色温 -> ${newVal}K`, ok ? 'success' : 'error')
})

watch(() => lightState.brightness, async (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  if (syncingHardwareState) return
  const ok = await sendCommand('light_brightness', String(newVal))
  addLog(`灯光亮度 -> ${newVal}%`, ok ? 'success' : 'error')
})

// === 微信消息通知监听 ===
watch(wechatNotifyState, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  if (syncingHardwareState) return
  toggleLoading.wechat_notify = true
  const ok = await sendCommand('wechat_notify', newVal ? 'on' : 'off')
  addLog(`${newVal ? '开启' : '关闭'}微信消息通知`, ok ? 'success' : 'error')
  toggleLoading.wechat_notify = false
})

// === 自动屏幕亮度监听 ===
watch(autoScreenBrightness, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  if (syncingHardwareState) return
  toggleLoading.auto_screen_brightness = true
  const ok = await sendCommand('auto_screen_brightness', newVal ? 'on' : 'off')
  addLog(`${newVal ? '开启' : '关闭'}自动屏幕亮度`, ok ? 'success' : 'error')
  toggleLoading.auto_screen_brightness = false
})

// === 专注模式控制监听 ===
watch(focusMode, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  if (syncingHardwareState) return
  toggleLoading.focus_mode = true
  const ok = await sendCommand('focus_mode', newVal ? 'on' : 'off')
  addLog(`专注模式 -> ${newVal ? 'ON' : 'OFF'}`, ok ? 'success' : 'error')
  toggleLoading.focus_mode = false
})

// === 屏幕亮度 ===
async function handleScreenBrightnessChange(val: number) {
  const ok = await sendCommand('screen_brightness', String(val))
  addLog(`屏幕亮度 -> ${val}%`, ok ? 'success' : 'error')
}

/**
 * 选择设备
 */
function selectDevice(deviceId: string) {
  selectedDeviceId.value = deviceId
  // 重置控制状态
  lightState.on = false
  lightState.colorTemperature = 3000
  lightState.brightness = 80
  wechatNotifyState.value = false
  autoScreenBrightness.value = false
  focusMode.value = false
  screenBrightness.value = 60
  loadControlLogs(deviceId)
  void fetchLatestSensorData(deviceId)
}

async function playLaunchTransition() {
  const payload = sessionStorage.getItem('tianmu:twin-transition')
  if (!payload) return

  sessionStorage.removeItem('tianmu:twin-transition')
  try {
    const parsed = JSON.parse(payload) as {
      deviceId: string
      rect: { left: number; top: number; width: number; height: number }
    }
    if (parsed.deviceId !== selectedDeviceId.value) return
    await nextTick()
    const targetRect = centralTwinRef.value?.getBoundingClientRect()
    if (!targetRect) return

    twinLaunchOverlay.value = {
      from: parsed.rect,
      to: {
        left: targetRect.left,
        top: targetRect.top,
        width: targetRect.width,
        height: targetRect.height,
      },
      settled: false,
    }
    requestAnimationFrame(() => {
      if (twinLaunchOverlay.value) twinLaunchOverlay.value.settled = true
    })
    window.setTimeout(() => {
      twinLaunchOverlay.value = null
    }, 780)
  } catch {
    twinLaunchOverlay.value = null
  }
}

function goBackToDashboard() {
  const rect = centralTwinRef.value?.getBoundingClientRect()
  if (rect && selectedDeviceId.value) {
    sessionStorage.setItem(
      'tianmu:twin-return',
      JSON.stringify({
        deviceId: selectedDeviceId.value,
        rect: {
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
        },
      }),
    )
  }
  router.push({ path: '/teen/dashboard', query: route.query.demo ? { demo: route.query.demo } : undefined })
}

/**
 * 获取设备列表
 */
async function fetchDevices() {
  try {
    const res = await getDeviceList()
    deviceStore.setDevices(res || [])
    subscribeDevices(res || [])
  } catch {
    // 忽略错误
  }
}

function subscribeDevices(devices = deviceStore.devices) {
  devices.forEach((device) => {
    if (device.device_id) {
      ws.send('subscribe', { device_id: device.device_id })
    }
  })
}

function applyRealtimeSensorData(data: Record<string, unknown>) {
  const deviceId = data.device_id as string
  if (!deviceId || deviceId !== selectedDeviceId.value) return
  latestSensorData.value = data as unknown as SensorData
  applyHardwareControlState(data)
}

function applyRealtimeHardwareState(data: Record<string, unknown>) {
  const deviceId = data.device_id as string
  if (!deviceId || deviceId !== selectedDeviceId.value) return
  applyHardwareControlState(data)
}

async function fetchLatestSensorData(deviceId: string) {
  if (!deviceId) {
    latestSensorData.value = null
    return
  }
  try {
    latestSensorData.value = await getLatestData(deviceId)
    applyHardwareControlState(latestSensorData.value)
  } catch {
    latestSensorData.value = null
  }
}

onMounted(async () => {
  ws.on('auth_result', () => {
    subscribeDevices()
  })
  ws.on('sensor_data', applyRealtimeSensorData)
  ws.on('device_heartbeat', applyRealtimeHardwareState)
  ws.connect()

  await fetchDevices()

  // 从路由 query 参数获取 deviceId（兼容旧链接）
  const queryDeviceId = route.query.deviceId as string
  if (queryDeviceId && deviceStore.devices.find((d) => d.device_id === queryDeviceId)) {
    selectedDeviceId.value = queryDeviceId
  } else if (deviceStore.devices.length > 0) {
    // 默认选中第一个设备
    selectedDeviceId.value = deviceStore.devices[0]?.device_id ?? ''
  }
  if (selectedDeviceId.value) {
    loadControlLogs(selectedDeviceId.value)
    await fetchLatestSensorData(selectedDeviceId.value)
  }
  sensorRefreshTimer = window.setInterval(() => {
    if (selectedDeviceId.value && isOnline.value) {
      void fetchLatestSensorData(selectedDeviceId.value)
    }
  }, 10000)
  await playLaunchTransition()
})

onUnmounted(() => {
  if (sensorRefreshTimer) window.clearInterval(sensorRefreshTimer)
})
</script>

<style scoped>
/* ========== Liquid Glass — CSS Custom Properties ========== */
.control-page {
  --glass-bg: linear-gradient(145deg, rgba(102, 198, 255, 0.075), rgba(5, 22, 49, 0.31));
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  --glass-inner-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15);
  --glass-radius: 20px;
  --glass-radius-sm: 14px;
  --glass-blur: blur(18px);
  --glass-saturation: saturate(1.6);
  --color-cube-primary: #06B6D4;
  --color-cube-accent: #A3E635;
  --text-primary: rgba(255, 255, 255, 0.92);
  --text-secondary: rgba(255, 255, 255, 0.60);
  --text-disabled: rgba(255, 255, 255, 0.30);

  display: flex;
  gap: 0;
  height: calc(100vh - 60px - 48px);
  margin: calc(-1 * var(--spacing-page));
  margin-top: calc(-1 * var(--spacing-page) + 0px);
}

/* ========== 左侧设备列表 — Glass Sidebar ========== */
.control-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--glass-bg);
  border-right: var(--glass-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturation);
}
.control-sidebar__title {
  padding: 18px 16px 12px;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.control-sidebar__list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 8px;
}

/* 设备列表项 — Glass List Items */
.device-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border-radius: var(--glass-radius-sm);
  cursor: pointer;
  transition:
    transform var(--transition-spring),
    background var(--transition-base),
    border-color var(--transition-base),
    color var(--transition-fast);
  margin-bottom: 6px;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}
.device-list-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.22);
  transform: translateX(3px);
}
.device-list-item--active {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.28);
  box-shadow: var(--glass-inner-shadow);
}
.device-list-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 9px;
  bottom: 9px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
}
.device-list-item--active .device-list-item__name {
  color: var(--color-cube-primary);
  font-weight: 500;
}
.device-list-item--offline {
  opacity: 0.5;
}
.device-list-item__name {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.device-list-empty {
  text-align: center;
  padding: 40px 16px;
  font-size: 13px;
  color: var(--text-disabled);
}

/* ========== 右侧控制区 ========== */
.control-main {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-page);
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: transparent;
}

/* 未选中设备 */
.control-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-disabled);
}
.control-empty__text {
  font-size: 15px;
}

/* 设备标题栏 — Glass Header */
.control-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  background: var(--glass-bg);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturation);
}
.control-header__info {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.control-header__name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.control-header__name::before {
  content: '';
  width: 4px;
  height: 22px;
  border-radius: var(--radius-full);
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
  box-shadow: 0 0 14px rgba(6, 182, 212, 0.45);
}
.control-header__id {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
}

/* 离线提示 — Glass Warning */
.control-offline-tip {
  position: absolute;
  top: 122px;
  left: 24px;
  right: 24px;
  z-index: 12;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.10);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: var(--glass-radius-sm);
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 500;
  backdrop-filter: blur(12px) saturate(1.4);
  -webkit-backdrop-filter: blur(12px) saturate(1.4);
  box-shadow: 0 12px 28px rgba(239, 68, 68, 0.08), var(--glass-inner-shadow);
}

/* ========== 控制面板网格 ========== */
.control-panels {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.control-panels--disabled {
  pointer-events: none;
  opacity: 0.5;
}

/* 单个控制面板 — Glass Card */
.control-panel {
  position: relative;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturation);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  overflow: hidden;
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  transition:
    transform var(--transition-spring),
    border-color var(--transition-base),
    box-shadow var(--transition-base),
    background var(--transition-base);
  animation: fade-up-blur 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
/* Top edge highlight — subtle white gradient line */
.control-panel::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.40),
    rgba(255, 255, 255, 0.12),
    transparent
  );
}
.control-panel:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.28);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.18),
    inset 0 1px 1px rgba(255, 255, 255, 0.20);
}
.control-panel:nth-child(2) { animation-delay: 60ms; }
.control-panel:nth-child(3) { animation-delay: 120ms; }
.control-panel:nth-child(4) { animation-delay: 180ms; }

.control-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.03);
}
.control-panel__title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.control-panel__status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.control-panel__subtitle {
  font-size: 12px;
  color: var(--text-disabled);
}

.control-panel__body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.control-panel__body--toggles {
  gap: 14px;
}

/* 滑块控制 — Glass Slider */
.slider-control {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--glass-radius-sm);
  background: rgba(255, 255, 255, 0.05);
}
.slider-control__label {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  flex-shrink: 0;
}
.slider-control__slider {
  flex: 1;
}
.slider-control__slider :deep(.el-slider__runway) {
  height: 4px;
}
.slider-control__slider :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
}
.slider-control__value {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 36px;
  text-align: right;
  flex-shrink: 0;
}

/* ========== 控制日志 — Glass Log ========== */
.log-empty {
  text-align: center;
  padding: 20px;
  font-size: 13px;
  color: var(--text-disabled);
}
.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.log-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--glass-radius-sm);
  font-size: 13px;
  transition:
    transform var(--transition-base),
    border-color var(--transition-base),
    background var(--transition-base);
}
.log-item:hover {
  transform: translateX(3px);
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.12);
}
.log-item__time {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.log-item__desc {
  flex: 1;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-item__tag {
  flex-shrink: 0;
}

/* ========== Element Plus 覆盖 ========== */
.control-panel :deep(.el-slider__runway) {
  background-color: rgba(255, 255, 255, 0.10);
}
.control-panel :deep(.el-slider__bar) {
  background: linear-gradient(90deg, var(--color-cube-primary), var(--color-cube-accent));
}
.control-panel :deep(.el-slider__button) {
  border-color: var(--color-cube-primary);
}

/* ========== Digital Twin Control Rebuild ========== */
.control-page {
  position: relative;
  min-height: calc(100vh - 60px - 48px);
  height: auto;
  margin: calc(-1 * var(--spacing-page));
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 44%, rgba(34, 211, 238, 0.16), transparent 38%),
    radial-gradient(circle at 68% 58%, rgba(163, 230, 53, 0.08), transparent 34%);
}

.control-back {
  position: absolute;
  top: 22px;
  left: 24px;
  z-index: 16;
  height: 38px;
  padding: 0 14px 0 11px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  font: 600 13px/1 var(--font-body);
  border: 1px solid rgba(216, 242, 255, 0.28);
  border-radius: 13px;
  background:
    linear-gradient(145deg, rgba(124, 211, 255, 0.14), rgba(9, 26, 55, 0.46)),
    rgba(255, 255, 255, 0.05);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  backdrop-filter: blur(28px) saturate(1.8);
  -webkit-backdrop-filter: blur(28px) saturate(1.8);
  cursor: pointer;
  transition:
    transform var(--transition-spring),
    border-color var(--transition-base),
    background var(--transition-base);
}

.control-back:hover {
  transform: translateX(-3px);
  border-color: rgba(226, 250, 255, 0.48);
  background: var(--glass-bg-hover);
}

.control-back__icon {
  width: 16px;
  height: 16px;
}

.control-air-stage {
  position: absolute;
  inset: 0;
  opacity: 0.8;
}

.control-titlebar {
  position: relative;
  z-index: 4;
  margin-left: 118px;
  min-height: 74px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 18px;
  border: 1px solid rgba(216, 242, 255, 0.2);
  border-radius: 22px;
  background:
    linear-gradient(120deg, rgba(94, 190, 255, 0.09), rgba(6, 22, 48, 0.34) 52%, rgba(163, 230, 53, 0.05)),
    rgba(255, 255, 255, 0.035);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  backdrop-filter: blur(30px) saturate(1.85);
  -webkit-backdrop-filter: blur(30px) saturate(1.85);
}

.control-titlebar__info {
  min-width: 220px;
}

.control-titlebar__eyebrow {
  display: block;
  margin-bottom: 3px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: rgba(163, 230, 53, 0.78);
}

.control-titlebar h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--text-primary);
}

.control-titlebar__info > span:last-child {
  display: block;
  margin-top: 3px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}

.control-titlebar__devices {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.device-chip {
  height: 32px;
  max-width: 168px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 11px;
  color: var(--text-secondary);
  border: 1px solid rgba(216, 242, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.device-chip span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-chip--active,
.device-chip:hover {
  color: var(--text-primary);
  border-color: rgba(163, 230, 53, 0.38);
  background: rgba(163, 230, 53, 0.1);
}

.control-stage {
  position: relative;
  z-index: 3;
  flex: 1;
  min-height: 540px;
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(320px, 1fr) minmax(280px, 360px);
  align-items: center;
  gap: 18px;
}

.control-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.control-twin-stage {
  position: relative;
  min-height: 460px;
  display: grid;
  place-items: center;
  opacity: 1;
  transition: opacity 220ms ease 560ms;
}

.control-twin-stage--hidden {
  opacity: 0;
}

.control-twin-stage::before {
  content: '';
  position: absolute;
  width: min(52vw, 560px);
  aspect-ratio: 1;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.15), transparent 60%),
    conic-gradient(from 120deg, transparent, rgba(163, 230, 53, 0.16), transparent, rgba(34, 211, 238, 0.14), transparent);
  filter: blur(1px);
  animation: twin-platform-turn 24s linear infinite;
}

.control-twin-stage__model {
  position: relative;
  z-index: 2;
  width: min(50vw, 560px);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
}

.control-twin-stage__model :deep(.digital-twin),
.control-twin-lite {
  width: 100%;
}

.control-twin-lite {
  position: relative;
  aspect-ratio: 1;
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

.control-panel {
  background:
    linear-gradient(145deg, rgba(102, 198, 255, 0.1), rgba(5, 22, 49, 0.36)),
    rgba(255, 255, 255, 0.035);
  border-color: rgba(216, 242, 255, 0.22);
}

.control-panel--compact .control-panel__body {
  padding: 14px;
}

.air-legend {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.air-legend__item {
  display: grid;
  grid-template-columns: 12px minmax(48px, auto) 1fr;
  align-items: center;
  gap: 8px;
  padding: 8px 9px;
  border: 1px solid rgba(216, 242, 255, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.045);
}

.air-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 12px currentColor;
}

.air-legend__label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-primary);
}

.air-legend__name {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
}

.twin-metrics {
  display: grid;
  gap: 8px;
}

.twin-metric {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(216, 242, 255, 0.12);
}

.twin-metric span {
  color: var(--text-secondary);
  font-size: 12px;
}

.twin-metric strong {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
}

.control-log-dock {
  position: relative;
  z-index: 4;
}

.control-log-dock .control-panel__body {
  padding: 12px 16px 16px;
}

.control-twin-launch {
  --twin-size: 100%;

  position: fixed;
  z-index: 999;
  pointer-events: none;
  transition:
    left 760ms cubic-bezier(0.2, 0.9, 0.18, 1),
    top 760ms cubic-bezier(0.2, 0.9, 0.18, 1),
    width 760ms cubic-bezier(0.2, 0.9, 0.18, 1),
    height 760ms cubic-bezier(0.2, 0.9, 0.18, 1),
    opacity 220ms ease 560ms,
    filter 760ms ease;
  filter: drop-shadow(0 24px 54px rgba(34, 211, 238, 0.26));
}

.control-twin-launch--settled {
  opacity: 0;
  filter: drop-shadow(0 10px 24px rgba(34, 211, 238, 0.1));
}

@keyframes twin-platform-turn {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 1180px) {
  .control-stage {
    grid-template-columns: 1fr;
  }

  .control-column--left,
  .control-column--right {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .control-titlebar {
    margin-left: 0;
    padding-left: 108px;
  }
}

@media (max-width: 760px) {
  .control-page {
    padding: 18px;
  }

  .control-back {
    position: relative;
    top: auto;
    left: auto;
    align-self: flex-start;
  }

  .control-titlebar {
    margin-left: 0;
    padding: 14px;
    flex-direction: column;
    align-items: stretch;
  }

  .control-titlebar__devices {
    justify-content: flex-start;
  }

  .control-column--left,
  .control-column--right {
    grid-template-columns: 1fr;
  }

  .control-twin-stage {
    min-height: 320px;
  }

  .control-twin-stage__model {
    width: min(78vw, 320px);
  }
}
</style>
