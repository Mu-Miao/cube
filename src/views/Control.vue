<!-- Control.vue -->
<!-- 控制面板页 -->
<!-- 左侧设备列表 + 右侧控制区（灯光/继电器/蜂鸣器/系统控制/日志） -->
<!-- 设备离线时所有控件置灰，禁止操作 -->
<template>
  <div class="control-page">
    <!-- 左侧设备列表 -->
    <aside class="control-sidebar">
      <div class="control-sidebar__title">设备列表</div>
      <div class="control-sidebar__list">
        <div
          v-for="device in deviceStore.devices"
          :key="device.device_id"
          class="device-list-item"
          :class="{
            'device-list-item--active': selectedDeviceId === device.device_id,
            'device-list-item--offline': device.status === 'offline',
          }"
          @click="selectDevice(device.device_id)"
        >
          <DeviceStatusDot :status="device.status" />
          <span class="device-list-item__name">{{ device.device_name }}</span>
        </div>
        <!-- 无设备 -->
        <div v-if="deviceStore.devices.length === 0" class="device-list-empty">
          暂无设备
        </div>
      </div>
    </aside>

    <!-- 右侧控制区 -->
    <main class="control-main">
      <!-- 未选中设备 -->
      <div v-if="!currentDevice" class="control-empty">
        <el-icon :size="48" color="var(--text-disabled)"><Monitor /></el-icon>
        <div class="control-empty__text">请从左侧选择一个设备</div>
      </div>

      <!-- 已选中设备 -->
      <template v-else>
        <!-- 设备标题栏 -->
        <div class="control-header">
          <div class="control-header__info">
            <h2 class="control-header__name">{{ currentDevice.device_name }}</h2>
            <span class="control-header__id">{{ currentDevice.device_id }}</span>
          </div>
          <el-tag
            :type="isOnline ? 'success' : 'danger'"
            effect="dark"
            size="small"
          >
            {{ isOnline ? '在线' : '离线' }}
          </el-tag>
        </div>

        <!-- 离线提示 -->
        <div v-if="!isOnline" class="control-offline-tip">
          <el-icon :size="16"><WarningFilled /></el-icon>
          <span>设备已离线，无法控制</span>
        </div>

        <!-- 控制面板网格 -->
        <div class="control-panels" :class="{ 'control-panels--disabled': !isOnline }">
          <!-- 灯光控制面板 -->
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
                v-model="lightState"
                :disabled="!isOnline"
              />
            </div>
          </div>

          <!-- 继电器与蜂鸣器面板 -->
          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">继电器与蜂鸣器</span>
            </div>
            <div class="control-panel__body control-panel__body--toggles">
              <ControlToggle
                v-model="relayState.relay_1"
                label="继电器1 (主灯)"
                :disabled="!isOnline"
                :loading="toggleLoading.relay_1"
              />
              <ControlToggle
                v-model="relayState.relay_2"
                label="继电器2 (备用)"
                :disabled="!isOnline"
                :loading="toggleLoading.relay_2"
              />
              <ControlToggle
                v-model="buzzerState"
                label="蜂鸣器 (报警)"
                :disabled="!isOnline"
                :loading="toggleLoading.buzzer"
              />
            </div>
          </div>

          <!-- 系统控制面板 -->
          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">系统控制</span>
            </div>
            <div class="control-panel__body">
              <ControlToggle
                v-model="focusMode"
                label="专注模式"
                :disabled="!isOnline"
                :loading="toggleLoading.focus_mode"
              />
              <div class="slider-control">
                <span class="slider-control__label">屏幕亮度</span>
                <div class="slider-control__slider">
                  <el-slider
                    v-model="screenBrightness"
                    :min="0"
                    :max="100"
                    :disabled="!isOnline"
                    :show-tooltip="true"
                    @change="handleScreenBrightnessChange"
                  />
                </div>
                <span class="slider-control__value">{{ screenBrightness }}%</span>
              </div>
            </div>
          </div>

          <!-- 控制日志面板 -->
          <div class="control-panel">
            <div class="control-panel__header">
              <span class="control-panel__title">控制日志</span>
              <span class="control-panel__subtitle">最近 {{ maxLogs }} 条</span>
            </div>
            <div class="control-panel__body">
              <div v-if="controlLogs.length === 0" class="log-empty">暂无操作记录</div>
              <div v-else class="log-list">
                <div
                  v-for="log in controlLogs"
                  :key="log.id"
                  class="log-item"
                >
                  <span class="log-item__time">{{ log.time }}</span>
                  <span class="log-item__desc">{{ log.description }}</span>
                  <el-tag
                    :type="log.status === 'success' ? 'success' : 'danger'"
                    size="small"
                    effect="plain"
                    class="log-item__tag"
                  >
                    {{ log.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Monitor, WarningFilled } from '@element-plus/icons-vue'
import DeviceStatusDot from '@/components/DeviceStatusDot.vue'
import LightColorPicker from '@/components/LightColorPicker.vue'
import ControlToggle from '@/components/ControlToggle.vue'
import { useDeviceStore } from '@/store/device'
import { sendControlCommand } from '@/api/device'
import { getDeviceList } from '@/api/device'
defineOptions({ name: 'ControlPage' })

const route = useRoute()
const deviceStore = useDeviceStore()

// 当前选中的设备 ID
const selectedDeviceId = ref('')

// 最大日志条数
const maxLogs = 5

// 当前设备对象
const currentDevice = computed(() => {
  return deviceStore.devices.find((d) => d.device_id === selectedDeviceId.value) || null
})

// 设备是否在线
const isOnline = computed(() => {
  return currentDevice.value?.status === 'online'
})

// === 灯光状态 ===
interface LightValue {
  on: boolean
  color: string
  brightness: number
}
const lightState = reactive<LightValue>({
  on: false,
  color: '#FFFFFF',
  brightness: 80,
})

// === 继电器状态 ===
const relayState = reactive({
  relay_1: false,
  relay_2: false,
})

// === 蜂鸣器状态 ===
const buzzerState = ref(false)

// === 系统控制 ===
const focusMode = ref(false)
const screenBrightness = ref(60)

// === Toggle 加载状态 ===
const toggleLoading = reactive({
  relay_1: false,
  relay_2: false,
  buzzer: false,
  focus_mode: false,
})

// === 控制日志 ===
interface ControlLog {
  id: number
  time: string
  description: string
  status: 'success' | 'error'
}
const controlLogs = ref<ControlLog[]>([])
let logIdCounter = 0

/**
 * 添加控制日志
 */
function addLog(description: string, status: 'success' | 'error') {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  controlLogs.value.unshift({
    id: ++logIdCounter,
    time,
    description,
    status,
  })
  if (controlLogs.value.length > maxLogs) {
    controlLogs.value = controlLogs.value.slice(0, maxLogs)
  }
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

/**
 * 颜色名称映射
 */
function colorName(hex: string): string {
  const map: Record<string, string> = {
    '#FFFFFF': '白',
    '#EF4444': '红',
    '#10B981': '绿',
    '#3B82F6': '蓝',
  }
  return map[hex] || hex
}

// === 灯光控制监听 ===
watch(() => lightState.on, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  const command = newVal ? 'on' : 'off'
  const ok = await sendCommand('light', command)
  addLog(`${newVal ? '开启' : '关闭'}灯光`, ok ? 'success' : 'error')
})

watch(() => lightState.color, async (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  const ok = await sendCommand('light_color', newVal)
  addLog(`灯光颜色 -> ${colorName(newVal)}`, ok ? 'success' : 'error')
})

watch(() => lightState.brightness, async (newVal, oldVal) => {
  if (newVal === oldVal || !lightState.on) return
  const ok = await sendCommand('light_brightness', String(newVal))
  addLog(`灯光亮度 -> ${newVal}%`, ok ? 'success' : 'error')
})

// === 继电器控制监听 ===
watch(() => relayState.relay_1, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  toggleLoading.relay_1 = true
  const ok = await sendCommand('relay_1', newVal ? 'on' : 'off')
  addLog(`继电器1(主灯) -> ${newVal ? 'ON' : 'OFF'}`, ok ? 'success' : 'error')
  toggleLoading.relay_1 = false
})

watch(() => relayState.relay_2, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  toggleLoading.relay_2 = true
  const ok = await sendCommand('relay_2', newVal ? 'on' : 'off')
  addLog(`继电器2(备用) -> ${newVal ? 'ON' : 'OFF'}`, ok ? 'success' : 'error')
  toggleLoading.relay_2 = false
})

// === 蜂鸣器控制监听 ===
watch(buzzerState, async (newVal, oldVal) => {
  if (newVal === oldVal) return
  toggleLoading.buzzer = true
  const ok = await sendCommand('buzzer', newVal ? 'on' : 'off')
  addLog(`${newVal ? '开启' : '关闭'}蜂鸣器`, ok ? 'success' : 'error')
  toggleLoading.buzzer = false
})

// === 专注模式控制监听 ===
watch(focusMode, async (newVal, oldVal) => {
  if (newVal === oldVal) return
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
  lightState.color = '#FFFFFF'
  lightState.brightness = 80
  relayState.relay_1 = false
  relayState.relay_2 = false
  buzzerState.value = false
  focusMode.value = false
  screenBrightness.value = 60
  controlLogs.value = []
}

/**
 * 获取设备列表
 */
async function fetchDevices() {
  try {
    const res = await getDeviceList()
    deviceStore.setDevices(res || [])
  } catch {
    // 忽略错误
  }
}

onMounted(async () => {
  await fetchDevices()

  // 从路由 query 参数获取 deviceId（兼容旧链接）
  const queryDeviceId = route.query.deviceId as string
  if (queryDeviceId && deviceStore.devices.find((d) => d.device_id === queryDeviceId)) {
    selectedDeviceId.value = queryDeviceId
  } else if (deviceStore.devices.length > 0) {
    // 默认选中第一个设备
    selectedDeviceId.value = deviceStore.devices[0]?.device_id ?? ''
  }
})
</script>

<style scoped>
.control-page {
  display: flex;
  gap: 0;
  height: calc(100vh - 56px - 48px); /* 减去顶栏和 padding */
  margin: calc(-1 * var(--spacing-page));
  margin-top: calc(-1 * var(--spacing-page) + 0px);
}

/* ========== 左侧设备列表 ========== */
.control-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-surface);
  border-right: var(--border-default);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.control-sidebar__title {
  padding: 16px 16px 12px;
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

/* 设备列表项 */
.device-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 2px;
  border-left: 3px solid transparent;
}
.device-list-item:hover {
  background: var(--bg-hover);
}
.device-list-item--active {
  background: rgba(6, 182, 212, 0.08);
  border-left-color: var(--color-cube-primary);
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

/* 设备标题栏 */
.control-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
}
.control-header__id {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
}

/* 离线提示 */
.control-offline-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--color-danger-dim);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-button);
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 500;
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

/* 单个控制面板 */
.control-panel {
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: var(--border-default);
  border-radius: var(--radius-card);
  overflow: hidden;
  animation: fade-up-blur 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.control-panel:nth-child(2) { animation-delay: 60ms; }
.control-panel:nth-child(3) { animation-delay: 120ms; }
.control-panel:nth-child(4) { animation-delay: 180ms; }

.control-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: var(--border-default);
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

/* 滑块控制 */
.slider-control {
  display: flex;
  align-items: center;
  gap: 12px;
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

/* ========== 控制日志 ========== */
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
  background: var(--bg-elevated);
  border-radius: var(--radius-button);
  font-size: 13px;
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
  background-color: var(--bg-elevated);
}
.control-panel :deep(.el-slider__bar) {
  background-color: var(--color-cube-primary);
}
.control-panel :deep(.el-slider__button) {
  border-color: var(--color-cube-primary);
}
</style>
