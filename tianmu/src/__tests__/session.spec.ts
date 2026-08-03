import axios from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  bootstrapSession,
  clearAccessToken,
  getAccessToken,
  getSessionIdentity,
  onAccessTokenChange,
  refreshAccessToken,
  setAccessToken,
} from '@/api/session'

function token(payload: Record<string, unknown>) {
  return [
    btoa(JSON.stringify({ alg: 'none' })),
    btoa(JSON.stringify(payload)),
    'signature',
  ].join('.')
}

afterEach(() => {
  clearAccessToken()
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('refresh-cookie session', () => {
  it('restores access token in memory with credentialed refresh request', async () => {
    const accessToken = token({ username: 'alice', role: 'admin' })
    const post = vi.spyOn(axios, 'post').mockResolvedValue({
      data: { data: { access_token: accessToken } },
    })

    await expect(bootstrapSession()).resolves.toBe(true)
    expect(getAccessToken()).toBe(accessToken)
    expect(getSessionIdentity()).toEqual({ username: 'alice', role: 'admin' })
    expect(post).toHaveBeenCalledWith(
      '/api/v1/auth/refresh',
      {},
      { withCredentials: true },
    )
  })

  it('clears memory when refresh cookie is invalid', async () => {
    setAccessToken('stale')
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('unauthorized'))
    await expect(bootstrapSession()).resolves.toBe(false)
    expect(getAccessToken()).toBe('')
  })

  it('restores an in-memory admin identity for persisted demo mode', async () => {
    localStorage.setItem('demo', 'true')
    const post = vi.spyOn(axios, 'post')

    await expect(bootstrapSession()).resolves.toBe(true)
    expect(getSessionIdentity()).toEqual({ username: 'admin', role: 'admin' })
    expect(post).not.toHaveBeenCalled()
  })

  it('deduplicates concurrent refresh requests', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({
      data: { data: { access_token: 'next-token' } },
    })
    await Promise.all([refreshAccessToken(), refreshAccessToken()])
    expect(post).toHaveBeenCalledTimes(1)
  })

  it('notifies the auth store bridge when the in-memory token changes', () => {
    const listener = vi.fn()
    const unsubscribe = onAccessTokenChange(listener)

    setAccessToken('next-token')
    clearAccessToken()
    unsubscribe()
    setAccessToken('ignored')

    expect(listener.mock.calls).toEqual([['next-token'], ['']])
  })
})
