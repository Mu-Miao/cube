<template>
  <div class="light-color-picker">
    <!-- 颜色选择 -->
    <div class="light-color-picker__colors">
      <div
        v-for="c in colorOptions"
        :key="c.value"
        class="light-color-picker__swatch"
        :class="{
          'light-color-picker__swatch--active': modelValue.on && modelValue.color === c.value,
          'light-color-picker__swatch--disabled': disabled,
        }"
        :style="{ backgroundColor: c.value }"
        @click="selectColor(c.value)"
      >
        <span v-if="modelValue.on && modelValue.color === c.value" class="light-color-picker__check">
          &#10003;
        </span>
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
defineOptions({ name: 'LightColorPicker' })

interface LightValue {
  on: boolean
  color: string
  brightness: number
}

const props = defineProps<{
  modelValue: LightValue
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: LightValue): void
}>()

const colorOptions = [
  { label: '白', value: '#FFFFFF' },
  { label: '红', value: '#EF4444' },
  { label: '绿', value: '#10B981' },
  { label: '蓝', value: '#3B82F6' },
]

function selectColor(color: string) {
  if (props.disabled) return
  emit('update:modelValue', { ...props.modelValue, on: true, color })
}

function updateBrightness(brightness: number) {
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
.light-color-picker__colors {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: var(--radius-button, 6px);
  background: rgba(255, 255, 255, 0.028);
}

.light-color-picker__swatch {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform var(--transition-spring, 420ms cubic-bezier(0.2, 0.9, 0.2, 1)),
    box-shadow var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1)),
    border-color var(--transition-base, 250ms cubic-bezier(0.4, 0, 0.2, 1));
  border: 2px solid rgba(255, 255, 255, 0.12);
  position: relative;
  box-shadow: inset 0 0 12px rgba(255, 255, 255, 0.14);
}

.light-color-picker__swatch:hover:not(.light-color-picker__swatch--disabled) {
  transform: translateY(-2px) scale(1.08);
  box-shadow: 0 0 18px currentColor, inset 0 0 12px rgba(255, 255, 255, 0.18);
}

.light-color-picker__swatch--active {
  border-color: #ffffff;
  transform: translateY(-2px) scale(1.08);
  box-shadow: 0 0 18px rgba(255, 255, 255, 0.32), inset 0 0 14px rgba(255, 255, 255, 0.2);
}

.light-color-picker__swatch--disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.light-color-picker__check {
  font-size: 14px;
  color: #000000;
  text-shadow: 0 0 2px rgba(255, 255, 255, 0.5);
  font-weight: 700;
}

/* 亮度调节 */
.light-color-picker__brightness {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.055);
  border-radius: var(--radius-button, 6px);
  background: rgba(255, 255, 255, 0.028);
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
