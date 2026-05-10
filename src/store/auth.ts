// src/store/auth.ts
// 用户认证状态管理（Pinia Store）
// 管理 JWT Token、用户名、角色等认证状态
// 数据持久化到 localStorage，刷新页面后保持登录状态

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 用户状态数据结构 */
export interface UserState {
  token: string                 // JWT 令牌
  username: string              // 用户名
  role: 'user' | 'admin'       // 角色
}

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 恢复状态，刷新页面后保持登录
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref<'user' | 'admin'>((localStorage.getItem('role') as 'user' | 'admin') || 'user')

  // 计算属性：是否已登录
  const isLoggedIn = computed(() => !!token.value)
  // 计算属性：是否为管理员
  const isAdmin = computed(() => role.value === 'admin')

  /**
   * 保存认证信息
   * 登录成功后调用，同时更新内存状态和 localStorage 持久化
   */
  function setAuth(user: UserState) {
    token.value = user.token
    username.value = user.username
    role.value = user.role
    localStorage.setItem('token', user.token)
    localStorage.setItem('username', user.username)
    localStorage.setItem('role', user.role)
  }

  /**
   * 清除认证信息
   * 退出登录时调用，清除内存状态和 localStorage
   */
  function clearAuth() {
    token.value = ''
    username.value = ''
    role.value = 'user'
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { token, username, role, isLoggedIn, isAdmin, setAuth, clearAuth }
})
