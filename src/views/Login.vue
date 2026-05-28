<!-- Login.vue -->
<!-- 用户登录页面 -->
<!-- 提供用户名/密码表单，调用后端登录接口获取 JWT Token -->
<!-- 支持一键演示模式（快捷进入管理员演示状态） -->
<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo + 页面标题 -->
      <div class="login-header">
        <div class="login-logo">
          <svg viewBox="0 0 48 48" class="cube-icon" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 简化魔方 SVG 图标 -->
            <rect x="8" y="8" width="14" height="14" rx="2" fill="#06B6D4" opacity="0.9" />
            <rect x="26" y="8" width="14" height="14" rx="2" fill="#22D3EE" opacity="0.7" />
            <rect x="8" y="26" width="14" height="14" rx="2" fill="#0891B2" opacity="0.7" />
            <rect x="26" y="26" width="14" height="14" rx="2" fill="#06B6D4" opacity="0.5" />
          </svg>
        </div>
        <h1 class="login-title">智能桌面魔方</h1>
        <p class="login-subtitle">MVP Demo 系统</p>
      </div>

      <!-- 登录表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <!-- 用户名输入 -->
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </el-form-item>

        <!-- 密码输入 -->
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          />
        </el-form-item>

        <!-- 登录按钮 -->
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          登 录
        </el-button>

        <!-- 演示模式快捷入口：一键进入管理员演示状态 -->
        <div class="demo-section">
          <div class="demo-divider">
            <span>竞赛演示快捷入口</span>
          </div>
          <el-button type="success" size="large" plain class="demo-btn" @click="handleDemoLogin">
            一键演示 (管理员)
          </el-button>
        </div>

        <!-- 注册链接 -->
        <div class="register-link">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { login } from '@/api/auth'
import { enableDemoMode } from '@/utils/demo'

defineOptions({
  name: 'LoginPage',
})

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>() // 表单引用，用于表单校验
const loading = ref(false) // 登录按钮加载状态

// 表单数据
const form = reactive({
  username: '',
  password: '',
})

// 表单校验规则
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

/**
 * 处理用户登录
 * 1. 校验表单
 * 2. 调用登录 API
 * 3. 存储 Token 到 authStore 和 localStorage
 * 4. 跳转到控制台
 */
async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login({ username: form.username, password: form.password })
    authStore.setAuth({
      token: res.access_token,
      username: form.username,
      role: 'user',
    })
    ElMessage.success('登录成功')
    await router.push('/dashboard')
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      '登录失败，请检查用户名和密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

/**
 * 处理一键演示模式
 * 不经过后端，直接设置管理员 Token 和用户名
 * 适用于没有后端环境时的竞赛演示
 */
async function handleDemoLogin() {
  loading.value = true
  try {
    // 启用演示模式：设置 localStorage 标志
    enableDemoMode()
    await new Promise((resolve) => setTimeout(resolve, 300))
    authStore.setAuth({
      token: 'demo-jwt-token-admin',
      username: 'admin',
      role: 'admin',
    })
    ElMessage.success('已进入演示模式')
    // 携带 ?demo=true 参数跳转，确保页面识别演示模式
    router.push('/dashboard?demo=true')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 登录页面布局：全屏深空背景 + 玻璃拟态卡片 */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-canvas);
  background-image:
    linear-gradient(135deg, rgba(6, 182, 212, 0.09), transparent 32%),
    linear-gradient(225deg, rgba(163, 230, 53, 0.055), transparent 34%),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.028) 0 1px, transparent 1px 36px),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.02) 0 1px, transparent 1px 36px);
  padding: 24px;
}

/* 登录卡片：玻璃拟态 */
.login-card {
  position: relative;
  overflow: hidden;
  width: 420px;
  padding: 40px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.015)),
    var(--bg-card);
  backdrop-filter: blur(20px) saturate(1.3);
  -webkit-backdrop-filter: blur(20px) saturate(1.3);
  border: var(--border-glass);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg), 0 0 40px rgba(6, 182, 212, 0.08);
  animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-primary), var(--color-cube-accent), var(--color-cube-violet));
  background-size: 200% 100%;
  animation: border-flow 4s linear infinite;
}

.login-card::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 36%;
  background: repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.045) 0 1px, transparent 1px 16px);
  opacity: 0.08;
  pointer-events: none;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

/* 魔方 Logo */
.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.cube-icon {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 0 16px rgba(6, 182, 212, 0.5));
}

.login-title {
  font-size: 28px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.login-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.login-form {
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.login-btn {
  width: 100%;
  margin-top: 12px;
}

/* 演示模式区域 */
.demo-section {
  margin-top: 24px;
}

.demo-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}
.demo-divider::before,
.demo-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.16), transparent);
}

.demo-btn {
  width: 100%;
}

.register-link {
  text-align: center;
  margin-top: 16px;
  color: var(--text-secondary);
}
.register-link a {
  color: var(--color-cube-primary);
  text-decoration: none;
  font-weight: 500;
}
.register-link a:hover {
  color: var(--primary-light);
  text-decoration: underline;
}
</style>
