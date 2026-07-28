<template>
  <section class="login-screen">
    <SideRays
      class-name="login-screen__rays"
      :speed="2.5"
      ray-color1="#EAB308"
      ray-color2="#96c8ff"
      :intensity="2"
      :spread="2"
      origin="top-right"
      :tilt="0"
      :saturation="1.5"
      :blend="0.75"
      :falloff="1.6"
      :opacity="1"
    />
    <DotField
      class-name="login-screen__dots"
      :dot-radius="1.5"
      :dot-spacing="14"
      :bulge-strength="67"
      :glow-radius="160"
      :sparkle="false"
      :wave-amplitude="0"
      :cursor-radius="500"
      :cursor-force="0.1"
      gradient-from="rgba(124, 255, 103, 0.32)"
      gradient-to="rgba(160, 255, 188, 0.18)"
      glow-color="rgba(18, 15, 23, 0.86)"
      bulge-only
    />

    <div class="login-shell">
      <div class="login-copy">
        <div class="brand brand--login">
          <img src="/tmzc-logo.svg" alt="" class="brand__mark" />
          <span>智能魔方</span>
        </div>
        <BlurReveal>
          <h1>智能桌面魔方</h1>
          <p>以更轻、更安静的界面查看环境状态，并控制你的桌面魔方。</p>
        </BlurReveal>
      </div>

      <LiquidGlass as="form" class="login-card" @submit.prevent="$emit('submit')">
        <span class="login-card__eyebrow">欢迎回来</span>
        <h2>{{ mode === 'login' ? '登录控制台' : '创建账号' }}</h2>
        <label>
          <span>账号</span>
          <input v-model="username" autocomplete="username" />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          />
        </label>
        <button class="primary-button" type="submit" :disabled="loading">
          {{ loading ? '连接中...' : mode === 'login' ? '进入概览' : '完成注册' }}
        </button>
        <button class="text-button" type="button" @click="$emit('toggle-mode')">
          {{ mode === 'login' ? '没有账号？注册' : '已有账号？登录' }}
        </button>
        <p v-if="message">{{ message }}</p>
      </LiquidGlass>
    </div>
  </section>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

import BlurReveal from './BlurReveal.vue'
import LiquidGlass from './LiquidGlass.vue'

defineProps<{
  mode: 'login' | 'register'
  loading: boolean
  message: string
}>()

defineEmits<{
  submit: []
  'toggle-mode': []
}>()

const username = defineModel<string>('username', { required: true })
const password = defineModel<string>('password', { required: true })
const DotField = defineAsyncComponent(() => import('./DotField.vue'))
const SideRays = defineAsyncComponent(() => import('./SideRays.vue'))
</script>

<style scoped>
.login-screen {
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  overflow: hidden;
}

.login-screen__dots {
  z-index: 2;
  opacity: 0.62;
  mask-image:
    radial-gradient(circle at 86% 8%, transparent 0%, transparent 20%, #000 48%),
    linear-gradient(90deg, #000 0%, #000 62%, transparent 96%);
}

.login-screen__rays {
  z-index: 1;
  opacity: 0.9;
  mask-image:
    radial-gradient(ellipse at 92% 0%, #000 0%, #000 46%, transparent 82%),
    linear-gradient(225deg, #000 0%, #000 56%, transparent 100%);
}

.login-screen::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 90% 0%, rgba(255, 247, 224, 0.12), transparent 26%),
    linear-gradient(
      225deg,
      rgba(255, 244, 214, 0.08),
      rgba(217, 236, 255, 0.035) 38%,
      transparent 72%
    ),
    linear-gradient(90deg, rgba(5, 5, 6, 0.12), rgba(5, 5, 6, 0.84) 74%);
}

.login-shell {
  position: relative;
  z-index: 3;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 440px);
  align-items: center;
  gap: 48px;
  padding: 48px clamp(24px, 7vw, 108px);
}

.brand--login {
  padding: 0;
  margin-bottom: 34px;
}

.login-copy {
  max-width: 760px;
}

.login-copy h1 {
  max-width: 760px;
  margin: 0;
  font-size: clamp(52px, 8vw, 112px);
  line-height: 0.96;
  letter-spacing: -0.055em;
}

.login-copy p {
  max-width: 520px;
  margin: 22px 0 0;
  color: var(--text-secondary);
  font-size: 21px;
  line-height: 1.55;
}

.login-card {
  padding: 28px;
  display: grid;
  gap: 18px;
}

.login-card__eyebrow {
  color: var(--accent-blue);
  font-size: 13px;
  font-weight: 800;
}

.login-card h2 {
  margin: -6px 0 6px;
  font-size: 31px;
  letter-spacing: -0.02em;
}

.login-card label {
  display: grid;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 800;
}

.login-card input {
  width: 100%;
  height: 52px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 17px;
  padding: 0 16px;
  outline: none;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    background 180ms ease;
}

.login-card input:focus {
  border-color: rgba(10, 132, 255, 0.42);
  background: rgba(255, 255, 255, 0.09);
  box-shadow: 0 0 0 5px rgba(10, 132, 255, 0.13);
}

.primary-button {
  min-height: 54px;
  border: 0;
  border-radius: 999px;
  color: #050506;
  background: #f5f5f7;
  box-shadow: 0 18px 46px rgba(255, 255, 255, 0.12);
  font-weight: 800;
}

.primary-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.login-card p {
  margin: 0;
  color: var(--text-tertiary);
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .login-shell {
    grid-template-columns: 1fr;
    align-content: center;
    gap: 30px;
    padding: 34px 18px;
  }

  .login-screen__dots {
    mask-image: linear-gradient(180deg, #000 0%, #000 72%, transparent 100%);
  }

  .login-copy h1 {
    font-size: 52px;
  }

  .login-copy p {
    font-size: 17px;
  }

  .login-card {
    padding: 22px;
  }
}
</style>
