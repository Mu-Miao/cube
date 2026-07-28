<template>
  <article
    class="device-card"
    :class="{
      'device-card--offline': device.status === 'offline',
      'device-card--selected': selected,
    }"
  >
    <div class="device-card__name">{{ device.device_name }}</div>
    <div class="device-card__id">{{ device.device_id }}</div>
    <div class="device-card__info">
      <div class="device-card__status">
        <DeviceStatusDot :status="device.status" />
        <span :class="device.status === 'online' ? 'text-online' : 'text-offline'">
          {{ device.status === 'online' ? '在线' : '离线' }}
        </span>
      </div>
      <div class="device-card__chip">{{ device.chip_model || 'ESP32-S3' }}</div>
    </div>
    <div class="device-card__firmware">固件: {{ device.firmware_version || '-' }}</div>
    <div class="device-card__heartbeat">最后心跳: {{ formatRelativeTime(device.last_seen) }}</div>
    <div class="device-card__actions">
      <el-button size="small" :type="selected ? 'success' : 'primary'" @click="$emit('select')">
        {{ selected ? '✓ 已选中' : '选中' }}
      </el-button>
      <el-button size="small" @click="$emit('details')">查看详情</el-button>
      <el-button size="small" type="danger" plain @click="$emit('unbind')">解除绑定</el-button>
    </div>
  </article>
</template>

<script setup lang="ts">
import DeviceStatusDot from '@/components/DeviceStatusDot.vue'
import type { DeviceInfo } from '@/stores/device'

defineProps<{ device: DeviceInfo; selected: boolean }>()
defineEmits<{ select: []; details: []; unbind: [] }>()

function formatRelativeTime(timeStr: string): string {
  if (!timeStr) return '-'
  const diff = Date.now() - new Date(timeStr).getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}小时前`
  return `${Math.floor(diff / 86_400_000)}天前`
}
</script>

<style scoped>
.device-card {
  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  transition: transform var(--transition-spring), border-color var(--transition-base);
}
.device-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.4), transparent);
}
.device-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.28);
  transform: translateY(-5px);
}
.device-card--offline { opacity: 0.6; }
.device-card--selected {
  border-color: rgba(16, 185, 129, 0.45);
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.25), var(--glass-shadow);
}
.device-card__name { font-size: 16px; font-weight: 500; color: var(--text-primary); }
.device-card__id,
.device-card__firmware,
.device-card__heartbeat { font-size: 12px; color: var(--text-secondary); }
.device-card__id,
.device-card__chip { font-family: var(--font-mono); }
.device-card__info { display: flex; align-items: center; justify-content: space-between; }
.device-card__status { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.device-card__chip {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 3px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
}
.device-card__actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.device-card__actions :deep(.el-button--danger) {
  --el-button-text-color: #fff;
  --el-button-hover-text-color: #fff;
}
</style>
