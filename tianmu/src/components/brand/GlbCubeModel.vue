<template>
  <div
    class="digital-twin glb-cube"
    :class="[
      `glb-cube--${size}`,
      {
        'glb-cube--offline': offline,
        'glb-cube--interactive': interactive,
        'glb-cube--dragging': isDragging,
      },
    ]"
    @pointerdown="handlePointerDown"
    @pointermove="handlePointerMove"
    @pointerup="handlePointerUp"
    @pointercancel="handlePointerUp"
    @pointerleave="handlePointerUp"
  >
    <div class="glb-cube__aura" aria-hidden="true"></div>
    <canvas ref="canvasRef" class="glb-cube__canvas" :aria-label="label"></canvas>
    <div class="glb-cube__grid" aria-hidden="true"></div>
    <div v-if="showLabel" class="glb-cube__label">
      <span>{{ label }}</span>
      <small>{{ offline ? 'OFFLINE' : 'GLB MODEL' }}</small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

const modelUrl = '/mzh5(1).glb'

defineOptions({ name: 'GlbCubeModel' })

const props = withDefaults(
  defineProps<{
    label?: string
    offline?: boolean
    showLabel?: boolean
    size?: 'mini' | 'hero'
    interactive?: boolean
    autoRotate?: boolean
  }>(),
  {
    label: 'Cube Model',
    offline: false,
    showLabel: false,
    size: 'mini',
    interactive: false,
    autoRotate: true,
  },
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isDragging = ref(false)

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let modelPivot: THREE.Group | null = null
let model: THREE.Group | null = null
let dracoLoader: DRACOLoader | null = null
let resizeObserver: ResizeObserver | null = null
let frameId = 0
let yaw = THREE.MathUtils.degToRad(18)
let pitch = THREE.MathUtils.degToRad(8)
let dragStartX = 0
let dragStartY = 0
let dragStartYaw = yaw
let dragStartPitch = pitch

function fitCameraToModel(object: THREE.Object3D) {
  if (!camera) return

  const box = new THREE.Box3().setFromObject(object)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxSize = Math.max(size.x, size.y, size.z)
  const distance = maxSize / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2))

  object.position.sub(center)
  camera.position.set(distance * 0.7, distance * 0.58, distance * 1.15)
  camera.near = Math.max(distance / 100, 0.01)
  camera.far = distance * 100
  camera.lookAt(0, 0, 0)
  camera.updateProjectionMatrix()
}

function resizeRenderer() {
  const canvas = canvasRef.value
  if (!canvas || !renderer || !camera) return

  const { width, height } = canvas.getBoundingClientRect()
  const nextWidth = Math.max(1, Math.floor(width))
  const nextHeight = Math.max(1, Math.floor(height))

  renderer.setSize(nextWidth, nextHeight, false)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  camera.aspect = nextWidth / nextHeight
  camera.updateProjectionMatrix()
}

function animate() {
  if (!renderer || !scene || !camera) return

  frameId = window.requestAnimationFrame(animate)

  if (modelPivot) {
    if (!isDragging.value && props.autoRotate) yaw += 0.006
    modelPivot.rotation.set(pitch, yaw, Math.PI)
  }

  renderer.render(scene, camera)
}

function handlePointerDown(event: PointerEvent) {
  if (!props.interactive) return

  isDragging.value = true
  dragStartX = event.clientX
  dragStartY = event.clientY
  dragStartYaw = yaw
  dragStartPitch = pitch
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function handlePointerMove(event: PointerEvent) {
  if (!props.interactive || !isDragging.value) return

  const deltaX = event.clientX - dragStartX
  const deltaY = event.clientY - dragStartY
  yaw = dragStartYaw + deltaX * 0.01
  pitch = THREE.MathUtils.clamp(dragStartPitch + deltaY * 0.008, -0.75, 0.75)
}

function handlePointerUp(event: PointerEvent) {
  if (!isDragging.value) return

  isDragging.value = false
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) target.releasePointerCapture(event.pointerId)
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  scene = new THREE.Scene()
  modelPivot = new THREE.Group()
  scene.add(modelPivot)
  camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100)
  renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: 'high-performance',
  })
  renderer.outputColorSpace = THREE.SRGBColorSpace

  const keyLight = new THREE.DirectionalLight(0xffffff, 3.4)
  keyLight.position.set(3, 5, 4)
  scene.add(keyLight)

  const fillLight = new THREE.DirectionalLight(0x67e8f9, 2.2)
  fillLight.position.set(-4, 2, 3)
  scene.add(fillLight)
  scene.add(new THREE.AmbientLight(0xbdefff, 2.4))

  resizeObserver = new ResizeObserver(resizeRenderer)
  resizeObserver.observe(canvas)
  resizeRenderer()

  dracoLoader = new DRACOLoader()
  dracoLoader.setDecoderPath(`${import.meta.env.BASE_URL}draco/`)
  const gltfLoader = new GLTFLoader()
  gltfLoader.setDRACOLoader(dracoLoader)

  gltfLoader.load(modelUrl, (gltf) => {
    model = gltf.scene
    model.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = false
        child.receiveShadow = false
        child.frustumCulled = false
      }
    })
    modelPivot?.add(model)
    fitCameraToModel(model)
  })

  animate()
})

onBeforeUnmount(() => {
  if (frameId) window.cancelAnimationFrame(frameId)
  resizeObserver?.disconnect()
  renderer?.dispose()
  dracoLoader?.dispose()
  scene?.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.geometry.dispose()
      const materials = Array.isArray(object.material) ? object.material : [object.material]
      materials.forEach((material) => material.dispose())
    }
  })
  renderer = null
  scene = null
  camera = null
  modelPivot = null
  model = null
  dracoLoader = null
})
</script>

<style scoped>
.glb-cube {
  --twin-size: 72px;

  position: relative;
  width: var(--twin-size);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  isolation: isolate;
  touch-action: none;
}

.glb-cube--hero {
  --twin-size: min(42vw, 420px);
}

.glb-cube--offline {
  filter: grayscale(0.7);
  opacity: 0.66;
}

.glb-cube--interactive {
  cursor: grab;
}

.glb-cube--dragging {
  cursor: grabbing;
}

.glb-cube__canvas {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: block;
}

.glb-cube__aura {
  position: absolute;
  inset: 4%;
  border-radius: 50%;
  background:
    radial-gradient(circle, rgba(34, 211, 238, 0.32), transparent 62%),
    radial-gradient(circle at 62% 30%, rgba(163, 230, 53, 0.18), transparent 54%);
  filter: blur(10px);
  animation: glb-cube-breathe 3.8s ease-in-out infinite;
  z-index: -2;
}

.glb-cube__grid {
  position: absolute;
  inset: 10%;
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

.glb-cube__label {
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

.glb-cube__label small {
  font-family: var(--font-mono);
  font-size: 9px;
  color: rgba(163, 230, 53, 0.78);
}

@keyframes glb-cube-breathe {
  0%, 100% { transform: scale(0.96); opacity: 0.78; }
  50% { transform: scale(1.08); opacity: 1; }
}
</style>
