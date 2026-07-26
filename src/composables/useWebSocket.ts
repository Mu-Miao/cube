// src/composables/useWebSocket.ts
// WebSocket 封装 Hook（组合式函数）
// 提供 WebSocket 连接管理、认证、消息订阅/发送、自动清理功能
// 用于 Dashboard 页面接收实时传感器数据推送和设备状态变更
// 支持演示模式：通过 demo=true 参数激活模拟 WebSocket 行为

import { ref, onUnmounted } from 'vue'
import { isDemoMode, mockConnect, mockOn, mockSend, mockDisconnect } from '@/utils/demo'

export function useWebSocket(url: string) {
  // WebSocket 实例
  const ws = ref<WebSocket | null>(null)
  // 连接状态
  const connected = ref(false)
  // 消息处理器映射表：消息类型 → 回调函数数组
  const messageHandlers = new Map<string, ((data: Record<string, unknown>) => void)[]>()
  // 是否为演示模式
  const demoMode = ref(isDemoMode())
  let reconnectTimer: number | null = null
  let reconnectAttempts = 0
  let manuallyDisconnected = false
  const pendingMessages: { type: string; data: Record<string, unknown> }[] = []
  const MAX_RECONNECT_DELAY = 30000

  function resolveWebSocketBaseUrl() {
    const configured = import.meta.env.VITE_WS_BASE_URL as string | undefined
    const isBrowserLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname)

    if (configured && (isBrowserLocalhost || !configured.includes('localhost'))) {
      return configured.replace(/\/$/, '')
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}`
  }

  function clearReconnectTimer() {
    if (reconnectTimer !== null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function scheduleReconnect() {
    if (manuallyDisconnected || demoMode.value || reconnectTimer !== null) return
    const delay = Math.min(1000 * 2 ** reconnectAttempts, MAX_RECONNECT_DELAY)
    reconnectAttempts += 1
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  /**
   * 建立 WebSocket 连接
   * 演示模式下使用模拟连接，否则创建真实 WebSocket
   * 连接成功后自动发送认证消息（携带 JWT Token）
   * 服务端认证通过后才会开始推送业务消息
   */
  function connect() {
    manuallyDisconnected = false
    clearReconnectTimer()

    // 演示模式：使用模拟 WebSocket 行为
    if (demoMode.value) {
      mockConnect()

      // 100ms 后模拟连接成功并发送认证
      setTimeout(() => {
        connected.value = true
        const token = localStorage.getItem('token')
        if (token) {
          mockSend('auth', { token })
        }
      }, 100)
      return
    }

    // 真实模式：创建 WebSocket 连接
    const wsUrl = `${resolveWebSocketBaseUrl()}${url}`
    if (ws.value?.readyState === WebSocket.OPEN || ws.value?.readyState === WebSocket.CONNECTING) {
      return
    }
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
      // 连接成功后立即发送认证消息（使用统一的嵌套格式）
      const token = localStorage.getItem('token')
      if (token) {
        send('auth', { token })
      }
      while (pendingMessages.length > 0) {
        const message = pendingMessages.shift()
        if (message) send(message.type, message.data)
      }
    }

    /**
     * 接收服务端消息
     * 根据消息类型（type 字段）分发到对应的处理器
     * 支持的消息类型：
     *   - sensor_data: 传感器数据推送
     *   - device_status: 设备状态变更
     *   - control_result: 指令执行结果
     *   - auth_result: 认证结果
     *   - pong: 心跳响应
     */
    ws.value.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as {
          type: string
          data?: Record<string, unknown>
          [key: string]: unknown
        }
        const handlers = messageHandlers.get(msg.type) || []
        handlers.forEach((h) => h(msg.data ?? msg))
      } catch (error) {
        console.error('WebSocket message parse error:', error)
      }
    }

    // 连接关闭时更新状态
    ws.value.onclose = () => {
      connected.value = false
      ws.value = null
      scheduleReconnect()
    }

    // 连接错误时打印日志
    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  /**
   * 注册消息处理器
   * 监听指定类型的消息，收到后调用回调函数
   * 同一类型可注册多个处理器
   * 演示模式下自动注册到模拟 WebSocket
   */
  function on(type: string, handler: (data: Record<string, unknown>) => void) {
    // 演示模式：注册到模拟 WebSocket
    if (demoMode.value) {
      mockOn(type, handler)
      return
    }
    // 真实模式：注册到本地处理器映射表
    const handlers = messageHandlers.get(type) || []
    handlers.push(handler)
    messageHandlers.set(type, handlers)
  }

  /**
   * 向服务端发送消息
   * 自动序列化为 JSON，附加 type 字段
   * 演示模式下使用模拟发送
   */
  function send(type: string, data: Record<string, unknown>) {
    // 演示模式：使用模拟发送
    if (demoMode.value) {
      mockSend(type, data)
      return
    }
    // 真实模式：通过真实 WebSocket 发送
    if (ws.value?.readyState !== WebSocket.OPEN) {
      pendingMessages.push({ type, data })
      return
    }
    ws.value.send(JSON.stringify({ type, data }))
  }

  /**
   * 断开 WebSocket 连接
   * 演示模式下断开模拟连接，否则关闭真实 WebSocket
   */
  function disconnect() {
    manuallyDisconnected = true
    clearReconnectTimer()
    // 演示模式：断开模拟连接
    if (demoMode.value) {
      mockDisconnect()
      connected.value = false
      return
    }
    // 真实模式：关闭真实 WebSocket
    ws.value?.close()
    ws.value = null
    connected.value = false
  }

  // 组件卸载时自动断开连接，防止内存泄漏
  onUnmounted(disconnect)

  return { connected, connect, disconnect, on, send }
}
