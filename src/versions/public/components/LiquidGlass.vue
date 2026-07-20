<template>
  <component
    :is="as"
    v-bind="$attrs"
    class="liquid-glass"
    :class="[`liquid-glass--${tone}`, { 'liquid-glass--hover': hover }]"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
defineOptions({ inheritAttrs: false })

withDefaults(
  defineProps<{
    as?: string
    tone?: 'plain' | 'blue' | 'green'
    hover?: boolean
  }>(),
  {
    as: 'section',
    tone: 'plain',
    hover: false,
  },
)
</script>

<style scoped>
.liquid-glass {
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-2xl);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.035)),
    rgba(18, 18, 22, 0.62);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 28px 90px rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(28px) saturate(1.65);
  -webkit-backdrop-filter: blur(28px) saturate(1.65);
  overflow: hidden;
}

.liquid-glass::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 16% 0%, rgba(255, 255, 255, 0.24), transparent 32%),
    linear-gradient(120deg, rgba(255, 255, 255, 0.12), transparent 38%, rgba(255, 255, 255, 0.06));
  opacity: 0.64;
}

.liquid-glass--blue {
  background:
    linear-gradient(145deg, rgba(54, 128, 220, 0.14), rgba(255, 255, 255, 0.035)),
    rgba(16, 28, 46, 0.58);
}

.liquid-glass--green {
  background:
    linear-gradient(145deg, rgba(57, 190, 124, 0.13), rgba(255, 255, 255, 0.035)),
    rgba(14, 34, 26, 0.56);
}

.liquid-glass--hover {
  transition:
    transform 240ms ease,
    border-color 240ms ease,
    box-shadow 240ms ease;
}

.liquid-glass--hover:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    0 34px 96px rgba(0, 0, 0, 0.38);
}
</style>
