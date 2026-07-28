import { afterEach, describe, expect, it, vi } from 'vitest'
import service from '@/api'
import { api as publicApi } from '@/versions/public/api/client'
import { api as seniorApi } from '@/versions/senior/api/client'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('shared version API client', () => {
  it('uses one client implementation for public and senior versions', () => {
    expect(publicApi).toBe(seniorApi)
  })

  it('routes version login through the credentialed Axios client', async () => {
    const response = {
      access_token: 'memory-only-token',
      token_type: 'bearer',
      expires_in: 900,
    }
    const post = vi.spyOn(service, 'post').mockResolvedValue(response)

    await expect(publicApi.login('demo', 'demo123456')).resolves.toEqual(response)
    expect(post).toHaveBeenCalledWith('/auth/login', {
      username: 'demo',
      password: 'demo123456',
    })
  })
})
