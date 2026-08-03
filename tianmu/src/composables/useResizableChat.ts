import { onUnmounted, ref } from 'vue'

const MIN_CHAT_WIDTH = 280
const MAX_CHAT_WIDTH = 680

export function useResizableChat() {
  const chatOpen = ref(false)
  const chatWidth = ref(380)
  const isDragging = ref(false)

  function onResizeStart(event: MouseEvent) {
    event.preventDefault()
    isDragging.value = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onResizeMove)
    window.addEventListener('mouseup', onResizeEnd)
  }

  function onResizeMove(event: MouseEvent) {
    if (!isDragging.value) return
    const widthFromRight = window.innerWidth - event.clientX
    chatWidth.value = Math.max(MIN_CHAT_WIDTH, Math.min(MAX_CHAT_WIDTH, widthFromRight))
  }

  function onResizeEnd() {
    if (!isDragging.value) return
    isDragging.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    window.removeEventListener('mousemove', onResizeMove)
    window.removeEventListener('mouseup', onResizeEnd)
  }

  onUnmounted(() => {
    window.removeEventListener('mousemove', onResizeMove)
    window.removeEventListener('mouseup', onResizeEnd)
    onResizeEnd()
  })

  return {
    chatOpen,
    chatWidth,
    isDragging,
    onResizeStart,
  }
}
