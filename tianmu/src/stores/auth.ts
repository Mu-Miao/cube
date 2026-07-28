// src/stores/auth.ts
// 用户认证状态管理（Pinia Store）
// 管理 JWT Token、用户名、角色等认证状态
// Access Token 仅保存在内存；刷新页面时由 HttpOnly Refresh Cookie 恢复会话

import { defineStore } from 'pinia'
import { computed, onScopeDispose, ref } from 'vue'
import {
  clearAccessToken,
  getAccessToken,
  getSessionIdentity,
  onAccessTokenChange,
  setAccessToken,
} from '@/api/session'
import { logout as logoutApi } from '@/api/auth'

/** 用户状态数据结构 */
export interface UserState {
  token: string                 // JWT 令牌
  username: string              // 用户名
  role: 'user' | 'admin'       // 角色
}

export const useAuthStore = defineStore('auth', () => {
  const restoredIdentity = getSessionIdentity()
  const token = ref(getAccessToken())
  const username = ref(restoredIdentity.username)
  const role = ref<'user' | 'admin'>(restoredIdentity.role)
  const stopTokenSync = onAccessTokenChange((nextToken) => {
    token.value = nextToken
  })
  onScopeDispose(stopTokenSync)

  // 计算属性：是否已登录
  const isLoggedIn = computed(() => !!token.value)
  // 计算属性：是否为管理员
  const isAdmin = computed(() => role.value === 'admin')

  /**
   * 保存认证信息
   * 登录成功后调用，只更新当前页面内存状态
   */
  function setAuth(user: UserState) {
    token.value = user.token
    setAccessToken(user.token)
    username.value = user.username
    role.value = user.role
  }

  /**
   * 清除认证信息
   * 退出登录或刷新失败时调用，只清除内存认证状态
   */
  function clearAuth() {
    clearAccessToken()
    token.value = ''
    username.value = ''
    role.value = 'user'
  }

  async function signOut() {
    try {
      await logoutApi()
    } finally {
      clearAuth()
    }
  }

  return { token, username, role, isLoggedIn, isAdmin, setAuth, clearAuth, signOut }
})
