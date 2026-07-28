import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import type { RouteLocationNormalized } from 'vue-router'
import { authNavigationGuard } from '@/router'
import { useAuthStore } from '@/stores/auth'

function route(
  name: string,
  requiresAuth = false,
): RouteLocationNormalized {
  return {
    name,
    meta: { requiresAuth },
  } as unknown as RouteLocationNormalized
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})

describe('auth route guard', () => {
  it('redirects anonymous users from protected routes', () => {
    expect(authNavigationGuard(route('dashboard', true))).toEqual({ name: 'login' })
  })

  it('allows demo mode through protected routes', () => {
    localStorage.setItem('demo', 'true')
    expect(authNavigationGuard(route('dashboard', true))).toBeUndefined()
  })

  it('keeps authenticated users away from login/register', () => {
    useAuthStore().setAuth({ token: 'token', username: 'alice', role: 'user' })
    expect(authNavigationGuard(route('login'))).toEqual({ path: '/public' })
  })
})
