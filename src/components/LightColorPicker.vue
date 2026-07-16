<template>
  <div class="light-color-picker">
    <ControlToggle
      :model-value="modelValue.on"
      label="灯光开关"
      :disabled="disabled"
      :loading="loading"
      @update:model-value="updatePower"
    />

    <div class="light-color-picker__temperature">
      <div class="light-color-picker__temperature-head">
        <span class="light-color-picker__brightness-label">色温</span>
        <span class="light-color-picker__temperature-value">{{ modelValue.colorTemperature }}K</span>
      </div>
      <div class="light-color-picker__temperature-track">
        <span>暖</span>
        <el-slider
          :model-value="modelValue.colorTemperature"
          :min="2700"
          :max="6500"
          :step="100"
          :disabled="disabled || !modelValue.on"
          :show-tooltip="true"
          @update:model-value="updateColorTemperature"
        />
        <span>冷</span>
      </div>
      <div class="light-color-picker__presets">
        <button
          v-for="preset in temperaturePresets"
          :key="preset.value"
          class="light-color-picker__preset"
          :class="{ 'light-color-picker__preset--active': modelValue.on && modelValue.colorTemperature === preset.value }"
          :disabled="disabled || !modelValue.on"
          type="button"
          @click="updateColorTemperature(preset.value)"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>

    <!-- 亮度调节 -->
    <div class="light-color-picker__brightness">
      <span class="light-color-picker__brightness-label">亮度</span>
      <div class="light-color-picker__slider-wrap">
        <el-slider
          :model-value="modelValue.brightness"
          :min="0"
          :max="100"
          :disabled="disabled || !modelValue.on"
          :show-tooltip="true"
          @update:model-value="updateBrightness"
        />
      </div>
      <span class="light-color-picker__brightness-value">
        {{ modelValue.brightness }}%
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import ControlToggle from '@/components/ControlToggle.vue'

defineOptions({ name: 'LightColorPicker' })

interface LightValue {
  on: boolean
  colorTemperature: number
  brightness: number
}

const props = defineProps<{
  modelValue: LightValue
  disabled?: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: LightValue): void
}>()

const temperaturePresets = [
  { label: '暖色', value: 3000 },
  { label: '冷色', value: 6000 },
]

function updatePower(on: boolean) {
  if (props.disabled) return
  emit('update:modelValue', { ...props.modelValue, on })
}

function updateColorTemperature(colorTemperature: number | number[]) {
  if (Array.isArray(colorTemperature) || props.disabled || !props.modelValue.on) return
  emit('update:modelValue', { ...props.modelValue, colorTemperature })
}

function updateBrightness(brightness: number | number[]) {
  if (Array.isArray(brightness)) return
  emit('update:modelValue', { ...props.modelValue, brightness })
}
</script>

<style scoped>
.light-color-picker {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 颜色选择 */
.light-color-picker__temperature,
.light-color-picker__brightness {
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: var(--radius-button, 6px);
  background: rgba(255, 255, 255, 0.028);
}

.light-color-picker__temperature {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.light-color-picker__temperature-head,
.light-color-picker__temperature-track {
  display: flex;
  align-items: center;
  gap: 10px;
}

.light-color-picker__temperature-track {
  color: var(--text-secondary, #8b95b0);
  font-size: 12px;
}

.light-color-picker__temperature-track :deep(.el-slider) {
  flex: 1;
}

.light-color-picker__temperature-value {
  margin-left: auto;
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.86);
}

.light-color-picker__presets {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.light-color-picker__preset {
  height: 32px;
  border: 1px solid rgba(216, 242, 255, 0.15);
  border-radius: 10px;
  color: var(--text-secondary, #8b95b0);
  background: rgba(255, 255, 255, 0.045);
  cursor: pointer;
  transition:
    transform var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    background var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
}

.light-color-picker__preset:hover:not(:disabled),
.light-color-picker__preset--active {
  color: var(--text-primary, #ffffff);
  border-color: rgba(163, 230, 53, 0.45);
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.13), rgba(163, 230, 53, 0.13));
}

.light-color-picker__preset:hover:not(:disabled) {
  transform: translateY(-1px);
}

.light-color-picker__preset:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.light-color-picker__brightness {
  display: flex;
  align-items: center;
  gap: 10px;
}

.light-color-picker__brightness-label {
  font-family: var(--font-body, 'Inter', 'Plus Jakarta Sans', sans-serif);
  font-size: 13px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
  white-space: nowrap;
  flex-shrink: 0;
}

.light-color-picker__slider-wrap {
  flex: 1;
}

.light-color-picker__slider-wrap :deep(.el-slider__runway) {
  height: 4px;
}

.light-color-picker__slider-wrap :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
}

.light-color-picker__brightness-value {
  font-family: var(--font-mono, 'JetBrains Mono', monospace);
  font-size: 13px;
  color: var(--text-secondary, var(--text-secondary, #8b95b0));
  min-width: 36px;
  text-align: right;
  flex-shrink: 0;
}
</style>
