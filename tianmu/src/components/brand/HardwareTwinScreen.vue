<template>
  <div class="hardware-twin-screen" aria-label="硬件屏幕实时界面">
    <div class="hardware-twin-screen__status">
      <span :class="['hardware-twin-screen__dot', online ? 'is-wifi' : 'is-offline']"></span>
      <span :class="['hardware-twin-screen__dot', online ? 'is-mqtt' : 'is-offline']"></span>
      <span :class="['hardware-twin-screen__dot', focus ? 'is-focus is-active' : 'is-focus']"></span>
    </div>

    <div class="hardware-twin-screen__role">
      <img class="hardware-twin-screen__role-img" :src="roleImage" alt="小眠" />
      <span class="hardware-twin-screen__mood">{{ roleMood }}</span>
    </div>

    <div class="hardware-twin-screen__data">
      <div class="hardware-twin-screen__metrics">
        <div class="hardware-twin-screen__metric is-temp">
          <small>温度</small>
          <strong>{{ metricValue(data?.temperature, '°C', 1) }}</strong>
        </div>
        <div class="hardware-twin-screen__metric is-humi">
          <small>湿度</small>
          <strong>{{ metricValue(data?.humidity, '%', 0) }}</strong>
        </div>
        <div class="hardware-twin-screen__metric is-aqi">
          <small>AQI</small>
          <strong :style="{ color: aqiColor }">{{ metricValue(data?.aqi, '', 0) }}</strong>
        </div>
        <div class="hardware-twin-screen__metric is-co2">
          <small>CO2</small>
          <strong>{{ metricValue(data?.eco2, '', 0) }}</strong>
        </div>
        <div class="hardware-twin-screen__metric is-pm25">
          <small>PM2.5</small>
          <strong>{{ metricValue(data?.pm25, '', 0) }}</strong>
        </div>
        <div class="hardware-twin-screen__metric is-tvoc">
          <small>TVOC</small>
          <strong>{{ metricValue(data?.tvoc, '', 2) }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import roleCelebrate from '@/assets/mascot/role_celebrate.webp'
import roleFocus from '@/assets/mascot/role_focus.webp'
import roleNormal from '@/assets/mascot/role_normal.webp'
import roleRemind from '@/assets/mascot/role_remind.webp'

defineOptions({ name: 'HardwareTwinScreen' })

interface HardwareScreenData {
  temperature?: number | null
  humidity?: number | null
  illuminance?: number | null
  aqi?: number | null
  pm25?: number | null
  tvoc?: number | null
  eco2?: number | null
  timestamp?: string | number | null
}

const props = withDefaults(
  defineProps<{
    data?: HardwareScreenData | null
    focus?: boolean
    online?: boolean
  }>(),
  {
    data: null,
    focus: false,
    online: true,
  },
)

function getNumeric(value: number | null | undefined) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

const hasData = computed(() => {
  if (!props.data) return false

  return [
    props.data.temperature,
    props.data.humidity,
    props.data.illuminance,
    props.data.aqi,
    props.data.pm25,
    props.data.tvoc,
    props.data.eco2,
  ].some((value) => getNumeric(value) !== null)
})

function metricValue(value: number | null | undefined, suffix = '', digits = 0) {
  const numeric = getNumeric(value)
  if (!hasData.value || numeric === null) return '--'
  return `${numeric.toFixed(digits)}${suffix}`
}

const aqi = computed(() => getNumeric(props.data?.aqi) ?? 0)
const eco2 = computed(() => getNumeric(props.data?.eco2) ?? 0)
const tvoc = computed(() => getNumeric(props.data?.tvoc) ?? 0)

const aqiColor = computed(() => {
  if (!hasData.value) return '#7788aa'
  if (aqi.value <= 50) return '#4ade80'
  if (aqi.value <= 100) return '#fbbf24'
  if (aqi.value <= 150) return '#fb923c'
  if (aqi.value <= 200) return '#f43f5e'
  if (aqi.value <= 300) return '#dc2626'
  return '#991b1b'
})

const roleMood = computed(() => {
  if (!hasData.value) return 'Standby'
  if (props.focus) return 'Focus'
  if (aqi.value > 150 || eco2.value > 2000 || tvoc.value > 3000) return 'Alert!'
  if (aqi.value > 100 || eco2.value > 1000 || tvoc.value > 1000) return 'Ventilate'
  if (aqi.value > 50 || eco2.value > 800) return 'OK'
  return 'Great!'
})

const roleImage = computed(() => {
  if (props.focus) return roleFocus
  if (!hasData.value) return roleNormal
  if (aqi.value > 100 || eco2.value > 1000 || tvoc.value > 1000) return roleRemind
  if (aqi.value <= 50 && eco2.value <= 800) return roleCelebrate
  return roleNormal
})
</script>

<style scoped>
.hardware-twin-screen {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  color: #8899bb;
  background:
    radial-gradient(ellipse at 30% 20%, rgba(30, 40, 80, 0.4) 0%, transparent 60%),
    #0c1024;
  border-radius: 2px;
  container-type: size;
}

.hardware-twin-screen__status {
  position: absolute;
  inset: 0 0 auto;
  height: 10%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 3.2%;
  padding: 0 5%;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.42), rgba(0, 0, 0, 0.14));
  line-height: 1;
}

.hardware-twin-screen__dot {
  width: 3cqw;
  height: 3cqw;
  flex: none;
  border-radius: 50%;
  opacity: 0.42;
}

.hardware-twin-screen__dot.is-wifi {
  background: #4ade80;
  box-shadow: 0 0 1.4cqw #4ade80;
  opacity: 1;
}

.hardware-twin-screen__dot.is-mqtt {
  background: #60a5fa;
  box-shadow: 0 0 1.4cqw #60a5fa;
  opacity: 1;
}

.hardware-twin-screen__dot.is-offline {
  background: #f43f5e;
  box-shadow: 0 0 1.4cqw #f43f5e;
  opacity: 1;
}

.hardware-twin-screen__dot.is-focus {
  background: #a78bfa;
}

.hardware-twin-screen__dot.is-active {
  opacity: 1;
  box-shadow: 0 0 1.4cqw #a78bfa;
}

.hardware-twin-screen__role {
  position: absolute;
  left: 4%;
  top: 19%;
  width: 27%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3cqw;
}

.hardware-twin-screen__role-img {
  width: 23cqw;
  height: 23cqw;
  object-fit: contain;
  border-radius: 4.2cqw;
  background: rgba(15, 25, 64, 0.6);
  border: 1px solid rgba(100, 120, 200, 0.15);
}

.hardware-twin-screen__mood {
  max-width: 100%;
  padding: 1.2cqw 3cqw;
  overflow: hidden;
  color: rgba(220, 252, 255, 0.82);
  background: rgba(0, 0, 0, 0.36);
  border-radius: 999px;
  font-size: 3.8cqw;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hardware-twin-screen__data {
  position: absolute;
  right: 4%;
  top: 15%;
  bottom: 6%;
  width: 64%;
}

.hardware-twin-screen__metrics {
  height: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: minmax(0, 1fr);
  gap: 2.1cqw;
}

.hardware-twin-screen__metric {
  min-width: 0;
  overflow: hidden;
  background: rgba(15, 25, 64, 0.48);
  border: 1px solid rgba(100, 120, 200, 0.14);
  border-radius: 2.2cqw;
  padding: 2.2cqw 2.5cqw;
}

.hardware-twin-screen__metric strong,
.hardware-twin-screen__metric small {
  display: block;
  overflow: hidden;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hardware-twin-screen__metric small {
  margin-bottom: 1.5cqw;
  color: #667899;
  font-size: 3.7cqw;
}

.hardware-twin-screen__metric strong {
  font-size: 6.9cqw;
}

.hardware-twin-screen__metric.is-temp strong {
  color: #fb923c;
}

.hardware-twin-screen__metric.is-humi strong {
  color: #60a5fa;
}

.hardware-twin-screen__metric.is-co2 strong {
  color: #a78bfa;
}

.hardware-twin-screen__metric.is-tvoc strong {
  color: #f472b6;
}

.hardware-twin-screen__metric.is-pm25 strong {
  color: #34d399;
}
</style>
