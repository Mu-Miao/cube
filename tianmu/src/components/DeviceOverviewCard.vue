<template>
  <div
    class="device-overview-card"
    :data-device-card="device.device_id"
    :class="{
      'device-overview-card--offline': isOffline,
      'device-overview-card--launching': launching,
      'device-overview-card--muted': muted,
      'device-overview-card--twin-hidden': twinHidden,
      'device-overview-card--refreshing': refreshing,
    }"
    @click="handleClick"
  >
    <CubeSpinGifPreview
      class="device-overview-card__twin"
      :label="device.device_name"
      :offline="isOffline"
      :style="transitionName ? { '--twin-transition-name': transitionName } : undefined"
    />

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
      <button
        class="device-overview-card__data-item"
        type="button"
        title="刷新温度数据"
        :disabled="refreshing"
        @click.stop="handleRefresh"
      >
        <span class="device-overview-card__data-label">TEMP</span>
        <span class="device-overview-card__data-value">
          {{ refreshing ? '刷新中' : (isOffline ? '--' : (temperature !== null ? temperature + '℃' : '--')) }}
        </span>
      </button>
      <button
        class="device-overview-card__data-item"
        type="button"
        title="刷新湿度数据"
        :disabled="refreshing"
        @click.stop="handleRefresh"
      >
        <span class="device-overview-card__data-label">HUM</span>
        <span class="device-overview-card__data-value">
          {{ refreshing ? '刷新中' : (isOffline ? '--' : (humidity !== null ? humidity + '% RH' : '--')) }}
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import DeviceStatusDot from './DeviceStatusDot.vue'
import CubeSpinGifPreview from '@/components/brand/CubeSpinGifPreview.vue'

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
  launching?: boolean
  muted?: boolean
  transitionName?: string
  twinHidden?: boolean
  refreshing?: boolean
}>()

const emit = defineEmits<{
  (e: 'click', device: DeviceInfo, rect: DOMRect): void
  (e: 'refresh-data', device: DeviceInfo): void
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

function handleClick(event: MouseEvent) {
  const target = event.currentTarget as HTMLElement
  const twin = target.querySelector('.digital-twin') as HTMLElement | null
  emit('click', props.device, (twin || target).getBoundingClientRect())
}

function handleRefresh() {
  emit('refresh-data', props.device)
}
</script>

<style scoped>
.device-overview-card {
  --glass-bg: linear-gradient(145deg, rgba(105, 200, 255, 0.085), rgba(5, 23, 52, 0.3));
  --glass-border: 1px solid rgba(188, 231, 255, 0.2);
  --glass-shadow: 0 18px 42px rgba(0, 3, 18, 0.2);
  --glass-inner-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3), inset 0 -1px 0 rgba(76, 115, 255, 0.12);
  --glass-radius: 20px;

  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: blur(24px) saturate(1.85);
  -webkit-backdrop-filter: blur(24px) saturate(1.85);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  padding: 16px;
  min-width: 240px;
  cursor: pointer;
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.device-overview-card__twin {
  float: left;
  margin: -4px 10px 4px -4px;
  view-transition-name: var(--twin-transition-name, none);
  contain: layout;
  transform-origin: 40% 36%;
  will-change: transform, opacity;
  transition:
    transform 640ms cubic-bezier(0.2, 0.9, 0.18, 1),
    opacity 360ms ease,
    filter 360ms ease;
  position: relative;
  z-index: 1;
}

/* Subtle top-edge highlight */
.device-overview-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.35) 20%,
    rgba(255, 255, 255, 0.12) 80%,
    transparent
  );
  opacity: 0.8;
}

/* Hover sheen — white light passing through glass */
.device-overview-card::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 50%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.06),
    transparent
  );
  transform: translateX(-160%) skewX(-14deg);
  transition: transform var(--transition-slow, 500ms cubic-bezier(0.4, 0, 0.2, 1));
  pointer-events: none;
}

.device-overview-card:hover {
  transform: translateY(-5px);
  background: linear-gradient(145deg, rgba(118, 211, 255, 0.14), rgba(11, 34, 72, 0.34));
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.16),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
}

.device-overview-card:hover::after {
  transform: translateX(230%) skewX(-14deg);
}

.device-overview-card--offline {
  opacity: 0.55;
}

.device-overview-card--muted {
  opacity: 0;
  transform: translateY(12px) scale(0.94);
  pointer-events: none;
}

.device-overview-card--launching {
  z-index: 5;
  border-color: rgba(226, 250, 255, 0.55);
  box-shadow:
    0 22px 70px rgba(0, 4, 18, 0.4),
    0 0 46px rgba(34, 211, 238, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.38);
}

.device-overview-card--launching .device-overview-card__twin {
  transform: translate(36px, -8px) scale(1.32);
}

.device-overview-card--twin-hidden .device-overview-card__twin {
  opacity: 0;
}

.device-overview-card--refreshing .device-overview-card__data-item {
  border-color: rgba(34, 211, 238, 0.22);
}

.device-overview-card__name {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary, #e8ecf4);
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
  color: var(--text-secondary, #8b95b0);
}

.device-overview-card__data {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  z-index: 1;
}

.device-overview-card__data-item {
  appearance: none;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 8px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: inherit;
  cursor: pointer;
  transition:
    background var(--transition-fast, 150ms ease),
    border-color var(--transition-fast, 150ms ease),
    transform var(--transition-fast, 150ms ease);
}

.device-overview-card__data-item:hover:not(:disabled) {
  background: rgba(34, 211, 238, 0.08);
  border-color: rgba(34, 211, 238, 0.24);
  transform: translateX(2px);
}

.device-overview-card__data-item:disabled {
  cursor: wait;
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
  color: var(--text-primary, #e8ecf4);
}

@media (max-width: 760px) {
  .device-overview-card {
    min-width: 200px;
  }

  .device-overview-card__twin {
    width: 60px;
  }

  .device-overview-card__name,
  .device-overview-card__id {
    padding-left: 0;
  }
}
</style>
