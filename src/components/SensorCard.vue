<template>
  <div class="sensor-card" :class="`sensor-card--${status}`">
    <!-- 头部：图标 + 标题 + 状态 -->
    <div class="sensor-card__header">
      <div class="sensor-card__title-group">
        <span
          class="sensor-card__icon-bg"
          :style="{ backgroundColor: `${resolvedColor}20` }"
        >
          <span class="sensor-card__icon" :style="{ color: resolvedColor }">
            {{ icon }}
          </span>
        </span>
        <span class="sensor-card__title">{{ title }}</span>
      </div>
      <span class="sensor-card__status" :class="`sensor-card__status--${status}`">
        {{ statusText }}
      </span>
    </div>

    <!-- 数值区域 -->
    <div class="sensor-card__value-area">
      <span class="sensor-card__value">{{ value }}</span>
      <span class="sensor-card__unit">{{ unit }}</span>
    </div>

    <!-- 迷你趋势线 -->
    <div v-if="trendData && trendData.length > 1" class="sensor-card__trend">
      <svg
        class="sensor-card__trend-svg"
        :viewBox="`0 0 ${trendData.length - 1} 32`"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" :stop-color="resolvedColor" stop-opacity="0.4" />
            <stop offset="100%" :stop-color="resolvedColor" stop-opacity="0.02" />
          </linearGradient>
        </defs>
        <!-- 渐变填充区域 -->
        <polygon
          :points="areaPoints"
          :fill="`url(#${gradientId})`"
        />
        <!-- 趋势线 -->
        <polyline
          :points="linePoints"
          fill="none"
          :stroke="resolvedColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

defineOptions({ name: 'SensorCard' })

const props = withDefaults(defineProps<{
  title: string
  value: number | string
  unit: string
  icon: string
  status?: 'normal' | 'warning' | 'danger'
  trendData?: number[]
  color?: string
}>(), {
  status: 'normal',
  trendData: () => [],
  color: '',
})

// 生成唯一 gradient ID
const gradientId = computed(() => `sensor-trend-${Math.random().toString(36).slice(2, 8)}`)

// 解析主题色
const resolvedColor = computed(() => {
  if (props.color) return props.color
  const colorMap: Record<string, string> = {
    normal: 'var(--color-info, var(--status-info, #3b82f6))',
    warning: 'var(--color-warning, var(--status-warn, #f59e0b))',
    danger: 'var(--color-danger, var(--status-danger, #ef4444))',
  }
  return colorMap[props.status] || 'var(--color-info, var(--status-info, #3b82f6))'
})

// 状态文字
const statusText = computed(() => {
  const map: Record<string, string> = {
    normal: '正常',
    warning: '警告',
    danger: '危险',
  }
  return map[props.status] || '正常'
})

// 计算趋势线 SVG 点
const linePoints = computed(() => {
  if (!props.trendData || props.trendData.length < 2) return ''
  const data = props.trendData
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const width = data.length - 1
  const height = 32
  const padding = 2

  return data
    .map((v, i) => {
      const x = i
      const y = height - padding - ((v - min) / range) * (height - padding * 2)
      return `${x},${y}`
    })
    .join(' ')
})

// 计算填充区域 SVG 点
const areaPoints = computed(() => {
  if (!linePoints.value) return ''
  const data = props.trendData!
  const width = data.length - 1
  return `0,32 ${linePoints.value} ${width},32`
})
</script>

<style scoped>
.sensor-card {
  background: var(--bg-surface, var(--bg-card, rgba(15, 23, 42, 0.65)));
  border: 1px solid var(--border-default, var(--border-subtle, rgba(51, 65, 102, 0.45)));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  box-shadow: var(--shadow-card, var(--shadow-md, 0 4px 12px rgba(0, 0, 0, 0.35)));
  padding: 16px;
  transition: all var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
  animation: fade-up-blur 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  cursor: default;
}

.sensor-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-accent, rgba(245, 158, 11, 0.3));
}

/* 头部 */
.sensor-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.sensor-card__title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sensor-card__icon-bg {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-xs, 4px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sensor-card__icon {
  font-size: 14px;
  line-height: 1;
}

.sensor-card__title {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
}

/* 状态标签 */
.sensor-card__status {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: var(--radius-xs, 4px);
}

.sensor-card__status--normal {
  color: var(--color-success, var(--status-online, #10b981));
  background: rgba(16, 185, 129, 0.12);
}

.sensor-card__status--warning {
  color: var(--color-warning, var(--status-warn, #f59e0b));
  background: rgba(245, 158, 11, 0.12);
}

.sensor-card__status--danger {
  color: var(--color-danger, var(--status-danger, #ef4444));
  background: rgba(239, 68, 68, 0.12);
}

/* 数值区域 */
.sensor-card__value-area {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}

.sensor-card__value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 36px;
  font-weight: 500;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  line-height: 1.1;
}

.sensor-card__unit {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 14px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
}

/* 迷你趋势线 */
.sensor-card__trend {
  height: 32px;
  width: 100%;
}

.sensor-card__trend-svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* 进场动画 */
@keyframes fade-up-blur {
  from {
    opacity: 0;
    transform: translateY(12px);
    filter: blur(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}
</style>
