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
              <ControlToggle
                :model-value="focusMode"
                label="专注模式"
                :disabled="!isOnline"
                :loading="toggleLoading.focus_mode"
                @update:model-value="handleFocusModeChange"
              />
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

      <ControlLogDock :logs="controlLogs" :max-logs="maxLogs" />
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
import ControlLogDock from '@/components/control/ControlLogDock.vue'
import { useDeviceStore } from '@/stores/device'
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
let sensorRefreshTimer: number | undefined
const ws = useWebSocket('/ws')
let syncingHardwareState = false
let colorTemperatureTimer: number | undefined
let lightBrightnessTimer: number | undefined
let twinAnimationFrame: number | undefined
let twinAnimationTimer: number | undefined
const FOCUS_CONFIRM_TIMEOUT_MS = 15_000
const SLIDER_COMMAND_DEBOUNCE_MS = 350
let pendingFocusMode: { value: boolean; expiresAt: number } | null = null

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
  if (typeof data.focus_mode === 'boolean') {
    const hardwareFocusMode = data.focus_mode
    if (pendingFocusMode) {
      if (hardwareFocusMode === pendingFocusMode.value) {
        pendingFocusMode = null
        focusMode.value = hardwareFocusMode
      } else if (Date.now() >= pendingFocusMode.expiresAt) {
        pendingFocusMode = null
        focusMode.value = hardwareFocusMode
      }
    } else {
      focusMode.value = hardwareFocusMode
    }
  }

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
  if (!newVal) {
    if (colorTemperatureTimer) window.clearTimeout(colorTemperatureTimer)
    if (lightBrightnessTimer) window.clearTimeout(lightBrightnessTimer)
  }
  toggleLoading.light = true
  const command = newVal ? 'on' : 'off'
  const ok = await sendCommand('light', command)
  addLog(`${newVal ? '开启' : '关闭'}灯光`, ok ? 'success' : 'error')
  toggleLoading.light = false
})

watch(() => lightState.colorTemperature, (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  if (syncingHardwareState) return
  if (colorTemperatureTimer) window.clearTimeout(colorTemperatureTimer)
  colorTemperatureTimer = window.setTimeout(async () => {
    colorTemperatureTimer = undefined
    if (!lightState.on || syncingHardwareState) return
    const ok = await sendCommand('color_temperature', String(newVal))
    addLog(`色温 -> ${newVal}K`, ok ? 'success' : 'error')
  }, SLIDER_COMMAND_DEBOUNCE_MS)
})

watch(() => lightState.brightness, (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  if (syncingHardwareState) return
  if (lightBrightnessTimer) window.clearTimeout(lightBrightnessTimer)
  lightBrightnessTimer = window.setTimeout(async () => {
    lightBrightnessTimer = undefined
    if (!lightState.on || syncingHardwareState) return
    const ok = await sendCommand('light_brightness', String(newVal))
    addLog(`灯光亮度 -> ${newVal}%`, ok ? 'success' : 'error')
  }, SLIDER_COMMAND_DEBOUNCE_MS)
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

// === 专注模式控制 ===
async function handleFocusModeChange(newVal: boolean) {
  if (toggleLoading.focus_mode || !isOnline.value) return
  const previousValue = focusMode.value
  focusMode.value = newVal
  pendingFocusMode = {
    value: newVal,
    expiresAt: Date.now() + FOCUS_CONFIRM_TIMEOUT_MS,
  }
  toggleLoading.focus_mode = true
  const ok = await sendCommand('focus_mode', newVal ? 'on' : 'off')
  if (!ok) {
    pendingFocusMode = null
    focusMode.value = previousValue
  }
  addLog(`专注模式 -> ${newVal ? 'ON' : 'OFF'}`, ok ? 'success' : 'error')
  toggleLoading.focus_mode = false
}

// === 屏幕亮度 ===
async function handleScreenBrightnessChange(val: number) {
  const ok = await sendCommand('screen_brightness', String(val))
  addLog(`屏幕亮度 -> ${val}%`, ok ? 'success' : 'error')
}

/**
 * 选择设备
 */
function selectDevice(deviceId: string) {
  syncingHardwareState = true
  selectedDeviceId.value = deviceId
  pendingFocusMode = null
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
  nextTick(() => {
    syncingHardwareState = false
  })
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
    twinAnimationFrame = requestAnimationFrame(() => {
      if (twinLaunchOverlay.value) twinLaunchOverlay.value.settled = true
    })
    twinAnimationTimer = window.setTimeout(() => {
      twinAnimationTimer = undefined
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
  const demo = route.query.demo
  const normalizedDemo = typeof demo === 'string' ? demo : undefined
  router.push(normalizedDemo ? { path: '/teen/dashboard', query: { demo: normalizedDemo } } : { path: '/teen/dashboard' })
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
  if (colorTemperatureTimer) window.clearTimeout(colorTemperatureTimer)
  if (lightBrightnessTimer) window.clearTimeout(lightBrightnessTimer)
  if (twinAnimationFrame) window.cancelAnimationFrame(twinAnimationFrame)
  if (twinAnimationTimer) window.clearTimeout(twinAnimationTimer)
})
</script>

<style scoped src="./styles/Control.css"></style>
