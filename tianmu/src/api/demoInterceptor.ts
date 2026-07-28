import type { InternalAxiosRequestConfig } from 'axios'
import {
  isDemoMode,
  mockBindDevice,
  mockGetDeviceList,
  mockGetLatestData,
  mockSendControlCommand,
} from '@/utils/demo'
import { getAccessToken } from './session'

function mock(data: unknown): never {
  throw { __mock__: true, response: { data } }
}

export async function interceptDemoRequest(
  config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
  if (!isDemoMode()) return config

  const url = config.url || ''
  const method = config.method?.toUpperCase()
  const query = config.params as { force_llm?: boolean } | undefined

  // 认证接口必须访问真实后端，避免演示开关阻断登录和退出。
  if (url.includes('/auth/')) {
    const token = getAccessToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  }

  if (url.includes('/ai/') && query?.force_llm) {
    throw {
      response: {
        data: {
          detail: '当前处于演示模式，强制 LLM 分析不会请求后端。请关闭 demo 模式后重试。',
        },
      },
    }
  }
  if (url.includes('/ai/') && url.endsWith('/score') && method === 'GET') {
    mock({ score: 85, level: 'good', summary: '当前室内环境整体舒适，空气质量良好。' })
  }
  if (url.includes('/ai/') && url.endsWith('/risks') && method === 'GET') {
    mock({ risks: [], highest_level: 'none' })
  }
  if (url.includes('/ai/') && url.endsWith('/suggestions') && method === 'GET') {
    mock({
      source: 'rule',
      suggestions: [
        { icon: 'wind', title: '空气质量良好', desc: '建议定时开窗，保持空气流通' },
        { icon: 'temp', title: '温度适宜', desc: '当前温度适合工作与休息' },
      ],
    })
  }
  if (url.includes('/ai/') && url.endsWith('/weekly-report') && method === 'GET') {
    const today = new Date()
    const days = Array.from({ length: 7 }, (_, index) => {
      const date = new Date(today)
      date.setDate(today.getDate() - (6 - index))
      return {
        date: date.toISOString().slice(0, 10),
        temperature: 24 + (index % 3) * 0.5,
        humidity: 56 + (index % 4),
        aqi: 42 + index * 2,
        sample_count: 48,
      }
    })
    mock({
      days,
      summary: '本周环境整体稳定，各项指标处于舒适范围。',
      source: 'rule',
    })
  }
  if (url.includes('/device/list') && method === 'GET') {
    mock(await mockGetDeviceList())
  }
  if (url.includes('/device/bind') && method === 'POST') {
    mock(await mockBindDevice(
      config.data as { device_id: string; device_name: string },
    ))
  }

  const latestMatch = url.match(/\/data\/([^/]+)\/latest/)
  if (latestMatch?.[1] && method === 'GET') {
    mock(await mockGetLatestData(latestMatch[1]))
  }

  const controlMatch = url.match(/\/control\/([^/]+)/)
  if (controlMatch?.[1] && method === 'POST') {
    const commandData = config.data as { command: string; value: string }
    mock(await mockSendControlCommand(controlMatch[1], commandData))
  }

  throw {
    response: {
      status: 501,
      data: { detail: `演示模式暂未实现该接口：${method || 'UNKNOWN'} ${url}` },
    },
  }
}
