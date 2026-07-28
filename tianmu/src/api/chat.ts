// src/api/chat.ts
// 小眠 AI 对话 — 通过后端 /api/v1/chat/stream SSE 代理
// API Key 安全存储在后端，前端不接触密钥

import { isDemoMode } from '@/utils/demo'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

/**
 * 流式调用后端聊天 API
 * @param messages 对话历史（不含 system 消息，后端自动拼接）
 * @param onChunk 每次收到文本片段时回调
 * @param onDone 全部完成时回调
 * @param onError 出错时回调
 * @returns AbortController，可用于取消请求
 */
export function streamChat(
  messages: ChatMessage[],
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
  deviceId?: string,
): AbortController {
  const controller = new AbortController()

  // 演示模式：使用本地模拟回复
  if (isDemoMode()) {
    simulateResponse(messages, onChunk, onDone)
    return controller
  }

  const token = localStorage.getItem('token') || ''

  // 只发送 user/assistant 消息给后端（后端自行拼接 system 提示词）
  const filteredMessages = messages
    .filter((m) => m.role !== 'system')
    .map((m) => ({ role: m.role, content: m.content }))

  fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ messages: filteredMessages, device_id: deviceId || undefined }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        throw new Error(`请求失败 (${response.status}): ${errorText || response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法读取响应流')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed || !trimmed.startsWith('data: ')) continue

          const data = trimmed.slice(6)
          if (data === '[DONE]') {
            onDone()
            return
          }

          try {
            const json = JSON.parse(data) as { content?: string }
            if (json.content) {
              onChunk(json.content)
            }
          } catch {
            // 忽略无法解析的行
          }
        }
      }

      onDone()
    })
    .catch((err) => {
      if (err.name === 'AbortError') return
      onError(err instanceof Error ? err : new Error(String(err)))
    })

  return controller
}

/**
 * 模拟回复（演示模式兜底）
 */
async function simulateResponse(
  messages: ChatMessage[],
  onChunk: (text: string) => void,
  onDone: () => void,
) {
  const lastUserMsg = messages.filter((m) => m.role === 'user').pop()?.content || ''

  const mockReplies: Array<[RegExp, string]> = [
    [
      /温度|热|冷|暖/,
      '目前温度数据正常，如果觉得偏热可以开一下空调或者通通风哦~ 保持舒适最重要！',
    ],
    [
      /湿度|潮|干/,
      '湿度方面，建议保持在 40%-60% 之间最舒适。如果偏高可以开一下除湿功能~',
    ],
    [
      /空气|AQI|质量|PM/,
      '空气质量要关注 AQI 指数哦！如果 AQI 超过 100 建议开一下空气净化器，关窗减少外界污染~',
    ],
    [
      /灯|光|亮/,
      '灯光控制可以在控制面板里操作哦~ 支持白/红/绿/蓝四种颜色，还可以调节亮度。',
    ],
    [/你好|嗨|hi|hello|hey/i, '你好呀！我是小眠，你的桌面魔方小助手~ 有什么想问的吗？'],
    [/谢谢|感谢|thx/i, '不客气！随时找我聊天呀~ 我会一直陪着你的！'],
  ]

  let reply = '我是小眠，你的桌面魔方小助手！你可以问我关于设备状态、环境数据的问题哦~ 比如「温度多少」「空气怎么样」「怎么开灯」之类的。'

  for (const [pattern, text] of mockReplies) {
    if (pattern.test(lastUserMsg)) {
      reply = text
      break
    }
  }

  // 逐字符模拟流式输出
  const chars = [...reply]
  for (const char of chars) {
    await new Promise((resolve) => setTimeout(resolve, 30 + Math.random() * 40))
    onChunk(char)
  }

  onDone()
}
