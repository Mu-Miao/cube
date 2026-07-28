import { nextTick, ref } from 'vue'

type ViewTransitionHandle = { finished: Promise<void> }
type SameDocumentTransition = Document & {
  startViewTransition?: (callback: () => void | Promise<void>) => ViewTransitionHandle
}

export function useDashboardTwinTransition() {
  const twinFlightRef = ref<HTMLElement>()
  const twinFlightVisible = ref(false)
  const twinFlightActive = ref(false)
  const twinFlightPlaying = ref(false)
  const twinFlightDirection = ref<'enter' | 'return'>('enter')
  const twinFlightStyle = ref<Record<string, string>>({})
  const twinFlightLabel = ref('Twin Model')
  const twinFlightOffline = ref(false)

  async function runSamePageTransition(update: () => void | Promise<void>) {
    const doc = document as SameDocumentTransition
    if (!doc.startViewTransition || prefersReducedMotion()) {
      await update()
      return false
    }
    const transition = doc.startViewTransition(update)
    await transition.finished.catch(() => undefined)
    return true
  }

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }

  function readTwinRect(selector: string) {
    return document.querySelector<HTMLElement>(selector)?.getBoundingClientRect()
  }

  function readDeviceTwinRect(deviceId: string) {
    const cards = Array.from(
      document.querySelectorAll<HTMLElement>('[data-device-card]'),
    )
    const card = cards.find((item) => item.dataset.deviceCard === deviceId)
    return card
      ?.querySelector<HTMLElement>('.digital-twin')
      ?.getBoundingClientRect()
  }

  function prepareTwinFlight(
    rect: DOMRect,
    device: { device_name?: string; status?: string } | undefined,
    direction: 'enter' | 'return',
  ) {
    twinFlightDirection.value = direction
    twinFlightLabel.value = device?.device_name || 'Twin Model'
    twinFlightOffline.value = device?.status !== 'online'
    twinFlightStyle.value = {
      width: `${Math.max(1, rect.width)}px`,
      height: `${Math.max(1, rect.height)}px`,
      transform: `translate3d(${rect.left}px, ${rect.top}px, 0)`,
    }
    twinFlightPlaying.value = false
    twinFlightActive.value = true
    twinFlightVisible.value = true
  }

  async function animateTwinFlight(
    fromRect: DOMRect | undefined,
    toRect: DOMRect | undefined,
  ) {
    if (!fromRect || !toRect || prefersReducedMotion()) return
    const targetWidth = Math.max(1, toRect.width)
    const targetHeight = Math.max(1, toRect.height)
    const startScaleX = Math.max(0.08, fromRect.width / targetWidth)
    const startScaleY = Math.max(0.08, fromRect.height / targetHeight)
    twinFlightStyle.value = {
      width: `${targetWidth}px`,
      height: `${targetHeight}px`,
      '--twin-flight-from': `translate3d(${fromRect.left}px, ${fromRect.top}px, 0) scale(${startScaleX}, ${startScaleY})`,
      '--twin-flight-to': `translate3d(${toRect.left}px, ${toRect.top}px, 0) scale(1, 1)`,
      '--twin-flight-end-opacity': twinFlightDirection.value === 'return' ? '0.84' : '1',
    }
    twinFlightPlaying.value = true
    twinFlightVisible.value = true
    await nextTick()
    await new Promise<void>((resolve) => window.setTimeout(resolve, 1080))
  }

  async function waitForPaintFrames(count = 1) {
    for (let index = 0; index < count; index += 1) {
      await new Promise<void>((resolve) => {
        window.requestAnimationFrame(() => resolve())
      })
    }
  }

  async function finishTwinFlight() {
    twinFlightVisible.value = false
    await nextTick()
    twinFlightActive.value = false
    twinFlightPlaying.value = false
    twinFlightStyle.value = {}
  }

  return {
    twinFlightRef,
    twinFlightVisible,
    twinFlightActive,
    twinFlightPlaying,
    twinFlightDirection,
    twinFlightStyle,
    twinFlightLabel,
    twinFlightOffline,
    runSamePageTransition,
    prefersReducedMotion,
    readTwinRect,
    readDeviceTwinRect,
    prepareTwinFlight,
    animateTwinFlight,
    waitForPaintFrames,
    finishTwinFlight,
  }
}
