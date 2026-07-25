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
          <img :src="cubeLogoImg" alt="天幕智创 TMZC Logo" class="cube-icon" />
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
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import type { FormInstance, FormRules } from 'element-plus/es/components/form/index.mjs'
import { register } from '@/api/auth'
import { formatApiError } from '@/api/errors'
import cubeLogoImg from '@/assets/brand/tmzc-logo.svg'

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
    ElMessage.error(formatApiError(err, '注册失败，请检查用户名和密码格式'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* =============================================
   Register — Liquid Glass Design
   ============================================= */

/* Page: transparent over ambient body gradient, no grid */
.register-page {
  --glass-bg: linear-gradient(145deg, rgba(102, 198, 255, 0.08), rgba(5, 22, 49, 0.32));
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  --glass-inner-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.12);
  --glass-radius: 28px;
  --glass-blur-heavy: 40px;
  --glass-saturation: 1.6;

  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  padding: 24px;
}

/* ---- Register card: liquid glass ---- */
.register-card {
  position: relative;
  overflow: hidden;
  width: 420px;
  padding: 44px 40px 40px;
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  -webkit-backdrop-filter: blur(var(--glass-blur-heavy)) saturate(var(--glass-saturation));
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  box-shadow:
    var(--glass-shadow),
    var(--glass-inner-shadow),
    0 0 80px rgba(139, 92, 246, 0.06);
  animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Top-edge highlight arc — simulates light reflecting off curved glass */
.register-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 8%;
  right: 8%;
  height: 140px;
  background: radial-gradient(
    ellipse 70% 100% at 50% 0%,
    rgba(255, 255, 255, 0.18) 0%,
    rgba(255, 255, 255, 0.06) 40%,
    transparent 72%
  );
  border-radius: 0 0 50% 50%;
  pointer-events: none;
  z-index: 0;
}

/* Subtle inner glass reflection sheen */
.register-card::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: calc(var(--glass-radius) - 1px);
  background: linear-gradient(
    165deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.02) 22%,
    transparent 50%,
    rgba(0, 0, 0, 0.03) 85%
  );
  pointer-events: none;
  z-index: 0;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

/* Logo */
.register-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.cube-icon {
  width: 72px;
  height: 72px;
  object-fit: contain;
  filter:
    drop-shadow(0 12px 16px rgba(0, 0, 0, 0.28))
    drop-shadow(0 0 22px rgba(6, 182, 212, 0.5));
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
  color: var(--color-cube-accent);
  text-decoration: underline;
}
</style>
