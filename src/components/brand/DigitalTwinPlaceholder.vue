<template>
  <div class="digital-twin" :class="[`digital-twin--${size}`, { 'digital-twin--offline': offline }]">
    <div class="digital-twin__aura"></div>
    <div class="digital-twin__model" aria-hidden="true">
      <span class="digital-twin__face digital-twin__face--front"></span>
      <span class="digital-twin__face digital-twin__face--top"></span>
      <span class="digital-twin__face digital-twin__face--side"></span>
      <span class="digital-twin__core"></span>
      <span class="digital-twin__scan digital-twin__scan--x"></span>
      <span class="digital-twin__scan digital-twin__scan--y"></span>
    </div>
    <div class="digital-twin__grid" aria-hidden="true"></div>
    <div v-if="showLabel" class="digital-twin__label">
      <span>{{ label }}</span>
      <small>{{ offline ? 'OFFLINE' : 'DIGITAL TWIN' }}</small>
    </div>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'DigitalTwinPlaceholder' })

withDefaults(
  defineProps<{
    label?: string
    offline?: boolean
    showLabel?: boolean
    size?: 'mini' | 'hero'
  }>(),
  {
    label: 'Twin Model',
    offline: false,
    showLabel: false,
    size: 'mini',
  },
)
</script>

<style scoped>
.digital-twin {
  --twin-size: 72px;
  --twin-accent: #22d3ee;
  --twin-accent-2: #a3e635;
  --twin-panel: rgba(112, 208, 255, 0.13);

  position: relative;
  width: var(--twin-size);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  isolation: isolate;
  transform-style: preserve-3d;
}

.digital-twin--hero {
  --twin-size: min(42vw, 420px);
}

.digital-twin--offline {
  filter: grayscale(0.65);
  opacity: 0.62;
}

.digital-twin__aura {
  position: absolute;
  inset: 8%;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.28), transparent 62%),
    radial-gradient(circle at 62% 30%, rgba(163, 230, 53, 0.16), transparent 54%);
  filter: blur(10px);
  animation: twin-breathe 3.8s ease-in-out infinite;
  z-index: -2;
}

.digital-twin__grid {
  position: absolute;
  inset: 9%;
  border-radius: 50%;
  border: 1px solid rgba(210, 246, 255, 0.18);
  background:
    linear-gradient(rgba(210, 246, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(210, 246, 255, 0.1) 1px, transparent 1px);
  background-size: 18% 18%;
  transform: rotateX(67deg) rotateZ(-12deg);
  mask-image: radial-gradient(circle, #000 42%, transparent 72%);
  z-index: -1;
}

.digital-twin__model {
  position: relative;
  width: 52%;
  aspect-ratio: 1;
  transform: rotateX(58deg) rotateZ(43deg);
  transform-style: preserve-3d;
  animation: twin-float 4.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.digital-twin__face,
.digital-twin__core,
.digital-twin__scan {
  position: absolute;
  inset: 0;
  border-radius: 18%;
  border: 1px solid rgba(225, 250, 255, 0.34);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.42),
    0 18px 42px rgba(0, 0, 0, 0.18);
}

.digital-twin__face--front {
  background:
    linear-gradient(145deg, rgba(125, 223, 255, 0.36), rgba(34, 211, 238, 0.08)),
    var(--twin-panel);
  transform: translateZ(calc(var(--twin-size) * 0.13));
}

.digital-twin__face--top {
  background: linear-gradient(145deg, rgba(226, 255, 247, 0.3), rgba(163, 230, 53, 0.08));
  transform: rotateX(90deg) translateZ(calc(var(--twin-size) * 0.13));
  transform-origin: top;
}

.digital-twin__face--side {
  background: linear-gradient(145deg, rgba(167, 139, 250, 0.26), rgba(34, 211, 238, 0.08));
  transform: rotateY(90deg) translateZ(calc(var(--twin-size) * 0.13));
  transform-origin: right;
}

.digital-twin__core {
  inset: 22%;
  border-radius: 35%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.9), rgba(34, 211, 238, 0.28) 38%, transparent 70%);
  border: 0;
  transform: translateZ(calc(var(--twin-size) * 0.17));
  filter: blur(0.2px);
}

.digital-twin__scan {
  inset: -14%;
  border-radius: 20%;
  border-color: rgba(163, 230, 53, 0.38);
  box-shadow: 0 0 22px rgba(163, 230, 53, 0.16);
}

.digital-twin__scan--x {
  animation: scan-x 2.6s ease-in-out infinite;
}

.digital-twin__scan--y {
  border-color: rgba(34, 211, 238, 0.34);
  animation: scan-y 3s ease-in-out infinite;
}

.digital-twin__label {
  position: absolute;
  left: 50%;
  bottom: -8px;
  min-width: 128%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  align-items: baseline;
  gap: 8px;
  color: rgba(255, 255, 255, 0.86);
  font-size: 13px;
  line-height: 1.2;
  text-align: center;
}

.digital-twin__label small {
  font-family: var(--font-mono);
  font-size: 9px;
  color: rgba(163, 230, 53, 0.78);
}

@keyframes twin-float {
  0%, 100% { transform: rotateX(58deg) rotateZ(43deg) translate3d(0, 0, 0); }
  50% { transform: rotateX(58deg) rotateZ(49deg) translate3d(0, -6%, 0); }
}

@keyframes twin-breathe {
  0%, 100% { transform: scale(0.96); opacity: 0.78; }
  50% { transform: scale(1.08); opacity: 1; }
}

@keyframes scan-x {
  0%, 100% { transform: translateZ(calc(var(--twin-size) * 0.19)) scaleX(0.78); opacity: 0.35; }
  50% { transform: translateZ(calc(var(--twin-size) * 0.2)) scaleX(1.12); opacity: 0.72; }
}

@keyframes scan-y {
  0%, 100% { transform: translateZ(calc(var(--twin-size) * 0.21)) scaleY(1.08); opacity: 0.28; }
  50% { transform: translateZ(calc(var(--twin-size) * 0.2)) scaleY(0.72); opacity: 0.62; }
}
</style>
