<template>
  <Teleport to="body">
    <Transition name="alert-slide-down">
      <div v-if="visible" class="gas-alert-banner">
        <div class="gas-alert-banner__content">
          <span class="gas-alert-banner__icon">&#9888;&#65039;</span>
          <span class="gas-alert-banner__text">
            检测到燃气泄漏！设备：{{ deviceName }}
          </span>
          <button class="gas-alert-banner__btn" @click="handleViewDetail">
            查看详情
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineOptions({ name: 'GasAlertBanner' })

const props = defineProps<{
  visible: boolean
  deviceName: string
  deviceId: string
}>()

const emit = defineEmits<{
  (e: 'view-detail', deviceId: string): void
}>()

function handleViewDetail() {
  emit('view-detail', props.deviceId)
}
</script>

<style scoped>
.gas-alert-banner {
  position: fixed;
  top: 0;
  left: 236px;
  right: 0;
  z-index: 2000;
  height: 40px;
  background: linear-gradient(90deg, #DC2626, #EF4444);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 12px rgba(220, 38, 38, 0.3);
}

.gas-alert-banner__content {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: 100%;
  padding: 0 20px;
}

.gas-alert-banner__icon {
  font-size: 16px;
  flex-shrink: 0;
}

.gas-alert-banner__text {
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-body, 'Plus Jakarta Sans', sans-serif);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gas-alert-banner__btn {
  flex-shrink: 0;
  padding: 4px 14px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-xs, 4px);
  background: transparent;
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
  font-family: var(--font-body, 'Plus Jakarta Sans', sans-serif);
  cursor: pointer;
  transition: all var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1));
  white-space: nowrap;
}

.gas-alert-banner__btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: #ffffff;
}

/* 进场动画 */
.alert-slide-down-enter-active {
  transition: transform 0.3s ease-out;
}
.alert-slide-down-leave-active {
  transition: transform 0.3s ease-in;
}
.alert-slide-down-enter-from {
  transform: translateY(-100%);
}
.alert-slide-down-leave-to {
  transform: translateY(-100%);
}

@media (max-width: 860px) {
  .gas-alert-banner {
    left: 78px;
  }
}
</style>
