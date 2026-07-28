<template>
  <Transition name="connection-fade">
    <div
      v-if="status === 'disconnected' || status === 'reconnected'"
      class="connection-status"
      :class="`connection-status--${status}`"
    >
      <span class="connection-status__icon">
        <template v-if="status === 'disconnected'">&#9888;</template>
        <template v-else>&#10003;</template>
      </span>
      <span class="connection-status__text">
        <template v-if="status === 'disconnected'">实时连接已断开，正在重连...</template>
        <template v-else>连接已恢复</template>
      </span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
defineOptions({ name: 'ConnectionStatus' })

defineProps<{
  status: 'connected' | 'disconnected' | 'reconnected'
}>()

// 当 status 为 'reconnected' 时，父组件需要在 2 秒后将其改为 'connected'
// 以实现"绿色小条闪现2秒"的效果
</script>

<style scoped>
.connection-status {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-body, 'Plus Jakarta Sans', sans-serif);
}

.connection-status--disconnected {
  background: rgba(245, 158, 11, 0.15);
  color: var(--status-warn, #f59e0b);
}

.connection-status--reconnected {
  background: rgba(16, 185, 129, 0.15);
  color: var(--status-online, #10b981);
}

.connection-status__icon {
  font-size: 14px;
  flex-shrink: 0;
}

.connection-status__text {
  white-space: nowrap;
}

/* fade-in / fade-out 过渡 */
.connection-fade-enter-active {
  transition: opacity 0.3s ease-out;
}
.connection-fade-leave-active {
  transition: opacity 0.3s ease-in;
}
.connection-fade-enter-from,
.connection-fade-leave-to {
  opacity: 0;
}
</style>
