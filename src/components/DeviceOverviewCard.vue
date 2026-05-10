<template>
  <div
    class="device-overview-card"
    :class="{ 'device-overview-card--offline': isOffline }"
    @click="emit('click', device)"
  >
    <!-- 设备名称 -->
    <div class="device-overview-card__name">{{ device.device_name }}</div>

    <!-- 状态 -->
    <div class="device-overview-card__status">
      <DeviceStatusDot :status="dotStatus" />
      <span class="device-overview-card__status-text">{{ statusText }}</span>
    </div>

    <!-- 传感器数据 -->
    <div class="device-overview-card__data">
      <div class="device-overview-card__data-item">
        <span class="device-overview-card__data-value">
          {{ isOffline ? '--' : (temperature !== null ? temperature + '℃' : '--') }}
        </span>
      </div>
      <div class="device-overview-card__data-item">
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
  background: var(--bg-surface, var(--bg-card, rgba(15, 23, 42, 0.65)));
  border: 1px solid var(--border-default, var(--border-subtle, rgba(51, 65, 102, 0.45)));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 14px;
  cursor: pointer;
  transition: all var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.device-overview-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-accent, rgba(245, 158, 11, 0.3));
}

.device-overview-card--offline {
  opacity: 0.6;
}

.device-overview-card__name {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-overview-card__status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.device-overview-card__status-text {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
}

.device-overview-card__data {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-overview-card__data-item {
  display: flex;
  align-items: center;
}

.device-overview-card__data-value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 14px;
  color: var(--text-primary, var(--text-main, #e8ecf4));
}
</style>
