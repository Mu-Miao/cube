<template>
  <label class="control-row">
    <span class="control-row__icon" v-html="icon"></span>
    <span class="control-row__copy">
      <strong>{{ label }}</strong>
      <small>{{ detail }}</small>
    </span>
    <input
      class="switch-input"
      type="checkbox"
      :checked="modelValue"
      @change="handleChange"
    />
    <span class="switch-visual"></span>
  </label>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  detail: string
  icon: string
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function handleChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).checked)
}
</script>
