<template>
  <div class="sensor-mini-card" :class="`sensor-mini-card--${status}`">
    <div class="sensor-mini-card__label">{{ label }}</div>
    <div class="sensor-mini-card__value-row">
      <span class="sensor-mini-card__value">{{ value }}</span>
      <span class="sensor-mini-card__unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'SensorMiniCard' })

withDefaults(defineProps<{
  label: string
  value: number | string
  unit: string
  status?: 'normal' | 'warning' | 'danger'
}>(), {
  status: 'normal',
})
</script>

<style scoped>
.sensor-mini-card {
  background: var(--bg-surface, var(--bg-card, rgba(15, 23, 42, 0.65)));
  border: 1px solid var(--border-default, var(--border-subtle, rgba(51, 65, 102, 0.45)));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 12px 14px;
  transition: all var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.sensor-mini-card:hover {
  border-color: var(--border-accent, rgba(245, 158, 11, 0.3));
}

.sensor-mini-card__label {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
  margin-bottom: 4px;
}

.sensor-mini-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.sensor-mini-card__value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 20px;
  font-weight: 400;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  line-height: 1.2;
}

.sensor-mini-card__unit {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
}

/* 状态变体 */
.sensor-mini-card--warning .sensor-mini-card__value {
  color: var(--color-warning, var(--status-warn, #f59e0b));
}

.sensor-mini-card--danger .sensor-mini-card__value {
  color: var(--color-danger, var(--status-danger, #ef4444));
}
</style>
