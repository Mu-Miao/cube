<template>
  <div
    class="sensor-card"
    :class="`sensor-card--${status}`"
    :style="{ '--sensor-color': resolvedColor }"
  >
    <!-- 头部：图标 + 标题 + 状态 -->
    <div class="sensor-card__header">
      <div class="sensor-card__title-group">
        <span
          class="sensor-card__icon-bg"
          :style="{ backgroundColor: iconTint }"
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
    normal: '#3B82F6',
    warning: '#F59E0B',
    danger: '#EF4444',
  }
  return colorMap[props.status] || '#3B82F6'
})

const iconTint = computed(() => {
  const tintMap: Record<string, string> = {
    normal: 'rgba(59, 130, 246, 0.16)',
    warning: 'rgba(245, 158, 11, 0.16)',
    danger: 'rgba(239, 68, 68, 0.16)',
  }
  return props.color ? `${props.color}22` : tintMap[props.status]
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
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.012)),
    var(--bg-card, rgba(15, 23, 42, 0.65));
  border: var(--border-glass, 1px solid rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, var(--radius-md, 12px));
  box-shadow: var(--shadow-card, var(--shadow-md, 0 4px 12px rgba(0, 0, 0, 0.35)));
  padding: 18px;
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
  animation: fade-up-blur 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
  cursor: default;
}

.sensor-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--sensor-color), transparent 76%);
  opacity: 0.9;
}

.sensor-card::after {
  content: '';
  position: absolute;
  inset: auto -18% -44% 46%;
  height: 112px;
  background: linear-gradient(135deg, transparent, color-mix(in srgb, var(--sensor-color) 20%, transparent), transparent);
  transform: rotate(-12deg);
  opacity: 0.55;
  pointer-events: none;
}

.sensor-card:hover {
  transform: translateY(-5px);
  border-color: color-mix(in srgb, var(--sensor-color) 36%, rgba(255, 255, 255, 0.12));
  box-shadow: 0 0 28px color-mix(in srgb, var(--sensor-color) 18%, transparent), var(--shadow-elevated, 0 10px 15px rgba(0, 0, 0, 0.3));
}

/* 头部 */
.sensor-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  position: relative;
  z-index: 1;
}

.sensor-card__title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sensor-card__icon-bg {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid color-mix(in srgb, var(--sensor-color) 24%, transparent);
  box-shadow: inset 0 0 16px color-mix(in srgb, var(--sensor-color) 10%, transparent);
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
  border: 1px solid rgba(255, 255, 255, 0.055);
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
  position: relative;
  z-index: 1;
}

.sensor-card__value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 36px;
  font-weight: 500;
  color: var(--text-primary, var(--text-main, #e8ecf4));
  line-height: 1.1;
  text-shadow: 0 0 18px color-mix(in srgb, var(--sensor-color) 18%, transparent);
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
  position: relative;
  z-index: 1;
  padding-top: 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.055);
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
