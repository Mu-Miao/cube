<!-- Login.vue -->
<!-- 用户登录页面 -->
<!-- 提供用户名/密码表单，调用后端登录接口获取 JWT Token -->
<!-- 支持一键演示模式（快捷进入管理员演示状态） -->
<template>
  <div class="login-page">
    <MineradioParticleStage
      class="login-particle-stage"
      variant="login"
      :density="0.78"
      :intensity="0.72"
    />
    <div class="login-showcase">
      <MascotCompanion
        state="boot"
        title="小眠"
        message="正在等待你的桌面魔方上线。"
      />
    </div>
    <div class="login-card">
      <!-- Logo + 页面标题 -->
      <div class="login-header">
        <div class="login-logo">
          <img :src="cubeLogoImg" alt="天幕智创 TMZC Logo" class="cube-icon" />
        </div>
        <h1 class="login-title">智能桌面魔方</h1>
        <p class="login-subtitle">天幕智创 · 智能魔方系统</p>
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
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import type { FormInstance, FormRules } from 'element-plus/es/components/form/index.mjs'
import { formatApiError } from '@/api/errors'
import { useAuthStore } from '@/store/auth'
import { login } from '@/api/auth'
import { disableDemoMode, enableDemoMode } from '@/utils/demo'
import MascotCompanion from '@/components/brand/MascotCompanion.vue'
import MineradioParticleStage from '@/components/brand/MineradioParticleStage.vue'
import cubeLogoImg from '@/assets/brand/tmzc-logo.svg'

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
    disableDemoMode()
    const res = await login({ username: form.username, password: form.password })
    authStore.setAuth({
      token: res.access_token,
      username: form.username,
      role: 'user',
    })
    ElMessage.success('登录成功')
    await router.push('/teen/dashboard')
  } catch (err: unknown) {
    ElMessage.error(formatApiError(err, '登录失败，请检查用户名和密码'))
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
    router.push('/teen/dashboard?demo=true')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* =============================================
   Login — Liquid Glass Design
   ============================================= */

/* Page: transparent over ambient body gradient, no grid */
.login-page {
  --glass-bg: linear-gradient(145deg, rgba(102, 198, 255, 0.09), rgba(5, 22, 49, 0.34));
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  --glass-inner-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.12);
  --glass-radius: 28px;
  --glass-blur-heavy: 40px;
  --glass-saturation: 1.6;

  position: relative;
  overflow: hidden;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(340px, 520px) 420px;
  gap: 42px;
  align-items: center;
  justify-content: center;
  background: transparent;
  padding: 24px;
}

.login-particle-stage {
  z-index: 0;
}

.login-showcase,
.login-card {
  position: relative;
  z-index: 1;
}

.login-showcase {
  width: min(520px, 100%);
}

/* ---- Login card: liquid glass ---- */
.login-card {
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
    0 0 80px rgba(6, 182, 212, 0.06);
  animation: slide-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Top-edge highlight arc — simulates light reflecting off curved glass */
.login-card::before {
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
.login-card::after {
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

.login-header {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

/* Logo */
.login-logo {
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

/* Demo section */
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
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.18), transparent);
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
  color: var(--color-cube-accent);
  text-decoration: underline;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: minmax(0, 420px);
  }

  .login-showcase {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-card {
    width: 100%;
    padding: 32px 22px 28px;
  }
}
</style>
