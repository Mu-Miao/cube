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
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.012)),
    var(--bg-card, rgba(15, 23, 42, 0.65));
  border: var(--border-glass, 1px solid rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  padding: 12px 14px;
  box-shadow: var(--shadow-card, 0 4px 12px rgba(0, 0, 0, 0.35));
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.sensor-mini-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, rgba(6, 182, 212, 0.85), rgba(163, 230, 53, 0.5), transparent);
  opacity: 0.42;
}

.sensor-mini-card:hover {
  transform: translateY(-3px);
  border-color: rgba(6, 182, 212, 0.32);
  box-shadow: var(--shadow-holo, 0 0 28px rgba(6, 182, 212, 0.12));
}

.sensor-mini-card__label {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
  margin-bottom: 4px;
  position: relative;
  z-index: 1;
}

.sensor-mini-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  position: relative;
  z-index: 1;
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
