<!-- Register.vue -->
<!-- 用户注册页面 -->
<!-- 提供用户名/密码/确认密码表单，调用后端注册接口创建账号 -->
<!-- 注册成功后跳转到登录页 -->
<template>
  <div class="register-page">
    <div class="register-card">
      <!-- Logo + 标题 -->
      <div class="register-header">
        <div class="register-logo">
          <svg viewBox="0 0 48 48" class="cube-icon" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 简化魔方 SVG 图标 -->
            <rect x="8" y="8" width="14" height="14" rx="2" fill="#06B6D4" opacity="0.9" />
            <rect x="26" y="8" width="14" height="14" rx="2" fill="#22D3EE" opacity="0.7" />
            <rect x="8" y="26" width="14" height="14" rx="2" fill="#0891B2" opacity="0.7" />
            <rect x="26" y="26" width="14" height="14" rx="2" fill="#06B6D4" opacity="0.5" />
          </svg>
        </div>
        <h2 class="register-title">注册账号</h2>
      </div>

      <!-- 注册表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleRegister"
      >
        <!-- 用户名 -->
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
          />
        </el-form-item>

        <!-- 确认密码 -->
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            size="large"
            show-password
          />
        </el-form-item>

        <!-- 注册按钮 -->
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="register-btn"
          @click="handleRegister"
        >
          注 册
        </el-button>

        <!-- 登录链接 -->
        <div class="login-link">
          已有账号？
          <router-link to="/login">立即登录</router-link>
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
import { register } from '@/api/auth'

defineOptions({
  name: 'RegisterPage',
})

const router = useRouter()
const formRef = ref<FormInstance>()  // 表单引用
const loading = ref(false)           // 按钮加载状态

// 表单数据
const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

/**
 * 自定义校验器：确认密码必须与密码一致
 */
const validateConfirmPassword = (
  _rule: unknown,
  value: string,
  callback: (error?: Error) => void,
) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单校验规则
const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3-50个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

/**
 * 处理用户注册
 * 1. 校验表单（含密码一致性）
 * 2. 调用注册 API
 * 3. 注册成功后延迟跳转到登录页
 */
async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await register({ username: form.username, password: form.password })
    ElMessage.success('注册成功，正在跳转到登录页...')
    setTimeout(() => {
      router.push('/login')
    }, 1000)
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg = error.response?.data?.detail || error.response?.data?.message || '注册失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 注册页面布局：全屏深空背景 + 玻璃拟态卡片 */
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-canvas);
  background-image:
    linear-gradient(135deg, rgba(6, 182, 212, 0.09), transparent 32%),
    linear-gradient(225deg, rgba(139, 92, 246, 0.06), transparent 34%),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.028) 0 1px, transparent 1px 36px),
    repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.02) 0 1px, transparent 1px 36px);
  padding: 24px;
}

/* 注册卡片：玻璃拟态 */
.register-card {
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
  box-shadow: var(--shadow-lg), 0 0 40px rgba(139, 92, 246, 0.08);
  animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.register-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-primary), var(--color-cube-violet), var(--color-cube-accent));
  background-size: 200% 100%;
  animation: border-flow 4s linear infinite;
}

.register-card::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 36%;
  background: repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.045) 0 1px, transparent 1px 16px);
  opacity: 0.08;
  pointer-events: none;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

/* 魔方 Logo */
.register-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.cube-icon {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 0 16px rgba(6, 182, 212, 0.5));
}

.register-title {
  font-size: 28px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.register-btn {
  width: 100%;
  margin-top: 12px;
}

.register-card :deep(.el-form) {
  position: relative;
  z-index: 1;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  color: var(--text-secondary);
}
.login-link a {
  color: var(--color-cube-primary);
  text-decoration: none;
  font-weight: 500;
}
.login-link a:hover {
  color: var(--primary-light);
  text-decoration: underline;
}
</style>
