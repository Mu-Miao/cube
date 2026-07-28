<template>
  <button
    class="device-row"
    :class="{ 'device-row--large': size === 'large', 'device-row--offline': device.status === 'offline' }"
  >
    <img :src="device.status === 'online' ? '/online.png' : '/offline.png'" alt="" loading="lazy" decoding="async" />
    <span class="device-row__main">
      <strong>{{ device.name }}</strong>
      <small>{{ device.subtitle }}</small>
    </span>
    <span class="device-row__status">
      <i></i>{{ device.status === 'online' ? '在线' : '离线' }}
    </span>
    <span class="device-row__metric">{{ formatMetric(device.temperature) }} °C</span>
    <span class="device-row__metric">{{ formatMetric(device.humidity) }} %</span>
    <b>›</b>
  </button>
</template>

<script setup lang="ts">
import type { Device } from '@/versions/public/data/mockData'

withDefaults(
  defineProps<{
    device: Device
    size?: 'normal' | 'large'
  }>(),
  {
    size: 'normal',
  },
)

function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}
</script>
