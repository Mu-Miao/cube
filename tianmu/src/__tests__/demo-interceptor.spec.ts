import service from '@/api'
import { afterEach, describe, expect, it, vi } from 'vitest'

afterEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('demo API interceptor', () => {
  it('returns device mock data without calling a network adapter', async () => {
    localStorage.setItem('demo', 'true')
    const adapter = vi.fn()
    const previous = service.defaults.adapter
    service.defaults.adapter = adapter
    try {
      const devices = await service.get('/device/list')
      expect(devices).toHaveLength(2)
      expect(adapter).not.toHaveBeenCalled()
    } finally {
      if (previous) service.defaults.adapter = previous
      else delete service.defaults.adapter
    }
  })

  it('rejects unknown demo endpoints explicitly', async () => {
    localStorage.setItem('demo', 'true')
    await expect(service.get('/unknown')).rejects.toMatchObject({
      response: {
        status: 501,
      },
    })
  })
})
