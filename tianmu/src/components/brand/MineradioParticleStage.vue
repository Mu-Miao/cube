<template>
  <canvas
    ref="canvasRef"
    class="particle-stage"
    :class="[`particle-stage--${variant}`, { 'particle-stage--embedded': embedded }]"
    aria-hidden="true"
  />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

defineOptions({ name: 'MineradioParticleStage' })

const props = withDefaults(
  defineProps<{
    airData?: AirQualityData
    density?: number
    embedded?: boolean
    fps?: number
    intensity?: number
    showLabels?: boolean
    variant?: 'ambient' | 'hero' | 'login'
  }>(),
  {
    density: 1,
    embedded: false,
    fps: 50,
    intensity: 0.72,
    showLabels: true,
    variant: 'ambient',
  },
)

type Particle = {
  baseX: number
  baseY: number
  baseZ: number
  phase: number
  size: number
  speed: number
  species: AirSpecies
}

type AirSpecies = {
  label: string
  name: string
  color: string
  glow: string
  baseWeight: number
}

type AirQualityData = {
  aqi?: number
  eco2?: number
  formaldehyde?: number
  humidity?: number
  oxygen?: number
  pm25?: number
  tvoc?: number
}

type SpeciesProfile = AirSpecies & {
  weight: number
}

const canvasRef = ref<HTMLCanvasElement>()
const particles: Particle[] = []
const pointer = { x: 0, y: 0 }
let animationFrame = 0
let ctx: CanvasRenderingContext2D | null = null
let width = 0
let height = 0
let pixelRatio = 1
let startedAt = 0
let isVisible = true
let documentVisible = true
let lastRenderAt = 0
let currentAirProfile: SpeciesProfile[] = []
let targetParticleCount = 0
let observer: IntersectionObserver | null = null

// 最大渲染宽度：超出此宽度的屏幕以较低分辨率渲染、CSS 放大，保证帧率稳定
const MAX_RENDER_WIDTH = 1440

function getFrameInterval() {
  return 1000 / Math.max(12, Math.min(60, props.fps))
}

const AIR_SPECIES: AirSpecies[] = [
  { label: 'O2', name: '氧气', color: '#a3e635', glow: 'rgba(163, 230, 53, 0.34)', baseWeight: 0.28 },
  { label: 'CO2', name: '二氧化碳', color: '#60a5fa', glow: 'rgba(96, 165, 250, 0.3)', baseWeight: 0.16 },
  { label: 'H2O', name: '水汽', color: '#22d3ee', glow: 'rgba(34, 211, 238, 0.32)', baseWeight: 0.16 },
  { label: 'PM2.5', name: '细颗粒物', color: '#9ca3af', glow: 'rgba(156, 163, 175, 0.28)', baseWeight: 0.14 },
  { label: 'TVOC', name: '挥发物', color: '#fbbf24', glow: 'rgba(251, 191, 36, 0.3)', baseWeight: 0.12 },
  { label: 'CH2O', name: '甲醛', color: '#fb7185', glow: 'rgba(251, 113, 133, 0.28)', baseWeight: 0.08 },
]

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min)
}

function clamp(value: number, min = 0, max = 1) {
  return Math.max(min, Math.min(max, value))
}

function normalize(value: number | undefined, clean: number, high: number) {
  if (value == null || Number.isNaN(value)) return 0
  return clamp((value - clean) / (high - clean))
}

function getAirProfile() {
  const data = props.airData ?? {}
  const pm25Pressure = data.pm25 != null
    ? normalize(data.pm25, 12, 75)
    : normalize(data.aqi, 50, 150)
  const co2Pressure = normalize(data.eco2, 600, 1500)
  const tvocPressure = normalize(data.tvoc, 120, 600)
  const humidityPressure = normalize(data.humidity, 45, 85)
  const formaldehydePressure = normalize(data.formaldehyde, 0.04, 0.18)
  const oxygenPressure = data.oxygen != null ? normalize(21 - data.oxygen, 0.2, 2.2) : 0

  const profile = AIR_SPECIES.map((species) => {
    const boostMap: Record<string, number> = {
      O2: oxygenPressure > 0 ? 0.18 - oxygenPressure * 0.08 : 0.1,
      CO2: co2Pressure * 0.42,
      H2O: humidityPressure * 0.34,
      'PM2.5': pm25Pressure * 0.62,
      TVOC: tvocPressure * 0.46,
      CH2O: formaldehydePressure * 0.44,
    }
    return {
      ...species,
      weight: Math.max(0.03, species.baseWeight + (boostMap[species.label] ?? 0)),
    }
  })

  const pollutionLoad = clamp(
    pm25Pressure * 0.45 +
      co2Pressure * 0.22 +
      tvocPressure * 0.2 +
      humidityPressure * 0.08 +
      formaldehydePressure * 0.18,
    0,
    1,
  )

  return {
    particleMultiplier: 1 + pollutionLoad * 0.75,
    profile,
  }
}

function pickSpecies(profile: SpeciesProfile[]) {
  const totalWeight = profile.reduce((sum, item) => sum + item.weight, 0)
  const roll = Math.random()
  let cursor = 0
  for (const item of profile) {
    cursor += item.weight / totalWeight
    if (roll <= cursor) return item
  }
  return profile[0] as SpeciesProfile
}

function getTargetParticleCount() {
  const { particleMultiplier } = getAirProfile()
  // 保留空气质量驱动的数量变化，但低密度场景允许显著缩小粒子池。
  const baseCount = Math.round(
    Math.min(110, Math.max(24, (width * height) / 22000) * particleMultiplier) * props.density,
  )
  const minimumCount = props.density <= 0.35 ? 10 : 22
  return Math.max(minimumCount, baseCount)
}

function createParticle(index = particles.length): Particle {
  const band = index % 5
  const angle = randomBetween(0, Math.PI * 2)
  const radius = band === 0 ? randomBetween(38, 210) : randomBetween(130, 560)
  const yBias = band === 0 ? randomBetween(-80, 90) : randomBetween(-250, 250)

  return {
    baseX: Math.cos(angle) * radius,
    baseY: yBias + Math.sin(angle * 1.8) * randomBetween(8, 64),
    baseZ: Math.sin(angle) * radius + randomBetween(-260, 260),
    phase: randomBetween(0, Math.PI * 2),
    size: randomBetween(0.75, band === 0 ? 2.4 : 1.7),
    speed: randomBetween(0.28, 1.12),
    species: pickSpecies(currentAirProfile),
  }
}

function refreshAirTargets() {
  currentAirProfile = getAirProfile().profile
  targetParticleCount = getTargetParticleCount()
}

function resetParticles() {
  particles.length = 0
  refreshAirTargets()

  for (let index = 0; index < targetParticleCount; index += 1) {
    particles.push(createParticle(index))
  }
}

let resetTimer = 0

function scheduleParticleReset() {
  window.clearTimeout(resetTimer)
  resetTimer = window.setTimeout(resetParticles, 180)
}

function easeParticlePool() {
  const delta = targetParticleCount - particles.length
  if (delta > 0) {
    const addCount = Math.min(2, delta)
    for (let index = 0; index < addCount; index += 1) {
      particles.push(createParticle())
    }
  } else if (delta < 0) {
    particles.splice(Math.max(0, particles.length - Math.min(2, -delta)), Math.min(2, -delta))
  }

  // 空气成分变化时不要整池重置：每帧轻微替换一小部分粒子的物种，
  // 让 PM2.5 / TVOC 等比例像呼吸一样慢慢变化。
  const remixCount = particles.length > 90 ? 2 : 1
  for (let index = 0; index < remixCount; index += 1) {
    const particle = particles[Math.floor(Math.random() * particles.length)]
    if (particle) {
      particle.species = pickSpecies(currentAirProfile)
    }
  }
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  width = Math.max(1, rect.width)
  height = Math.max(1, rect.height)

  // 基础像素比：限制最高 1.15，液态玻璃 + canvas 叠加时避免高 DPR 把像素量放大数倍。
  let dpr = Math.min(window.devicePixelRatio || 1, 1.15)

  // 大屏优化：限制最大渲染宽度，超出则降低像素比
  // 这样 4K 屏渲染 ~1920px 宽（而非 ~5760px），帧率与 1080p 屏一致
  if (width > MAX_RENDER_WIDTH) {
    dpr = Math.min(dpr, MAX_RENDER_WIDTH / width)
  }

  pixelRatio = dpr
  canvas.width = Math.round(width * pixelRatio)
  canvas.height = Math.round(height * pixelRatio)
  ctx = canvas.getContext('2d')
  ctx?.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0)
  resetParticles()
}

function project(x: number, y: number, z: number) {
  const perspective = props.variant === 'hero' ? 680 : 820
  const scale = perspective / (perspective + z)
  return {
    x: width * 0.5 + x * scale,
    y: height * 0.52 + y * scale,
    scale,
  }
}

function rotatePoint(x: number, y: number, z: number, time: number) {
  const yaw = Math.sin(time * 0.00017) * 0.42 + pointer.x * 0.18
  const pitch = Math.cos(time * 0.00013) * 0.18 + pointer.y * 0.12
  const cosYaw = Math.cos(yaw)
  const sinYaw = Math.sin(yaw)
  const cosPitch = Math.cos(pitch)
  const sinPitch = Math.sin(pitch)

  const rotatedX = x * cosYaw - z * sinYaw
  const rotatedZ = x * sinYaw + z * cosYaw
  const rotatedY = y * cosPitch - rotatedZ * sinPitch
  const finalZ = y * sinPitch + rotatedZ * cosPitch

  return { x: rotatedX, y: rotatedY, z: finalZ }
}

function drawRing(time: number, radius: number, zOffset: number, alpha: number, hue: number) {
  if (!ctx) return
  ctx.beginPath()
  // 优化：减少轨道采样点从 150 到 60
  const segments = 60
  for (let i = 0; i <= segments; i += 1) {
    const angle = (i / segments) * Math.PI * 2
    const wobble = Math.sin(angle * 5 + time * 0.0013) * 18
    const point = rotatePoint(
      Math.cos(angle) * (radius + wobble),
      Math.sin(angle) * (radius * 0.34),
      Math.sin(angle) * 110 + zOffset,
      time,
    )
    const projected = project(point.x, point.y, point.z)
    if (i === 0) {
      ctx.moveTo(projected.x, projected.y)
    } else {
      ctx.lineTo(projected.x, projected.y)
    }
  }
  ctx.strokeStyle = `hsla(${hue}, 92%, 62%, ${alpha})`
  ctx.lineWidth = 1
  ctx.stroke()
}

function render(now: number) {
  animationFrame = requestAnimationFrame(render)

  // 不可见时跳过渲染
  if (!isVisible || !documentVisible) {
    return
  }
  if (now - lastRenderAt < getFrameInterval()) return
  lastRenderAt = now

  if (!ctx) return
  const elapsed = now - startedAt
  const intensity = Math.max(0.2, Math.min(1.35, props.intensity))

  easeParticlePool()

  ctx.clearRect(0, 0, width, height)

  // 中心渐变光晕（仅绘制一次，开销很小）
  const gradient = ctx.createRadialGradient(
    width * 0.5,
    height * 0.44,
    40,
    width * 0.5,
    height * 0.5,
    Math.max(width, height) * 0.68,
  )
  gradient.addColorStop(0, `rgba(34, 211, 238, ${0.11 * intensity})`)
  gradient.addColorStop(0.42, `rgba(139, 92, 246, ${0.07 * intensity})`)
  gradient.addColorStop(1, 'rgba(7, 9, 13, 0)')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, width, height)

  // 轨道环
  drawRing(elapsed, Math.min(width, height) * 0.24, -80, 0.09 * intensity, 186)
  drawRing(elapsed + 1200, Math.min(width, height) * 0.34, 60, 0.065 * intensity, 82)
  if (props.showLabels) {
    drawRing(elapsed + 2400, Math.min(width, height) * 0.46, 140, 0.045 * intensity, 262)
  }

  // 粒子：不同颜色和细小标签代表空气成分。
  ctx.shadowBlur = 0

  for (let index = 0; index < particles.length; index += 1) {
    const particle = particles[index] as Particle
    const pulse = Math.sin(elapsed * 0.001 * particle.speed + particle.phase)
    const wave = Math.cos(elapsed * 0.00072 + particle.phase * 1.7)
    const point = rotatePoint(
      particle.baseX + pulse * 18,
      particle.baseY + wave * 22,
      particle.baseZ + pulse * 34,
      elapsed,
    )
    const projected = project(point.x, point.y, point.z)
    const alpha = Math.max(0.04, Math.min(0.45, (projected.scale - 0.38) * 0.5)) * intensity
    const size = Math.max(0.45, particle.size * projected.scale * (1 + Math.max(0, pulse) * 0.4))

    ctx.beginPath()
    ctx.fillStyle = particle.species.glow.replace(/[\d.]+\)$/u, `${Math.max(0.05, alpha * 0.58)})`)
    ctx.arc(projected.x, projected.y, size * 3, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.fillStyle = particle.species.color
    ctx.globalAlpha = Math.min(0.95, alpha * 1.85)
    ctx.arc(projected.x, projected.y, size, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = 1

    if (props.showLabels) {
      const labelAlpha = Math.max(0.1, Math.min(0.46, alpha * 0.96))
      const fontSize = Math.max(6.6, Math.min(8.6, 7 * projected.scale + 1.6))
      ctx.font = `500 ${fontSize}px "JetBrains Mono", ui-monospace, SFMono-Regular, monospace`
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = particle.species.color
      ctx.globalAlpha = labelAlpha
      ctx.fillText(particle.species.label, projected.x + size * 2.2 + 2, projected.y - size * 1.7)
      ctx.globalAlpha = 1
    }
  }
}

function handlePointerMove(event: PointerEvent) {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
  pointer.y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
}

function handlePointerLeave() {
  pointer.x = 0
  pointer.y = 0
}

function handleVisibilityChange() {
  documentVisible = document.visibilityState === 'visible'
}

watch(
  () => [props.density, props.airData],
  () => refreshAirTargets(),
  { deep: true },
)

watch(
  () => props.variant,
  () => scheduleParticleReset(),
  { deep: true },
)

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  startedAt = performance.now()
  resize()
  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  canvas.addEventListener('pointermove', handlePointerMove)
  canvas.addEventListener('pointerleave', handlePointerLeave)

  // 使用 IntersectionObserver 在 canvas 不可见时暂停渲染
  observer = new IntersectionObserver(
    (entries) => {
      isVisible = entries[0]?.isIntersecting ?? true
    },
    { threshold: 0 },
  )
  observer.observe(canvas)

  animationFrame = requestAnimationFrame(render)
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  canvasRef.value?.removeEventListener('pointermove', handlePointerMove)
  canvasRef.value?.removeEventListener('pointerleave', handlePointerLeave)
  window.clearTimeout(resetTimer)
  cancelAnimationFrame(animationFrame)
  observer?.disconnect()
})
</script>

<style scoped>
.particle-stage {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.86;
  mix-blend-mode: screen;
}

.particle-stage--embedded {
  position: absolute;
  inset: 0;
}

.particle-stage--hero {
  opacity: 0.98;
}

.particle-stage--login {
  opacity: 0.94;
}
</style>
