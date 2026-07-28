import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useWebSocket } from '@/composables/useWebSocket'
import { clearAccessToken, setAccessToken } from '@/api/session'

class FakeWebSocket {
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSED = 3
  static instances: FakeWebSocket[] = []

  readyState = FakeWebSocket.CONNECTING
  sent: string[] = []
  closeArgs: unknown[] = []
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: (() => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(readonly url: string) {
    FakeWebSocket.instances.push(this)
  }

  open() {
    this.readyState = FakeWebSocket.OPEN
    this.onopen?.()
  }

  send(value: string) {
    this.sent.push(value)
  }

  close(...args: unknown[]) {
    this.closeArgs = args
    this.readyState = FakeWebSocket.CLOSED
    this.onclose?.()
  }
}

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  FakeWebSocket.instances = []
  clearAccessToken()
  localStorage.clear()
})

describe('WebSocket heartbeat recovery', () => {
  it('authenticates, closes a half-open connection, and reconnects', async () => {
    vi.useFakeTimers()
    vi.stubGlobal('WebSocket', FakeWebSocket)
    setAccessToken('memory-token')

    let socket!: ReturnType<typeof useWebSocket>
    const wrapper = mount(defineComponent({
      setup() {
        socket = useWebSocket('/ws')
        return () => h('div')
      },
    }))

    socket.connect()
    const first = FakeWebSocket.instances[0]!
    first.open()
    expect(JSON.parse(first.sent[0]!)).toEqual({
      type: 'auth',
      data: { token: 'memory-token' },
    })

    await vi.advanceTimersByTimeAsync(30_000)
    expect(JSON.parse(first.sent[first.sent.length - 1]!)).toEqual({ type: 'ping', data: {} })
    await vi.advanceTimersByTimeAsync(10_000)
    expect(first.closeArgs).toEqual([4000, 'pong timeout'])

    await vi.advanceTimersByTimeAsync(1_000)
    expect(FakeWebSocket.instances).toHaveLength(2)
    wrapper.unmount()
  })
})
