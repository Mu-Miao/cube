import axios, { AxiosError } from 'axios'
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import service from '@/api'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/api/session'

function response(
  config: InternalAxiosRequestConfig,
  status: number,
  data: unknown,
): AxiosResponse {
  return {
    config,
    status,
    statusText: status === 401 ? 'Unauthorized' : 'OK',
    headers: {},
    data,
  }
}

afterEach(() => {
  clearAccessToken()
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('Axios 401 recovery', () => {
  it('refreshes once and retries the original request', async () => {
    const previous = service.defaults.adapter
    let attempts = 0
    service.defaults.adapter = async (config) => {
      attempts += 1
      if (attempts === 1) {
        throw new AxiosError(
          'unauthorized',
          'ERR_BAD_REQUEST',
          config,
          undefined,
          response(config, 401, { detail: 'expired' }),
        )
      }
      return response(config, 200, { code: 0, data: { ok: true } })
    }
    vi.spyOn(axios, 'post').mockResolvedValue({
      data: { data: { access_token: 'refreshed-token' } },
    })

    try {
      await expect(service.get('/device/list')).resolves.toEqual({ ok: true })
      expect(attempts).toBe(2)
      expect(getAccessToken()).toBe('refreshed-token')
    } finally {
      if (previous) service.defaults.adapter = previous
      else delete service.defaults.adapter
    }
  })

  it('clears auth and emits expiration event when refresh fails', async () => {
    const previous = service.defaults.adapter
    service.defaults.adapter = async (config) => {
      throw new AxiosError(
        'unauthorized',
        'ERR_BAD_REQUEST',
        config,
        undefined,
        response(config, 401, { detail: 'expired' }),
      )
    }
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('refresh failed'))
    const expired = vi.fn()
    window.addEventListener('cube:auth-expired', expired)
    setAccessToken('stale-token')

    try {
      await expect(service.get('/device/list')).rejects.toBeInstanceOf(AxiosError)
      expect(getAccessToken()).toBe('')
      expect(expired).toHaveBeenCalledOnce()
    } finally {
      window.removeEventListener('cube:auth-expired', expired)
      if (previous) service.defaults.adapter = previous
      else delete service.defaults.adapter
    }
  })
})
