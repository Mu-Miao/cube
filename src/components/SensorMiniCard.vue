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
  --glass-bg: linear-gradient(145deg, rgba(104, 199, 255, 0.065), rgba(4, 21, 46, 0.25));
  --glass-border: 1px solid rgba(188, 231, 255, 0.16);
  --glass-shadow: 0 15px 36px rgba(0, 3, 18, 0.17);
  --glass-inner-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24);
  --glass-radius: 14px;

  position: relative;
  overflow: hidden;
  background: var(--glass-bg);
  backdrop-filter: blur(22px) saturate(1.85);
  -webkit-backdrop-filter: blur(22px) saturate(1.85);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  padding: 12px 14px;
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

/* Subtle top-edge highlight */
.sensor-mini-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3) 25%,
    rgba(255, 255, 255, 0.1) 75%,
    transparent
  );
  opacity: 0.7;
}

.sensor-mini-card:hover {
  transform: translateY(-3px);
  background: linear-gradient(145deg, rgba(121, 210, 255, 0.12), rgba(10, 31, 66, 0.3));
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow:
    0 12px 36px rgba(0, 0, 0, 0.14),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
}

.sensor-mini-card__label {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, #8b95b0);
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
  color: var(--text-primary, #e8ecf4);
  line-height: 1.2;
}

.sensor-mini-card__unit {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  color: var(--text-secondary, #8b95b0);
}

/* Status variants */
.sensor-mini-card--warning .sensor-mini-card__value {
  color: var(--color-warning, #f59e0b);
}

.sensor-mini-card--danger .sensor-mini-card__value {
  color: var(--color-danger, #ef4444);
}
</style>
