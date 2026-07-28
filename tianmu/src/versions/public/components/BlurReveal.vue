<template>
  <component :is="as" class="blur-reveal" :style="{ '--delay': `${delay}ms` }">
    <slot />
  </component>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: string
    delay?: number
  }>(),
  {
    as: 'div',
    delay: 0,
  },
)
</script>

<style scoped>
.blur-reveal {
  animation: blur-reveal 740ms cubic-bezier(0.2, 0.9, 0.18, 1) both;
  animation-delay: var(--delay);
}

@keyframes blur-reveal {
  from {
    opacity: 0;
    filter: blur(14px);
    transform: translateY(18px);
  }

  to {
    opacity: 1;
    filter: blur(0);
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .blur-reveal {
    animation: none;
  }
}
</style>
