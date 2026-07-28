import { afterEach, describe, expect, it, vi } from 'vitest'
import { api as publicApi } from '@/versions/public/api/client'
import { api as seniorApi } from '@/versions/senior/api/client'

const clients = [
  ['public', publicApi],
  ['senior', seniorApi],
] as const

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe.each(clients)('%s version API client', (_, api) => {
  it('reports a plain-text server error without masking it as a JSON parse error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('Internal Server Error', {
          status: 500,
          headers: { 'Content-Type': 'text/plain' },
        }),
      ),
    )

    await expect(api.login('demo', 'demo123456')).rejects.toThrow(
      '请求失败：500（Internal Server Error）',
    )
  })

  it('reports malformed successful responses as a response-format error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('not-json', {
          status: 200,
          headers: { 'Content-Type': 'text/plain' },
        }),
      ),
    )

    await expect(api.login('demo', 'demo123456')).rejects.toThrow(
      '服务器响应格式错误，请稍后重试',
    )
  })
})
