<template>
  <div class="control-toggle">
    <div class="control-toggle__label">{{ label }}</div>
    <el-switch
      :model-value="modelValue"
      :disabled="disabled || loading"
      :loading="loading"
      size="large"
      @update:model-value="emit('update:modelValue', $event)"
    />
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'ControlToggle' })

defineProps<{
  modelValue: boolean
  label: string
  disabled?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
</script>

<style scoped>
.control-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.045);
  border-radius: var(--radius-button, 6px);
  background: rgba(255, 255, 255, 0.026);
  transition:
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.control-toggle:hover {
  background: rgba(6, 182, 212, 0.045);
  border-color: rgba(6, 182, 212, 0.18);
}

.control-toggle__label {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, var(--text-main, #e8ecf4));
}

/* 自定义开关尺寸 44px x 24px */
.control-toggle :deep(.el-switch) {
  --el-switch-on-color: var(--color-cube-primary, var(--primary, #f59e0b));
  --el-switch-off-color: var(--bg-elevated, #151d35);
  height: 24px;
}

.control-toggle :deep(.el-switch__core) {
  min-width: 44px;
  height: 24px;
  border-radius: var(--radius-full, 9999px);
  transition: all 0.3s ease;
}

.control-toggle :deep(.el-switch__inner) {
  font-size: 0;
}

.control-toggle :deep(.el-switch__action) {
  width: 20px;
  height: 20px;
}

.control-toggle :deep(.el-switch.is-checked .el-switch__core) {
  background: linear-gradient(90deg, var(--color-cube-primary, var(--primary, #06b6d4)), var(--color-cube-accent, #a3e635)) !important;
  border-color: var(--color-cube-primary, var(--primary, #f59e0b)) !important;
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.25) !important;
}

.control-toggle :deep(.el-switch__core) {
  background-color: var(--bg-elevated, #151d35) !important;
  border-color: var(--border-subtle, rgba(51, 65, 102, 0.45)) !important;
}
</style>
