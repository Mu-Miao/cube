<template>
  <div class="product-cube" :class="`product-cube--${variant}`" aria-label="智能桌面魔方模型预览">
    <div class="product-cube__halo"></div>
    <div class="product-cube__visual">
      <img class="product-cube__image" src="/smart-cube-transparent.png" alt="智能桌面魔方渲染图" decoding="async" />
      <div class="product-cube__screen" aria-label="魔方屏幕实时数据">
        <HardwareTwinScreen :data="sensor" :online="online" :focus="focus" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import HardwareTwinScreen from '@/components/brand/HardwareTwinScreen.vue'
import type { SensorData } from '@/versions/public/api/client'

withDefaults(
  defineProps<{
    focus?: boolean
    online?: boolean
    sensor?: SensorData | null
    value?: string
    variant?: 'default' | 'hero'
  }>(),
  {
    focus: false,
    online: true,
    sensor: null,
    value: '26',
    variant: 'default',
  },
)
</script>

<style scoped>
.product-cube {
  position: relative;
  width: min(48vw, 600px);
  min-width: 340px;
  aspect-ratio: 1.34;
  display: grid;
  place-items: center;
  isolation: isolate;
}

.product-cube__halo {
  position: absolute;
  inset: 12% 9% 7%;
  border-radius: 50%;
  background:
    radial-gradient(ellipse at 52% 58%, rgba(255, 255, 255, 0.28), transparent 58%),
    radial-gradient(ellipse at 50% 80%, rgba(0, 0, 0, 0.2), transparent 64%);
  filter: blur(18px);
  opacity: 0.85;
  z-index: -1;
}

.product-cube__visual {
  position: relative;
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
}

.product-cube__image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  filter: drop-shadow(0 22px 34px rgba(0, 0, 0, 0.22)) contrast(1.03) saturate(0.98);
}

.product-cube__screen {
  position: absolute;
  left: 50.24%;
  top: 52.07%;
  width: 33.84%;
  min-width: 118px;
  aspect-ratio: 1.31;
  overflow: hidden;
  transform: translate(-50%, -50%);
  background: #0c1024;
  border-radius: 3px;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.42);
  pointer-events: none;
}

.product-cube::after {
  content: '';
  position: absolute;
  right: 18%;
  bottom: 14%;
  width: 44%;
  height: 13%;
  border-radius: 50%;
  background:
    radial-gradient(ellipse, rgba(0, 0, 0, 0.22), transparent 68%);
  filter: blur(12px);
  opacity: 0.35;
  z-index: -1;
}

.product-cube--hero {
  width: clamp(390px, 34vw, 540px);
  min-width: 390px;
}

@media (max-width: 760px) {
  .product-cube {
    width: min(82vw, 380px);
    min-width: 0;
  }

  .product-cube--hero {
    width: min(78vw, 360px);
    min-width: 0;
  }
}
</style>
