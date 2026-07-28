<template>
  <aside
    class="mascot-companion"
    :class="[
      `mascot-companion--${tone}`,
      `mascot-companion--state-${state}`,
      { 'mascot-companion--compact': compact },
    ]"
  >
    <div class="mascot-companion__aura" />
    <div class="mascot-companion__image-wrap">
      <img class="mascot-companion__image" :src="currentImage" :alt="`${title} 吉祥物`" loading="lazy" decoding="async" />
    </div>
    <div class="mascot-companion__content">
      <div class="mascot-companion__status">
        <span class="mascot-companion__pulse" />
        <span>{{ statusLabel }}</span>
      </div>
      <h3 class="mascot-companion__title">{{ title }}</h3>
      <p class="mascot-companion__message">{{ currentMessage }}</p>
      <div v-if="metrics.length" class="mascot-companion__metrics">
        <div v-for="metric in metrics" :key="metric.label" class="mascot-companion__metric">
          <span class="mascot-companion__metric-value">{{ metric.value }}</span>
          <span class="mascot-companion__metric-label">{{ metric.label }}</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import roleCelebrate from '@/assets/mascot/role_celebrate.webp'
import roleFocus from '@/assets/mascot/role_focus.webp'
import roleNormal from '@/assets/mascot/role_normal.webp'
import roleRemind from '@/assets/mascot/role_remind.webp'

defineOptions({ name: 'MascotCompanion' })

type MascotState = 'boot' | 'normal' | 'focus' | 'celebrate' | 'remind'

const props = withDefaults(
  defineProps<{
    compact?: boolean
    message?: string
    metrics?: Array<{ label: string; value: string | number }>
    state?: MascotState
    title?: string
  }>(),
  {
    compact: false,
    message: '',
    metrics: () => [],
    state: 'normal',
    title: '小眠',
  },
)

const stateMap: Record<
  MascotState,
  {
    image: string
    label: string
    message: string
    tone: 'calm' | 'focus' | 'good' | 'warn'
  }
> = {
  boot: {
    image: '/boot_sleep.gif',
    label: '启动中',
    message: '正在连接桌面魔方。',
    tone: 'calm',
  },
  normal: {
    image: roleNormal,
    label: '在线陪伴',
    message: '你的桌面魔方运行平稳。',
    tone: 'calm',
  },
  focus: {
    image: roleFocus,
    label: '专注守护',
    message: '专注模式已开启，环境保持安静。',
    tone: 'focus',
  },
  celebrate: {
    image: roleCelebrate,
    label: '状态优秀',
    message: '空气和设备状态都很漂亮。',
    tone: 'good',
  },
  remind: {
    image: roleRemind,
    label: '轻提醒',
    message: '有几项指标值得留意一下。',
    tone: 'warn',
  },
}

const currentConfig = computed(() => stateMap[props.state] ?? stateMap.normal)
const currentImage = computed(() => currentConfig.value.image)
const currentMessage = computed(() => props.message || currentConfig.value.message)
const statusLabel = computed(() => currentConfig.value.label)
const tone = computed(() => currentConfig.value.tone)
</script>

<style scoped>
.mascot-companion {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(156px, 0.86fr) minmax(220px, 1fr);
  align-items: center;
  gap: 18px;
  min-height: 236px;
  padding: 18px 20px;
  border: 1px solid rgba(190, 232, 255, 0.24);
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(118, 207, 255, 0.08), rgba(5, 22, 49, 0.2) 52%, rgba(127, 83, 255, 0.07));
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(26px) saturate(1.9);
  -webkit-backdrop-filter: blur(26px) saturate(1.9);
}

/* 顶部高光弧线 — 模拟光线在玻璃表面的折射 */
.mascot-companion::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg,
    transparent 5%,
    rgba(255, 255, 255, 0.3) 25%,
    rgba(255, 255, 255, 0.45) 50%,
    rgba(255, 255, 255, 0.3) 75%,
    transparent 95%
  );
  opacity: 0.7;
}

.mascot-companion__aura {
  position: absolute;
  left: 12px;
  top: 50%;
  width: 240px;
  height: 240px;
  transform: translateY(-50%);
  border-radius: 999px;
  background:
    radial-gradient(circle, rgba(255, 255, 255, 0.12), transparent 28%),
    conic-gradient(
      from 130deg,
      rgba(34, 211, 238, 0.2),
      rgba(163, 230, 53, 0.12),
      rgba(167, 139, 250, 0.14),
      rgba(34, 211, 238, 0.2)
    );
  filter: blur(24px);
  opacity: 0.35;
  animation: mascot-aura 9s linear infinite;
}

.mascot-companion__image-wrap {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: end center;
  min-height: 198px;
  overflow: hidden;
  border-radius: 28px;
  isolation: isolate;
}

.mascot-companion__image-wrap::after {
  content: '';
  position: absolute;
  right: 14%;
  bottom: 6px;
  width: 56%;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.2);
  filter: blur(10px);
}

.mascot-companion__image {
  position: relative;
  z-index: 1;
  width: min(190px, 100%);
  max-height: 214px;
  object-fit: contain;
  filter: drop-shadow(0 16px 20px rgba(0, 0, 0, 0.2))
    drop-shadow(0 0 12px rgba(255, 255, 255, 0.08));
  transform-origin: 50% 86%;
  animation: mascot-float 4.6s ease-in-out infinite;
}

.mascot-companion--state-boot .mascot-companion__image-wrap {
  place-items: center;
  background:
    radial-gradient(circle at 50% 44%, rgba(236, 253, 255, 0.52), rgba(102, 222, 255, 0.34) 42%, rgba(96, 142, 255, 0.22) 76%),
    linear-gradient(145deg, rgba(118, 224, 255, 0.28), rgba(126, 105, 255, 0.18));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.34),
    inset 0 -1px 0 rgba(53, 98, 255, 0.14),
    0 18px 34px rgba(0, 7, 22, 0.14),
    0 0 28px rgba(72, 208, 255, 0.12);
}

.mascot-companion--state-boot .mascot-companion__image-wrap::before {
  content: '';
  position: absolute;
  inset: 12px;
  z-index: 0;
  border-radius: 24px;
  background:
    radial-gradient(circle at 50% 46%, rgba(255, 255, 255, 0.16), transparent 62%),
    linear-gradient(160deg, rgba(255, 255, 255, 0.13), transparent 44%, rgba(34, 211, 238, 0.1));
  border: 1px solid rgba(225, 248, 255, 0.16);
}

.mascot-companion--state-boot .mascot-companion__image-wrap::after {
  background: rgba(52, 211, 238, 0.15);
  filter: blur(12px);
}

.mascot-companion--state-boot .mascot-companion__image {
  width: min(196px, 96%);
  mix-blend-mode: screen;
  filter:
    brightness(1.18)
    contrast(1.02)
    saturate(1.06)
    drop-shadow(0 16px 24px rgba(0, 0, 0, 0.14))
    drop-shadow(0 0 18px rgba(88, 216, 255, 0.24));
}

.mascot-companion__content {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.mascot-companion__status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}

.mascot-companion__pulse {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--color-cube-primary);
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.5);
  animation: status-pulse 2s ease-in-out infinite;
}

.mascot-companion__title {
  margin: 0;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 26px;
  line-height: 1.12;
  font-weight: 800;
}

.mascot-companion__message {
  max-width: 26em;
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.65;
}

.mascot-companion__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.mascot-companion__metric {
  min-width: 0;
  padding: 13px 12px;
  border: 1px solid rgba(190, 231, 255, 0.25);
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(145, 218, 255, 0.12), rgba(15, 42, 82, 0.18));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.32),
    0 12px 30px rgba(0, 4, 22, 0.16);
  backdrop-filter: blur(18px) saturate(1.9);
  -webkit-backdrop-filter: blur(18px) saturate(1.9);
  animation: mascot-metric-rise 860ms cubic-bezier(0.16, 1, 0.3, 1) both;
  will-change: transform, opacity;
}

.mascot-companion__metric:nth-child(1) { animation-delay: 140ms; }
.mascot-companion__metric:nth-child(2) { animation-delay: 220ms; }
.mascot-companion__metric:nth-child(3) { animation-delay: 300ms; }

.mascot-companion__metric-value {
  display: block;
  overflow: visible;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: clamp(18px, 1.32vw, 20px);
  font-weight: 700;
  line-height: 1.1;
  white-space: nowrap;
}

.mascot-companion__metric-label {
  display: block;
  overflow: hidden;
  margin-top: 6px;
  color: var(--text-disabled);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 状态变体 */
.mascot-companion--focus {
  border-color: rgba(96, 165, 250, 0.22);
}

.mascot-companion--good {
  border-color: rgba(163, 230, 53, 0.2);
}

.mascot-companion--warn {
  border-color: rgba(251, 191, 36, 0.22);
}

.mascot-companion--focus .mascot-companion__pulse {
  background: #60a5fa;
  box-shadow: 0 0 12px rgba(96, 165, 250, 0.5);
}

.mascot-companion--good .mascot-companion__pulse {
  background: var(--color-cube-accent);
  box-shadow: 0 0 12px rgba(163, 230, 53, 0.45);
}

.mascot-companion--warn .mascot-companion__pulse {
  background: var(--color-warning);
  box-shadow: 0 0 12px rgba(251, 191, 36, 0.45);
}

/* 紧凑模式（侧边栏） */
.mascot-companion--compact {
  grid-template-columns: 74px 1fr;
  gap: 10px;
  min-height: 104px;
  padding: 12px;
  border-radius: 14px;
}

.mascot-companion--compact .mascot-companion__aura {
  width: 118px;
  height: 118px;
  left: -10px;
}

.mascot-companion--compact .mascot-companion__image-wrap {
  min-height: 82px;
}

.mascot-companion--compact .mascot-companion__image {
  width: 78px;
  max-height: 90px;
}

.mascot-companion--compact .mascot-companion__title {
  font-size: 16px;
}

.mascot-companion--compact .mascot-companion__message,
.mascot-companion--compact .mascot-companion__metrics {
  display: none;
}

@keyframes mascot-float {
  0%,
  100% {
    transform: translateY(0) rotate(-0.4deg);
  }
  50% {
    transform: translateY(-8px) rotate(0.6deg);
  }
}

@keyframes mascot-aura {
  from {
    transform: translateY(-50%) rotate(0deg);
  }
  to {
    transform: translateY(-50%) rotate(360deg);
  }
}

@keyframes mascot-metric-rise {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.97);
    filter: blur(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@media (max-width: 760px) {
  .mascot-companion {
    grid-template-columns: 116px 1fr;
    min-height: 176px;
    padding: 14px;
  }

  .mascot-companion__image-wrap {
    min-height: 148px;
  }

  .mascot-companion__image {
    width: 130px;
    max-height: 158px;
  }

  .mascot-companion__title {
    font-size: 21px;
  }

  .mascot-companion__metrics {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .mascot-companion:not(.mascot-companion--compact) {
    grid-template-columns: 1fr;
    gap: 4px;
    padding: 16px 12px;
    text-align: center;
  }

  .mascot-companion:not(.mascot-companion--compact) .mascot-companion__image-wrap {
    min-height: 132px;
  }

  .mascot-companion:not(.mascot-companion--compact) .mascot-companion__content {
    width: 100%;
  }

  .mascot-companion:not(.mascot-companion--compact) .mascot-companion__status {
    justify-content: center;
  }

  .mascot-companion:not(.mascot-companion--compact) .mascot-companion__message {
    margin-inline: auto;
  }

  .mascot-companion:not(.mascot-companion--compact) .mascot-companion__metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
