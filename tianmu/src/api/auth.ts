// src/api/auth.ts
// 用户认证 API 封装
// 提供注册、登录、登出接口的类型定义和请求方法

import api from './index'
import type { ApiResponse } from './device'

function unwrapData<T>(res: unknown): T {
  const response = res as ApiResponse<T>
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data as T
  }
  return res as T
}

/** 登录请求参数 */
export interface LoginParams {
  username: string  // 用户名
  password: string  // 密码
}

/** 注册请求参数 */
export interface RegisterParams {
  username: string  // 用户名
  password: string  // 密码
}

/** 登录响应数据：JWT Token 信息 */
export interface LoginResult {
  access_token: string  // JWT 访问令牌
  token_type: string    // Token 类型，固定为 bearer
  expires_in: number    // Token 有效期（秒）
}

/**
 * 用户登录
 * POST /api/v1/auth/login
 * 返回 JWT Token，前端存储到 localStorage
 */
export const login = (data: LoginParams) => {
  return api.post('/auth/login', data).then((res) => unwrapData<LoginResult>(res))
}

/**
 * 用户注册
 * POST /api/v1/auth/register
 * 创建新用户账号，注册成功后跳转到登录页
 */
export const register = (data: RegisterParams) => {
  return api.post('/auth/register', data).then((res) => unwrapData<{ id: number }>(res))
}

/**
 * 用户登出
 * POST /api/v1/auth/logout
 * 后端清除会话（可选实现），前端直接清除本地 Token
 */
export const logout = () => {
  return api.post('/auth/logout').then((r) => r.data) as Promise<unknown>
}
