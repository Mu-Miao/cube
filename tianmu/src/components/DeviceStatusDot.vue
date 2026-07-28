<template>
  <div
    class="device-status-dot"
    :class="`device-status-dot--${status}`"
  />
</template>

<script setup lang="ts">
defineOptions({ name: 'DeviceStatusDot' })

defineProps<{
  status: 'online' | 'offline' | 'error'
}>()
</script>

<style scoped>
.device-status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full, 9999px);
  display: inline-block;
  flex-shrink: 0;
}

/* 在线：绿色 + 光晕 + 呼吸动画 */
.device-status-dot--online {
  background-color: var(--color-success, var(--status-online, #10b981));
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: status-dot-breathe 2s ease-in-out infinite;
}

/* 离线：红色，无光晕 */
.device-status-dot--offline {
  background-color: var(--color-danger, var(--status-danger, #ef4444));
}

/* 异常：黄色，无光晕 */
.device-status-dot--error {
  background-color: var(--color-warning, var(--status-warn, #f59e0b));
}

@keyframes status-dot-breathe {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  }
  50% {
    opacity: 0.6;
    box-shadow: 0 0 4px rgba(16, 185, 129, 0.3);
  }
}
</style>
