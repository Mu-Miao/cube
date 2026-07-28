<template>
  <div class="digital-twin cube-spin-preview" :class="{ 'cube-spin-preview--offline': offline }">
    <div class="cube-spin-preview__aura" aria-hidden="true"></div>
    <img class="cube-spin-preview__image" :src="previewImage" :alt="label" loading="lazy" decoding="async" draggable="false" />
    <div class="cube-spin-preview__grid" aria-hidden="true"></div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'CubeSpinGifPreview' })

withDefaults(
  defineProps<{
    label?: string
    offline?: boolean
  }>(),
  {
    label: 'Cube model preview',
    offline: false,
  },
)

const previewImage = '/smart-cube-transparent.png'
</script>

<style scoped>
.cube-spin-preview {
  --twin-size: 72px;

  position: relative;
  width: var(--twin-size);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  isolation: isolate;
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(125, 213, 255, 0.14), rgba(22, 47, 93, 0.22)),
    radial-gradient(circle at 46% 38%, rgba(255, 255, 255, 0.18), transparent 54%);
  border: 1px solid rgba(203, 242, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.26),
    0 12px 28px rgba(0, 7, 24, 0.24);
}

.cube-spin-preview--offline {
  filter: grayscale(0.72);
  opacity: 0.62;
}

.cube-spin-preview__image {
  position: relative;
  z-index: 1;
  width: 94%;
  height: 82%;
  display: block;
  object-fit: contain;
  transform: translateY(1px);
  filter:
    drop-shadow(0 8px 12px rgba(0, 9, 24, 0.3))
    drop-shadow(0 0 12px rgba(64, 224, 255, 0.16));
}

.cube-spin-preview__aura {
  position: absolute;
  inset: 12%;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.28), transparent 64%),
    radial-gradient(circle at 60% 34%, rgba(163, 230, 53, 0.14), transparent 54%);
  filter: blur(12px);
  animation: cube-spin-preview-breathe 3.8s ease-in-out infinite;
  z-index: -2;
}

.cube-spin-preview__grid {
  position: absolute;
  inset: 22% 15% 12%;
  border-radius: 50%;
  border: 1px solid rgba(210, 246, 255, 0.1);
  background:
    linear-gradient(rgba(210, 246, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(210, 246, 255, 0.06) 1px, transparent 1px);
  background-size: 20% 20%;
  transform: rotateX(67deg) rotateZ(-12deg);
  mask-image: radial-gradient(circle, #000 42%, transparent 72%);
  z-index: -1;
}

@keyframes cube-spin-preview-breathe {
  0%, 100% { transform: scale(0.96); opacity: 0.78; }
  50% { transform: scale(1.08); opacity: 1; }
}
</style>
