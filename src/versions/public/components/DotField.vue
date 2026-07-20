<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const TWO_PI = Math.PI * 2

type Dot = {
  ax: number
  ay: number
  sx: number
  sy: number
  vx: number
  vy: number
  x: number
  y: number
}

const props = withDefaults(
  defineProps<{
    dotRadius?: number
    dotSpacing?: number
    cursorRadius?: number
    cursorForce?: number
    bulgeOnly?: boolean
    bulgeStrength?: number
    glowRadius?: number
    sparkle?: boolean
    waveAmplitude?: number
    gradientFrom?: string
    gradientTo?: string
    glowColor?: string
    className?: string
  }>(),
  {
    dotRadius: 1.5,
    dotSpacing: 14,
    cursorRadius: 500,
    cursorForce: 0.1,
    bulgeOnly: true,
    bulgeStrength: 67,
    glowRadius: 160,
    sparkle: false,
    waveAmplitude: 0,
    gradientFrom: 'rgba(124, 255, 103, 0.35)',
    gradientTo: 'rgba(160, 255, 188, 0.25)',
    glowColor: '#14110E',
    className: '',
  },
)

const root = ref<HTMLDivElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
const glowEl = ref<SVGCircleElement | null>(null)
const glowId = `dot-field-glow-${Math.random().toString(36).slice(2, 9)}`

let dots: Dot[] = []

const mouse = {
  x: -9999,
  y: -9999,
  prevX: -9999,
  prevY: -9999,
  speed: 0,
}

let size = {
  w: 0,
  h: 0,
  offsetX: 0,
  offsetY: 0,
}

let glowOpacity = 0
let engagement = 0
let raf = 0
let resizeTimer: ReturnType<typeof setTimeout> | undefined
let speedInterval: ReturnType<typeof setInterval> | undefined
let frameCount = 0
let resizeObserver: ResizeObserver | undefined
let isPaused = false

function buildDots(w: number, h: number) {
  const step = props.dotRadius + props.dotSpacing
  const cols = Math.max(1, Math.floor(w / step))
  const rows = Math.max(1, Math.floor(h / step))
  const padX = (w % step) / 2
  const padY = (h % step) / 2
  const nextDots: Dot[] = new Array(rows * cols)

  let idx = 0

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const ax = padX + col * step + step / 2
      const ay = padY + row * step + step / 2

      nextDots[idx++] = {
        ax,
        ay,
        sx: ax,
        sy: ay,
        vx: 0,
        vy: 0,
        x: ax,
        y: ay,
      }
    }
  }

  dots = nextDots
}

function updateMouseSpeed() {
  const dx = mouse.prevX - mouse.x
  const dy = mouse.prevY - mouse.y
  const dist = Math.sqrt(dx * dx + dy * dy)

  mouse.speed += (dist - mouse.speed) * 0.5

  if (mouse.speed < 0.001) {
    mouse.speed = 0
  }

  mouse.prevX = mouse.x
  mouse.prevY = mouse.y
}

function setupCanvas() {
  if (!root.value || !canvas.value) return

  const ctx = canvas.value.getContext('2d', { alpha: true })

  if (!ctx) return

  const renderCtx = ctx

  const dpr = Math.min(window.devicePixelRatio || 1, 2)

  function doResize() {
    if (!root.value || !canvas.value) return

    const rect = root.value.getBoundingClientRect()
    const w = rect.width
    const h = rect.height

    canvas.value.width = w * dpr
    canvas.value.height = h * dpr
    canvas.value.style.width = `${w}px`
    canvas.value.style.height = `${h}px`

    renderCtx.setTransform(dpr, 0, 0, dpr, 0, 0)

    size = {
      w,
      h,
      offsetX: rect.left + window.scrollX,
      offsetY: rect.top + window.scrollY,
    }

    buildDots(w, h)
  }

  function resize() {
    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }

    resizeTimer = setTimeout(doResize, 100)
  }

  function onPointerMove(e: PointerEvent) {
    mouse.x = e.pageX - size.offsetX
    mouse.y = e.pageY - size.offsetY
  }

  function resetPointer() {
    mouse.x = -9999
    mouse.y = -9999
    mouse.prevX = -9999
    mouse.prevY = -9999
    mouse.speed = 0
  }

  function handleVisibilityChange() {
    isPaused = document.hidden

    if (!isPaused && !raf) {
      raf = requestAnimationFrame(tick)
    }
  }

  function tick() {
    if (isPaused) {
      raf = 0
      return
    }

    frameCount++

    const { w, h } = size
    const t = frameCount * 0.02
    const targetEngagement = Math.min(mouse.speed / 5, 1)

    engagement += (targetEngagement - engagement) * 0.06

    if (engagement < 0.001) {
      engagement = 0
    }

    glowOpacity += (engagement - glowOpacity) * 0.08

    if (glowEl.value) {
      glowEl.value.setAttribute('cx', String(mouse.x))
      glowEl.value.setAttribute('cy', String(mouse.y))
      glowEl.value.style.opacity = String(glowOpacity)
    }

    renderCtx.clearRect(0, 0, w, h)

    const grad = renderCtx.createLinearGradient(0, 0, w, h)
    grad.addColorStop(0, props.gradientFrom)
    grad.addColorStop(1, props.gradientTo)
    renderCtx.fillStyle = grad

    const crSq = props.cursorRadius * props.cursorRadius
    const rad = props.dotRadius / 2

    renderCtx.beginPath()

    for (let i = 0; i < dots.length; i++) {
      const d = dots[i]
      if (!d) continue

      const dx = mouse.x - d.ax
      const dy = mouse.y - d.ay
      const distSq = dx * dx + dy * dy

      if (distSq < crSq && engagement > 0.01) {
        const dist = Math.sqrt(distSq)
        const angle = Math.atan2(dy, dx)

        if (props.bulgeOnly) {
          const falloff = 1 - dist / props.cursorRadius
          const push = falloff * falloff * props.bulgeStrength * engagement

          d.sx += (d.ax - Math.cos(angle) * push - d.sx) * 0.15
          d.sy += (d.ay - Math.sin(angle) * push - d.sy) * 0.15
        } else {
          const safeDist = Math.max(dist, 0.001)
          const move = (500 / safeDist) * (mouse.speed * props.cursorForce)

          d.vx += Math.cos(angle) * -move
          d.vy += Math.sin(angle) * -move
        }
      } else if (props.bulgeOnly) {
        d.sx += (d.ax - d.sx) * 0.1
        d.sy += (d.ay - d.sy) * 0.1
      }

      if (!props.bulgeOnly) {
        d.vx *= 0.9
        d.vy *= 0.9
        d.x = d.ax + d.vx
        d.y = d.ay + d.vy
        d.sx += (d.x - d.sx) * 0.1
        d.sy += (d.y - d.sy) * 0.1
      }

      let drawX = d.sx
      let drawY = d.sy

      if (props.waveAmplitude > 0) {
        drawY += Math.sin(d.ax * 0.03 + t) * props.waveAmplitude
        drawX += Math.cos(d.ay * 0.03 + t * 0.7) * props.waveAmplitude * 0.5
      }

      if (props.sparkle) {
        const hash = ((i * 2654435761) ^ (frameCount >> 3)) >>> 0
        const sparkleRadius = hash % 100 < 3 ? rad * 1.8 : rad

        renderCtx.moveTo(drawX + sparkleRadius, drawY)
        renderCtx.arc(drawX, drawY, sparkleRadius, 0, TWO_PI)
      } else {
        renderCtx.moveTo(drawX + rad, drawY)
        renderCtx.arc(drawX, drawY, rad, 0, TWO_PI)
      }
    }

    renderCtx.fill()
    raf = requestAnimationFrame(tick)
  }

  doResize()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(root.value)
  window.addEventListener('resize', resize)
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  window.addEventListener('pointerleave', resetPointer)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  speedInterval = setInterval(updateMouseSpeed, 20)
  raf = requestAnimationFrame(tick)

  cleanupFns.push(() => {
    window.removeEventListener('resize', resize)
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerleave', resetPointer)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })
}

const cleanupFns: Array<() => void> = []

function cleanup() {
  cancelAnimationFrame(raf)

  if (speedInterval) {
    clearInterval(speedInterval)
  }

  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }

  resizeObserver?.disconnect()
  cleanupFns.splice(0).forEach((fn) => fn())
}

watch(
  () => [props.dotRadius, props.dotSpacing],
  async () => {
    await nextTick()

    if (size.w > 0 && size.h > 0) {
      buildDots(size.w, size.h)
    }
  },
)

onMounted(() => {
  setupCanvas()
})

onBeforeUnmount(() => {
  cleanup()
})
</script>

<template>
  <div ref="root" class="dot-field" :class="className">
    <canvas ref="canvas" class="dot-field__canvas" />

    <svg class="dot-field__glow" aria-hidden="true">
      <defs>
        <radialGradient :id="glowId">
          <stop offset="0%" :stop-color="glowColor" />
          <stop offset="100%" stop-color="transparent" />
        </radialGradient>
      </defs>

      <circle
        ref="glowEl"
        cx="-9999"
        cy="-9999"
        :r="glowRadius"
        :fill="`url(#${glowId})`"
        style="opacity: 0; will-change: opacity"
      />
    </svg>
  </div>
</template>

<style scoped>
.dot-field {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.dot-field__canvas,
.dot-field__glow {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.dot-field__glow {
  pointer-events: none;
}
</style>
