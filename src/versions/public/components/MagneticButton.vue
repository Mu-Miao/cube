<template>
  <button
    class="magnetic-button"
    :class="`magnetic-button--${variant}`"
    :style="style"
    @pointermove="handleMove"
    @pointerleave="reset"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'quiet'
  }>(),
  {
    variant: 'primary',
  },
)

const x = ref(0)
const y = ref(0)

const style = computed(() => ({
  transform: `translate3d(${x.value}px, ${y.value}px, 0)`,
}))

function handleMove(event: PointerEvent) {
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  x.value = (event.clientX - rect.left - rect.width / 2) * 0.08
  y.value = (event.clientY - rect.top - rect.height / 2) * 0.12
}

function reset() {
  x.value = 0
  y.value = 0
}
</script>

<style scoped>
.magnetic-button {
  appearance: none;
  border: 0;
  min-height: 42px;
  border-radius: 999px;
  padding: 0 18px;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background 180ms ease;
}

.magnetic-button--primary {
  color: white;
  background: #0071e3;
  box-shadow: 0 16px 36px rgba(0, 113, 227, 0.22);
}

.magnetic-button--quiet {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.64);
  border: 1px solid rgba(30, 45, 72, 0.1);
}

.magnetic-button:hover {
  box-shadow: 0 18px 42px rgba(0, 113, 227, 0.18);
}
</style>
