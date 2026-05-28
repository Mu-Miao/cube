<template>
  <div
    class="device-overview-card"
    :class="{ 'device-overview-card--offline': isOffline }"
    @click="emit('click', device)"
  >
    <!-- 设备名称 -->
    <div class="device-overview-card__name">{{ device.device_name }}</div>
    <div class="device-overview-card__id">{{ device.device_id }}</div>

    <!-- 状态 -->
    <div class="device-overview-card__status">
      <DeviceStatusDot :status="dotStatus" />
      <span class="device-overview-card__status-text">{{ statusText }}</span>
    </div>

    <!-- 传感器数据 -->
    <div class="device-overview-card__data">
      <div class="device-overview-card__data-item">
        <span class="device-overview-card__data-label">TEMP</span>
        <span class="device-overview-card__data-value">
          {{ isOffline ? '--' : (temperature !== null ? temperature + '℃' : '--') }}
        </span>
      </div>
      <div class="device-overview-card__data-item">
        <span class="device-overview-card__data-label">HUM</span>
        <span class="device-overview-card__data-value">
          {{ isOffline ? '--' : (humidity !== null ? humidity + '% RH' : '--') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DeviceStatusDot from './DeviceStatusDot.vue'

defineOptions({ name: 'DeviceOverviewCard' })

interface DeviceInfo {
  device_id: string
  device_name: string
  status: string
  last_seen: string | number
}

const props = defineProps<{
  device: DeviceInfo
  temperature: number | null
  humidity: number | null
}>()

const emit = defineEmits<{
  (e: 'click', device: DeviceInfo): void
}>()

const isOffline = computed(() => {
  return props.device.status === 'offline' || props.device.status === '0'
})

const dotStatus = computed<'online' | 'offline' | 'error'>(() => {
  if (isOffline.value) return 'offline'
  if (props.device.status === 'error') return 'error'
  return 'online'
})

const statusText = computed(() => {
  if (isOffline.value) return '离线'
  if (props.device.status === 'error') return '异常'
  return '在线'
})
</script>

<style scoped>
.device-overview-card {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.058), rgba(255, 255, 255, 0.012)),
    var(--bg-card, rgba(15, 23, 42, 0.65));
  border: var(--border-glass, 1px solid rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 16px;
  cursor: pointer;
  box-shadow: var(--shadow-card, 0 4px 12px rgba(0, 0, 0, 0.35));
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.device-overview-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-primary, #06b6d4), var(--color-cube-accent, #a3e635), transparent);
  opacity: 0.75;
}

.device-overview-card::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 42%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.09), transparent);
  transform: translateX(-150%) skewX(-14deg);
  transition: transform var(--transition-slow, 400ms cubic-bezier(0.4, 0, 0.2, 1));
  pointer-events: none;
}

.device-overview-card:hover {
  transform: translateY(-5px);
  border-color: rgba(6, 182, 212, 0.38);
  box-shadow: var(--shadow-holo, 0 0 28px rgba(6, 182, 212, 0.12));
}

.device-overview-card:hover::after {
  transform: translateX(230%) skewX(-14deg);
}

.device-overview-card--offline {
  opacity: 0.6;
}

.device-overview-card__name {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  z-index: 1;
}

.device-overview-card__id {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 10px;
  color: var(--text-disabled, #4b5563);
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  z-index: 1;
}

.device-overview-card__status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

.device-overview-card__status-text {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
}

.device-overview-card__data {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  z-index: 1;
}

.device-overview-card__data-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 8px;
  border-radius: var(--radius-button, 6px);
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.045);
}

.device-overview-card__data-label {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 10px;
  color: var(--text-disabled, #4b5563);
  letter-spacing: 0.5px;
}

.device-overview-card__data-value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, var(--text-main, #e8ecf4));
}
</style>
