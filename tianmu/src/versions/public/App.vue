<template>
  <AuroraField />

  <Transition name="login-fade" mode="out-in">
    <section v-if="!isSignedIn" key="login" class="login-screen">
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

        <LiquidGlass as="form" class="login-card" @submit.prevent="handleAuth">
          <span class="login-card__eyebrow">欢迎回来</span>
          <h2>{{ authMode === 'login' ? '登录控制台' : '创建账号' }}</h2>
          <label>
            <span>账号</span>
            <input v-model="authForm.username" autocomplete="username" />
          </label>
          <label>
            <span>密码</span>
            <input v-model="authForm.password" type="password" autocomplete="current-password" />
          </label>
          <button class="primary-button" type="submit" :disabled="authLoading">
            {{ authLoading ? '连接中...' : authMode === 'login' ? '进入概览' : '完成注册' }}
          </button>
          <button class="text-button" type="button" @click="authMode = authMode === 'login' ? 'register' : 'login'">
            {{ authMode === 'login' ? '没有账号？注册' : '已有账号？登录' }}
          </button>
          <p v-if="authMessage">{{ authMessage }}</p>
        </LiquidGlass>
      </div>
    </section>

    <div v-else key="app" class="app-shell" :class="deviceShellClasses">
    <aside class="sidebar">
      <div class="brand">
        <img src="/tmzc-logo.svg" alt="" class="brand__mark" />
        <span>智能魔方</span>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <button
          v-for="item in navItems"
          :key="item.id"
          class="nav-item"
          :class="{ 'nav-item--active': activeView === item.id }"
          @click="activeView = item.id"
        >
          <span class="nav-item__icon" v-html="item.icon"></span>
          <span>{{ item.label }}</span>
        </button>
      </nav>

    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="topbar__date">{{ todayText }}</p>
          <strong>{{ currentViewTitle }}</strong>
        </div>
        <div class="topbar__actions">
          <button class="icon-button" aria-label="刷新" title="刷新数据" @click="refreshAll" v-html="icons.refresh"></button>
          <button class="icon-button" aria-label="通知" v-html="icons.bell"></button>
          <VersionSwitcher variant="dark" />
          <button class="profile-button" @click="signOut">
            <span>J</span>
            <strong>{{ authForm.username || 'User' }}</strong>
          </button>
        </div>
      </header>

      <div v-if="statusMessage || errorMessage" class="app-notice" :class="{ 'app-notice--error': errorMessage }">
        {{ errorMessage || statusMessage }}
      </div>

      <Transition name="view-fade" mode="out-in">
        <section v-if="activeView === 'overview'" key="overview" class="view">
          <BlurReveal>
            <div class="page-heading">
              <h1>智能桌面魔方</h1>
              <p>实时感知房间环境，AI 智能守护舒适每一刻。</p>
            </div>
          </BlurReveal>

          <div class="overview-grid">
            <LiquidGlass class="device-hero" :class="{ 'device-hero--empty': devices.length === 0 }">
              <DotField
                class-name="device-hero__dots"
                :dot-radius="1.4"
                :dot-spacing="15"
                :bulge-strength="54"
                :glow-radius="150"
                :cursor-radius="420"
                :cursor-force="0.1"
                gradient-from="rgba(245, 245, 247, 0.1)"
                gradient-to="rgba(120, 170, 220, 0.05)"
                glow-color="rgba(255, 255, 255, 0.16)"
                bulge-only
              />
              <div class="device-hero__copy">
                <span class="status-dot"></span>
                <strong>{{ activeDevice.name }}</strong>
                <small>{{ activeDevice.subtitle }} · {{ activeDevice.status === 'online' ? '在线' : '离线' }}</small>
              </div>
              <div v-if="devices.length === 0" class="device-hero__empty">
                <strong>还没有绑定设备</strong>
                <span>绑定桌面魔方后，这里会显示实时环境状态。</span>
                <button type="button" @click="activeView = 'devices'">去绑定设备</button>
              </div>
              <div v-else class="device-hero__body">
                <div class="metric-stack">
                  <button v-for="metric in heroMetrics" :key="metric.label" class="metric-row">
                    <span class="metric-row__icon" :class="`metric-row__icon--${metric.tone}`" v-html="metric.icon"></span>
                    <span>
                      <small>{{ metric.label }}</small>
                      <strong>{{ metric.value }}</strong>
                    </span>
                    <i>›</i>
                  </button>
                </div>
                <ProductCube variant="hero" :value="cubeValue" :sensor="activeSensor" :online="isActiveOnline" :focus="focusEnabled" />
              </div>
            </LiquidGlass>

            <LiquidGlass class="control-card">
              <ControlRow
                label="灯光"
                detail="柔和照明，舒适护眼"
                :icon="icons.sun"
                v-model="lightEnabled"
                @update:model-value="(value: boolean) => handleToggleControl('light', value)"
              />
              <div class="brightness">
                <span v-html="icons.sunSmall"></span>
                <input v-model="brightness" type="range" min="0" max="100" @change="handleSliderControl('screen_brightness', brightness)" />
                <span v-html="icons.sun"></span>
              </div>
              <ControlRow
                label="通知提醒"
                detail="重要通知，不错过"
                :icon="icons.bell"
                v-model="notifyEnabled"
                @update:model-value="(value: boolean) => handleToggleControl('wechat_notify', value)"
              />
              <div class="focus-segment">
                <span>专注模式</span>
                <button
                  v-for="mode in focusModes"
                  :key="mode"
                  :class="{ active: focusMode === mode }"
                  @click="setFocusMode(mode)"
                >
                  {{ mode }}
                </button>
              </div>
            </LiquidGlass>
          </div>

          <div class="lower-grid">
            <LiquidGlass class="device-list" hover>
              <div class="section-title">
                <h2>设备</h2>
                <button @click="activeView = 'devices'">查看全部</button>
              </div>
              <DeviceRow
                v-for="device in devices"
                :key="device.id"
                :device="device"
                @click="selectDevice(device.id)"
              />
            </LiquidGlass>

            <LiquidGlass class="insight-panel" hover>
              <div class="section-title">
                <h2>AI 洞察</h2>
                <div class="section-title__actions">
                  <div class="compact-segment" aria-label="AI 分析模式">
                    <button
                      v-for="mode in aiModeOptions"
                      :key="mode.id"
                      :class="{ active: aiMode === mode.id }"
                      :disabled="aiLoading"
                      @click="setAiMode(mode.id)"
                    >
                      {{ mode.label }}
                    </button>
                  </div>
                  <button @click="refreshAiPanel">{{ aiLoading ? '分析中' : '刷新' }}</button>
                  <button @click="activeView = 'insight'">查看全部</button>
                </div>
              </div>
              <div class="insight-grid">
                <article v-for="item in insights" :key="item.title" class="insight-card">
                  <span :class="`insight-card__icon insight-card__icon--${item.tone}`" v-html="toneIcon(item.tone)"></span>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.body }}</p>
                  <small>{{ item.time }}</small>
                </article>
              </div>
            </LiquidGlass>
          </div>
        </section>

        <section v-else-if="activeView === 'control'" key="control" class="view control-view">
          <BlurReveal>
            <div class="page-heading page-heading--compact">
              <h1>控制面板</h1>
              <p>以更安静的方式控制灯光、提醒和专注状态。</p>
            </div>
          </BlurReveal>

          <div class="control-layout">
            <LiquidGlass class="model-stage" tone="blue">
              <ProductCube :value="cubeValue" :sensor="activeSensor" :online="isActiveOnline" :focus="focusEnabled" />
              <div class="model-stage__caption">
                <strong>{{ activeDevice.name }}</strong>
                <span>{{ activeDevice.id }} · {{ activeDevice.subtitle }}</span>
              </div>
            </LiquidGlass>

            <div class="control-stack">
              <LiquidGlass class="settings-panel">
                <ControlRow label="灯光" detail="同步桌面氛围灯" :icon="icons.sun" v-model="lightEnabled" @update:model-value="(value: boolean) => handleToggleControl('light', value)" />
                <label class="slider-block">
                  <span>屏幕亮度</span>
                  <strong>{{ brightness }}%</strong>
                  <input v-model="brightness" type="range" min="0" max="100" @change="handleSliderControl('screen_brightness', brightness)" />
                </label>
                <ControlRow label="微信通知" detail="环境异常时提醒" :icon="icons.bell" v-model="notifyEnabled" @update:model-value="(value: boolean) => handleToggleControl('wechat_notify', value)" />
                <ControlRow label="专注模式" detail="减少干扰，保持工作流" :icon="icons.moon" v-model="focusEnabled" @update:model-value="(value: boolean) => handleToggleControl('focus_mode', value)" />
              </LiquidGlass>

              <LiquidGlass class="mini-report" tone="green">
                <h2>孪生状态</h2>
                <div class="mini-report__grid">
                  <span>温度 <strong>{{ activeDevice.temperature }}℃</strong></span>
                  <span>湿度 <strong>{{ activeDevice.humidity }}%</strong></span>
                  <span>AQI <strong>{{ activeDevice.aqi }}</strong></span>
                </div>
              </LiquidGlass>
            </div>
          </div>
        </section>

        <section v-else-if="activeView === 'devices'" key="devices" class="view">
          <BlurReveal>
            <div class="page-heading page-heading--compact">
              <h1>设备</h1>
              <p>绑定、筛选、解绑和选择每个魔方终端。</p>
            </div>
          </BlurReveal>
          <LiquidGlass class="settings-list">
            <div class="device-toolbar">
              <input v-model="deviceSearch" placeholder="搜索设备名称或 ID" />
              <select v-model="deviceStatusFilter">
                <option value="all">全部状态</option>
                <option value="online">在线</option>
                <option value="offline">离线</option>
              </select>
            </div>
            <div v-for="device in filteredDevices" :key="device.id" class="device-admin-row">
              <DeviceRow :device="device" size="large" @click="selectDevice(device.id)" />
              <button @click="refreshDeviceData(device.id)">刷新</button>
              <button @click="unbindSelectedDevice(device.id)">解绑</button>
            </div>
            <form class="bind-form" @submit.prevent="bindNewDevice">
              <input v-model="bindForm.deviceId" placeholder="设备 ID" />
              <input v-model="bindForm.deviceName" placeholder="设备名称" />
              <button class="add-row" type="submit">添加设备 <span>+</span></button>
            </form>
          </LiquidGlass>
        </section>

        <section v-else-if="activeView === 'insight'" key="insight" class="view">
          <BlurReveal>
            <div class="page-heading page-heading--compact">
              <h1>AI 洞察</h1>
              <p>把环境数据整理成评分、风险、建议和本周周报。</p>
            </div>
          </BlurReveal>
          <div class="insight-page">
            <LiquidGlass class="score-card" tone="green">
              <span>今日舒适度</span>
              <strong>{{ environmentScore }}</strong>
              <p>{{ scoreSummary }}</p>
              <div class="score-card__actions">
                <div class="compact-segment" aria-label="AI 分析模式">
                  <button
                    v-for="mode in aiModeOptions"
                    :key="mode.id"
                    :class="{ active: aiMode === mode.id }"
                    :disabled="aiLoading"
                    @click="aiMode = mode.id"
                  >
                    {{ mode.label }}
                  </button>
                </div>
                <button class="text-button" :disabled="aiLoading" @click="refreshAiPanel">
                  {{ aiLoading ? '分析中...' : aiMode === 'llm' ? '开始 LLM 分析' : '刷新规则分析' }}
                </button>
              </div>
            </LiquidGlass>
            <LiquidGlass class="chart-card">
              <div class="section-title">
                <h2>本周环境</h2>
                <small>{{ weeklySource }}</small>
              </div>
              <div class="weekly-report" aria-label="本周环境周报">
                <article
                  v-for="day in weeklyCards"
                  :key="day.key"
                  class="weekly-report__day-card"
                  :class="`weekly-report__day-card--${day.tone}`"
                >
                  <div class="weekly-report__day">
                    <strong>{{ day.label }}</strong>
                    <span>{{ day.status }}</span>
                  </div>
                  <div class="weekly-report__metrics">
                    <div class="weekly-report__metric weekly-report__metric--temp">
                      <b>温度</b>
                      <div><i :style="{ width: day.temperatureWidth }"></i></div>
                      <em>{{ day.temperatureText }}</em>
                    </div>
                    <div class="weekly-report__metric weekly-report__metric--humidity">
                      <b>湿度</b>
                      <div><i :style="{ width: day.humidityWidth }"></i></div>
                      <em>{{ day.humidityText }}</em>
                    </div>
                    <div class="weekly-report__metric weekly-report__metric--aqi">
                      <b>AQI</b>
                      <div><i :style="{ width: day.aqiWidth }"></i></div>
                      <em>{{ day.aqiText }}</em>
                    </div>
                  </div>
                </article>
              </div>
              <p class="weekly-summary">{{ weeklySummary || weeklySummaryFallback }}</p>
            </LiquidGlass>
            <LiquidGlass class="insight-list">
              <article v-for="item in insights" :key="item.title">
                <span :class="`insight-card__icon insight-card__icon--${item.tone}`" v-html="toneIcon(item.tone)"></span>
                <div>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.body }}</p>
                </div>
                <small>{{ item.time }}</small>
              </article>
            </LiquidGlass>
          </div>
        </section>

        <section v-else-if="activeView === 'logs'" key="logs" class="view">
          <BlurReveal>
            <div class="page-heading page-heading--compact">
              <h1>日志</h1>
              <p>查看最近的控制指令和后端操作记录。</p>
            </div>
          </BlurReveal>
          <LiquidGlass class="settings-list">
            <div v-if="operationLogs.length === 0" class="empty-state">暂无操作记录</div>
            <article v-for="log in operationLogs" :key="log.id" class="log-row">
              <span>{{ formatDate(log.created_at) }}</span>
              <strong>{{ log.action }}</strong>
              <small>{{ log.device_id || activeDevice.id }}</small>
              <p>{{ formatLogDetail(log.detail) }}</p>
            </article>
          </LiquidGlass>
        </section>

        <section v-else key="settings" class="view">
          <BlurReveal>
            <div class="page-heading page-heading--compact">
              <h1>设置</h1>
              <p>切换不同人群的前端版本，当前页面为大众版。</p>
            </div>
          </BlurReveal>
          <LiquidGlass class="mode-panel">
            <article
              v-for="mode in appModes"
              :key="mode.id"
              class="mode-card"
              :class="{ 'mode-card--active': mode.id === 'public', 'mode-card--disabled': mode.disabled }"
            >
              <div>
                <span>{{ mode.badge }}</span>
                <h2>{{ mode.title }}</h2>
                <p>{{ mode.description }}</p>
              </div>
              <button :disabled="mode.disabled || mode.id === 'public'" @click="openMode(mode.id)">
                {{ mode.id === 'public' ? '当前版本' : mode.disabled ? '开发中' : '进入' }}
              </button>
            </article>
          </LiquidGlass>
        </section>
      </Transition>
    </main>
    </div>
  </Transition>

</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import '@/versions/public/styles/base.css'
import { api, clearToken, getToken, setToken, type AiSuggestion, type DeviceInfo, type OperationLog, type SensorData } from '@/versions/public/api/client'
import BlurReveal from '@/versions/public/components/BlurReveal.vue'
import ControlRow from '@/versions/public/components/ControlRow.vue'
import DeviceRow from '@/versions/public/components/DeviceRow.vue'
import LiquidGlass from '@/versions/public/components/LiquidGlass.vue'
import ProductCube from '@/versions/public/components/ProductCube.vue'
import VersionSwitcher from '@/components/VersionSwitcher.vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { BEIJING_TIME_ZONE } from '@/utils/format'
import type { Device as DeviceView, Insight } from '@/versions/public/data/mockData'

const AuroraField = defineAsyncComponent(() => import('@/versions/public/components/AuroraField.vue'))
const DotField = defineAsyncComponent(() => import('@/versions/public/components/DotField.vue'))
const SideRays = defineAsyncComponent(() => import('@/versions/public/components/SideRays.vue'))

const icons = {
  home: '<svg viewBox="0 0 24 24"><path d="M4 11.2 12 4l8 7.2V20a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-8.8Z"/></svg>',
  cube: '<svg viewBox="0 0 24 24"><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Zm0 2.4L6.5 8.5 12 11.6l5.5-3.1L12 5.4Zm-6 5.2v4.7l5 2.8v-4.7l-5-2.8Zm7 7.5 5-2.8v-4.7l-5 2.8v4.7Z"/></svg>',
  spark: '<svg viewBox="0 0 24 24"><path d="M12 2.5 14.3 9l6.7 2.1-6.7 2.2L12 20l-2.3-6.7L3 11.1 9.7 9 12 2.5Z"/></svg>',
  chart: '<svg viewBox="0 0 24 24"><path d="M5 19V5h2v14H5Zm6 0V9h2v10h-2Zm6 0v-7h2v7h-2Z"/></svg>',
  bell: '<svg viewBox="0 0 24 24"><path d="M18 16v-5a6 6 0 0 0-12 0v5l-2 2v1h16v-1l-2-2Zm-8 5h4a2 2 0 0 1-4 0Z"/></svg>',
  refresh: '<svg viewBox="0 0 24 24"><path d="M18.6 6.4A8 8 0 1 0 20 12h-2a6 6 0 1 1-1.8-4.3L13 11h8V3l-2.4 3.4Z"/></svg>',
  settings: '<svg viewBox="0 0 24 24"><path d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Zm8 4a7.8 7.8 0 0 0-.1-1l2-1.6-2-3.5-2.4 1a7.4 7.4 0 0 0-1.8-1L15.4 3h-4l-.4 2.7c-.6.2-1.2.6-1.8 1l-2.4-1-2 3.5 2 1.6a7.8 7.8 0 0 0 0 2l-2 1.6 2 3.5 2.4-1c.6.4 1.2.7 1.8 1l.4 2.7h4l.4-2.7c.6-.2 1.2-.6 1.8-1l2.4 1 2-3.5-2-1.6c.1-.3.1-.7.1-1Z"/></svg>',
  sun: '<svg viewBox="0 0 24 24"><path d="M12 6a6 6 0 1 1 0 12 6 6 0 0 1 0-12Zm0-4 1.2 3h-2.4L12 2Zm0 20-1.2-3h2.4L12 22ZM2 12l3-1.2v2.4L2 12Zm20 0-3 1.2v-2.4l3 1.2ZM4.2 4.2l3 1.3-1.7 1.7-1.3-3Zm15.6 15.6-3-1.3 1.7-1.7 1.3 3Zm0-15.6-1.3 3-1.7-1.7 3-1.3ZM4.2 19.8l1.3-3 1.7 1.7-3 1.3Z"/></svg>',
  sunSmall: '<svg viewBox="0 0 24 24"><path d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M20 15.2A8.4 8.4 0 0 1 8.8 4 8.5 8.5 0 1 0 20 15.2Z"/></svg>',
  drop: '<svg viewBox="0 0 24 24"><path d="M12 2s7 7.2 7 13a7 7 0 0 1-14 0C5 9.2 12 2 12 2Z"/></svg>',
  leaf: '<svg viewBox="0 0 24 24"><path d="M20.8 3.2C12.5 3.5 6.7 6.4 5 12.5c-1 3.6.8 6.9.8 6.9s3.3 1.1 6.5-.5c5.8-2.9 7.7-9.3 8.5-15.7ZM7 18c2.5-4 5.7-6.7 10-9"/></svg>',
}

const navItems = [
  { id: 'overview', label: '概览', icon: icons.home },
  { id: 'devices', label: '设备', icon: icons.cube },
  { id: 'control', label: '控制', icon: icons.spark },
  { id: 'insight', label: '洞察', icon: icons.chart },
  { id: 'logs', label: '日志', icon: icons.settings },
] as const

type ViewId = (typeof navItems)[number]['id']
type AppModeId = 'teen' | 'public' | 'senior'
type AiMode = 'rule' | 'llm'
type WeeklyDayReading = {
  date: string
  temperature: number | null
  humidity: number | null
  aqi: number | null
  sample_count?: number
}

const currentMode: AppModeId = 'public'
const activeView = ref<ViewId | 'settings'>('overview')
const brightness = ref(62)
const lightEnabled = ref(true)
const notifyEnabled = ref(true)
const focusEnabled = ref(false)
const focusMode = ref('关闭')
const focusModes = ['关闭', '专注']
const isSignedIn = ref(Boolean(getToken()))
const isMobileViewport = ref(false)
const isTouchDevice = ref(false)

const initialAuthMode = window.location.pathname === '/register' ? 'register' : 'login'
const authMode = ref<'login' | 'register'>(initialAuthMode)
const authLoading = ref(false)
const authMessage = ref('')
const authForm = reactive({
  username: initialAuthMode === 'register' ? '' : localStorage.getItem('username') || 'demo',
  password: initialAuthMode === 'register' ? '' : 'demo123456',
})

const appLoading = ref(false)
const aiLoading = ref(false)
const aiMode = ref<AiMode>('rule')
const statusMessage = ref('')
const errorMessage = ref('')
let noticeTimer: ReturnType<typeof window.setTimeout> | undefined
const ws = useWebSocket('/ws')
const selectedDeviceId = ref(localStorage.getItem('selectedDeviceId') || '')
const rawDevices = ref<DeviceInfo[]>([])
const sensorMap = ref<Record<string, SensorData | null>>({})
const aiSuggestions = ref<AiSuggestion[]>([])
const suggestionSource = ref<'llm' | 'rule' | ''>('')
const environmentScore = ref(0)
const scoreSummary = ref('等待后端环境评分。')
const weeklySummary = ref('')
const weeklySource = ref('规则/LLM')
const weeklyDays = ref<WeeklyDayReading[]>([])
const riskItems = ref<Array<{ field: string; level: 'warning' | 'critical'; title: string; message: string }>>([])
const operationLogs = ref<OperationLog[]>([])
const deviceSearch = ref('')
const deviceStatusFilter = ref<'all' | 'online' | 'offline'>('all')
const bindForm = reactive({ deviceId: '', deviceName: '' })

const aiModeOptions: Array<{ id: AiMode; label: string }> = [
  { id: 'rule', label: '规则' },
  { id: 'llm', label: 'LLM' },
]

const appModes: Array<{
  id: AppModeId
  badge: string
  title: string
  description: string
  disabled?: boolean
}> = [
  {
    id: 'teen',
    badge: 'tianmu',
    title: '青少年版',
    description: '打开原 tianmu 前端，保留更完整的青少年版控制台。',
  },
  {
    id: 'public',
    badge: 'tianmu-liquid',
    title: '大众版',
    description: '当前简约液态玻璃界面，适合日常查看和控制。',
  },
  {
    id: 'senior',
    badge: 'tianmu-senior',
    title: '老年版',
    description: '更大字号、更低信息密度和更清晰操作路径。',
  },
]

const entryPaths: Record<AppModeId, string> = {
  teen: '/teen/dashboard',
  public: '/public',
  senior: '/senior',
}

const currentViewTitle = computed(() => {
  if (activeView.value === 'settings') return '设置'
  return navItems.find((item) => item.id === activeView.value)?.label || '概览'
})
const deviceShellClasses = computed(() => ({
  'app-shell--mobile': isMobileViewport.value,
  'app-shell--desktop': !isMobileViewport.value,
  'app-shell--touch': isTouchDevice.value,
}))
const todayText = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
  timeZone: BEIJING_TIME_ZONE,
}).format(new Date())

const emptyDevice: DeviceView = {
  id: '未选择设备',
  name: '等待设备',
  subtitle: '未绑定',
  status: 'offline',
  temperature: null,
  humidity: null,
  aqi: null,
}

const devices = computed<DeviceView[]>(() =>
  rawDevices.value.map((device) => {
    const sensor = sensorMap.value[device.device_id]
    return {
      id: device.device_id,
      name: normalizeDeviceName(device),
      subtitle: normalizeDeviceSubtitle(device),
      status: device.status,
      temperature: sensor?.temperature ?? null,
      humidity: sensor?.humidity ?? null,
      aqi: sensor?.aqi ?? null,
    }
  }),
)

const activeDevice = computed(() => devices.value.find((device) => device.id === selectedDeviceId.value) || devices.value[0] || emptyDevice)
const activeSensor = computed(() => sensorMap.value[activeDevice.value.id] || null)
const isActiveOnline = computed(() => activeDevice.value.status === 'online')
const cubeValue = computed(() => (typeof activeDevice.value.temperature === 'number' ? String(Math.round(activeDevice.value.temperature)) : '--'))

const filteredDevices = computed(() => {
  const q = deviceSearch.value.trim().toLowerCase()
  return devices.value.filter((device) => {
    const matchesText = !q || device.name.toLowerCase().includes(q) || device.id.toLowerCase().includes(q)
    const matchesStatus = deviceStatusFilter.value === 'all' || device.status === deviceStatusFilter.value
    return matchesText && matchesStatus
  })
})

const heroMetrics = computed(() => [
  { label: '温度', value: `${formatMetric(activeDevice.value.temperature)} °C`, icon: icons.drop, tone: 'blue' },
  { label: '湿度', value: `${formatMetric(activeDevice.value.humidity)} %`, icon: icons.drop, tone: 'blue' },
  { label: '空气质量', value: `${formatMetric(activeDevice.value.aqi)} AQI`, icon: icons.leaf, tone: 'green' },
])

const insights = computed<Insight[]>(() => {
  const mapped: Insight[] = aiSuggestions.value.map((item) => ({
    title: item.title,
    body: item.desc,
    tone: mapSuggestionTone(item.icon),
    time: suggestionSource.value === 'llm' ? 'LLM 生成' : '规则引擎',
  }))

  if (riskItems.value.length) {
    const riskInsights: Insight[] = riskItems.value.slice(0, 2).map((risk) => ({
        title: risk.title,
        body: risk.message,
        tone: risk.level === 'critical' ? 'amber' : 'blue',
        time: '风险预警',
      }))
    mapped.unshift(...riskInsights)
  }

  return mapped.length
    ? mapped
    : [
        {
          title: '等待 AI 分析',
          body: '选择设备并点击开始 AI 分析后，将展示后端返回的建议。',
          tone: 'blue',
          time: '未开始',
        },
      ]
})

const weeklyCards = computed(() => {
  const readings = weeklyDays.value.length ? weeklyDays.value : buildFallbackWeeklyDays()

  return readings.slice(-7).map((day, index) => {
    const status = getWeeklyDayStatus(day)
    return {
      key: `${day.date || 'day'}-${index}`,
      label: formatWeekdayLabel(day.date, index),
      status: status.label,
      tone: status.tone,
      temperatureText: formatWeeklyMetric(day.temperature, '°C'),
      humidityText: formatWeeklyMetric(day.humidity, '%'),
      aqiText: formatWeeklyMetric(day.aqi, ''),
      temperatureWidth: metricWidth(day.temperature, 16, 34),
      humidityWidth: metricWidth(day.humidity, 30, 85),
      aqiWidth: metricWidth(day.aqi, 0, 180),
    }
  })
})

const weeklySummaryFallback = computed(() => {
  const latest = weeklyCards.value.at(-1)
  return latest ? `最近环境状态为「${latest.status}」，可重点关注温度、湿度和空气质量三项变化。` : '暂无本周环境数据。'
})

function toneIcon(tone: 'green' | 'blue' | 'amber') {
  if (tone === 'green') return icons.leaf
  if (tone === 'blue') return icons.drop
  return icons.sun
}

function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatWeeklyMetric(value: number | null | undefined, unit: string) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  const text = Number.isInteger(value) ? String(value) : value.toFixed(1)
  return unit ? `${text}${unit}` : text
}

function metricWidth(value: number | null | undefined, min: number, max: number) {
  if (value === null || value === undefined || Number.isNaN(value)) return '8%'
  const normalized = Math.max(0, Math.min(1, (value - min) / (max - min)))
  return `${Math.round(18 + normalized * 82)}%`
}

function formatWeekdayLabel(date: string, index: number) {
  const parsed = new Date(date)
  if (!Number.isNaN(parsed.getTime())) {
    return new Intl.DateTimeFormat('zh-CN', { weekday: 'short' }).format(parsed)
  }

  const fallback = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return fallback[index % fallback.length]
}

function getWeeklyDayStatus(day: WeeklyDayReading): { label: string; tone: 'good' | 'watch' | 'alert' } {
  if ((day.aqi ?? 0) >= 150) return { label: '空气较差', tone: 'alert' }
  if ((day.aqi ?? 0) >= 100) return { label: '空气关注', tone: 'watch' }
  if ((day.humidity ?? 0) >= 75) return { label: '偏湿', tone: 'watch' }
  if ((day.humidity ?? 100) <= 35) return { label: '偏干', tone: 'watch' }
  if ((day.temperature ?? 22) >= 30) return { label: '偏热', tone: 'watch' }
  if ((day.temperature ?? 22) <= 18) return { label: '偏冷', tone: 'watch' }
  return { label: '舒适', tone: 'good' }
}

function buildFallbackWeeklyDays(): WeeklyDayReading[] {
  const today = new Date()
  const tempBase = activeDevice.value.temperature
  const humidityBase = activeDevice.value.humidity
  const aqiBase = activeDevice.value.aqi

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (6 - index))
    const drift = index - 3
    return {
      date: date.toISOString(),
      temperature: typeof tempBase === 'number' ? Math.max(0, tempBase + drift * 0.3) : null,
      humidity: typeof humidityBase === 'number' ? Math.max(0, humidityBase + drift * 1.1) : null,
      aqi: typeof aqiBase === 'number' ? Math.max(0, aqiBase + drift * 2) : null,
    }
  })
}

function normalizeDeviceName(device: DeviceInfo) {
  const name = device.device_name?.trim()
  return name || device.device_id || '未命名设备'
}

function normalizeDeviceSubtitle(device: DeviceInfo) {
  const parts = [device.device_id, device.chip_model].filter((part): part is string => Boolean(part?.trim()))
  return parts.length ? parts.join(' · ') : '无设备信息'
}

function openMode(mode: AppModeId) {
  if (mode === currentMode) return
  window.location.href = getModeHref(mode)
}

function getModeHref(mode: AppModeId) {
  return entryPaths[mode]
}

function updateDeviceKind() {
  if (typeof window === 'undefined') return
  isMobileViewport.value = window.matchMedia('(max-width: 760px)').matches
  isTouchDevice.value = window.matchMedia('(pointer: coarse)').matches
}

function showStatus(message: string, isError = false) {
  clearNoticeTimer()

  if (isError) {
    errorMessage.value = message
    statusMessage.value = ''
  } else {
    statusMessage.value = message
    errorMessage.value = ''
  }

  noticeTimer = window.setTimeout(dismissNotice, 5000)
}

function dismissNotice() {
  clearNoticeTimer()
  statusMessage.value = ''
  errorMessage.value = ''
}

function clearNoticeTimer() {
  if (!noticeTimer) return
  window.clearTimeout(noticeTimer)
  noticeTimer = undefined
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

function selectDevice(deviceId: string) {
  selectedDeviceId.value = deviceId
  localStorage.setItem('selectedDeviceId', deviceId)
  refreshDeviceData(deviceId)
  loadAiData(false)
  loadOperationLogs()
}

async function handleAuth() {
  if (!authForm.username || !authForm.password) {
    authMessage.value = '请输入账号和密码'
    return
  }
  if (authMode.value === 'register' && authForm.username.trim().length < 2) {
    authMessage.value = '用户名至少 2 个字符'
    return
  }
  if (authMode.value === 'register' && authForm.password.length < 6) {
    authMessage.value = '密码至少 6 个字符'
    return
  }

  authLoading.value = true
  authMessage.value = ''

  try {
    if (authMode.value === 'register') {
      await api.register(authForm.username, authForm.password)
      authMode.value = 'login'
      authMessage.value = '注册成功，请登录'
      return
    }

    const result = await api.login(authForm.username, authForm.password)
    setToken(result.access_token)
    localStorage.setItem('username', authForm.username)
    isSignedIn.value = true
    ws.connect()
    await refreshAll()
  } catch (error) {
    authMessage.value = getErrorMessage(error, '登录失败，请检查后端服务')
  } finally {
    authLoading.value = false
  }
}

function signOut() {
  ws.disconnect()
  clearToken()
  isSignedIn.value = false
  rawDevices.value = []
  sensorMap.value = {}
  selectedDeviceId.value = ''
}

async function refreshAll() {
  if (!getToken()) return

  appLoading.value = true
  showStatus('正在同步后端数据...')

  try {
    await loadDevices()
    await Promise.all([loadAiData(false), loadOperationLogs()])
    showStatus('数据已同步')
  } catch (error) {
    showStatus(getErrorMessage(error, '同步失败，请检查后端接口'), true)
  } finally {
    appLoading.value = false
  }
}

async function loadDevices() {
  const list = await api.getDevices()
  rawDevices.value = list
  subscribeDevices(list)

  if (!selectedDeviceId.value || !list.some((device) => device.device_id === selectedDeviceId.value)) {
    selectedDeviceId.value = list[0]?.device_id || ''
  }

  await Promise.all(list.map((device) => refreshDeviceData(device.device_id, false)))

  const selectedHasData = selectedDeviceId.value && sensorMap.value[selectedDeviceId.value]
  const firstDeviceWithData = list.find((device) => sensorMap.value[device.device_id])

  if (!selectedHasData && firstDeviceWithData) {
    selectedDeviceId.value = firstDeviceWithData.device_id
  }

  if (selectedDeviceId.value) {
    localStorage.setItem('selectedDeviceId', selectedDeviceId.value)
  }
}

function subscribeDevices(devices = rawDevices.value) {
  devices.forEach((device) => {
    if (device.device_id) {
      ws.send('subscribe', { device_id: device.device_id })
    }
  })
}

function applyHardwareControlState(deviceId: string, data: Partial<SensorData> | null | undefined) {
  if (!data || deviceId !== selectedDeviceId.value) return
  if (typeof data.light === 'boolean') lightEnabled.value = data.light
  if (typeof data.wechat_notify === 'boolean') notifyEnabled.value = data.wechat_notify
  if (typeof data.focus_mode === 'boolean') {
    focusEnabled.value = data.focus_mode
    focusMode.value = data.focus_mode ? '专注' : '关闭'
  }
}

function applyRealtimeSensorData(data: Record<string, unknown>) {
  const deviceId = data.device_id as string
  if (!deviceId) return
  sensorMap.value = {
    ...sensorMap.value,
    [deviceId]: data as unknown as SensorData,
  }
  applyHardwareControlState(deviceId, data as unknown as SensorData)
}

function applyRealtimeHardwareState(data: Record<string, unknown>) {
  const deviceId = data.device_id as string
  if (!deviceId) return

  const current = sensorMap.value[deviceId]
  if (current) {
    sensorMap.value = {
      ...sensorMap.value,
      [deviceId]: { ...current, ...data } as SensorData,
    }
  }
  applyHardwareControlState(deviceId, data as unknown as SensorData)
}

async function refreshDeviceData(deviceId = activeDevice.value.id, notify = true) {
  if (!deviceId || deviceId === emptyDevice.id) return

  try {
    const data = await api.getLatestData(deviceId)
    sensorMap.value = {
      ...sensorMap.value,
      [deviceId]: data,
    }
    applyHardwareControlState(deviceId, data)

    if (notify) showStatus('设备数据已刷新')
  } catch (error) {
    if (notify) showStatus(getErrorMessage(error, '设备数据刷新失败'), true)
  }
}

async function handleToggleControl(command: string, value: boolean) {
  await sendControl(command, value ? 'on' : 'off')
}

async function handleSliderControl(command: string, value: number) {
  await sendControl(command, String(value))
}

async function setFocusMode(mode: string) {
  focusMode.value = mode
  focusEnabled.value = mode !== '关闭'
  await sendControl('focus_mode', mode === '关闭' ? 'off' : 'on', { mode })
}

async function sendControl(command: string, value: string, params: Record<string, unknown> = {}) {
  if (!selectedDeviceId.value || !isActiveOnline.value) {
    showStatus('设备离线或未选择，无法下发控制', true)
    return
  }

  try {
    await api.sendControl(selectedDeviceId.value, command, value, params)
    showStatus('控制指令已下发')
    await loadOperationLogs()
  } catch (error) {
    showStatus(getErrorMessage(error, '控制指令下发失败'), true)
  }
}

async function bindNewDevice() {
  if (!bindForm.deviceId || !bindForm.deviceName) {
    showStatus('请填写设备 ID 和设备名称', true)
    return
  }

  try {
    await api.bindDevice(bindForm.deviceId.trim(), bindForm.deviceName.trim())
    bindForm.deviceId = ''
    bindForm.deviceName = ''
    await loadDevices()
    showStatus('设备已绑定')
  } catch (error) {
    showStatus(getErrorMessage(error, '绑定失败'), true)
  }
}

async function unbindSelectedDevice(deviceId: string) {
  try {
    await api.unbindDevice(deviceId)
    await loadDevices()
    showStatus('设备已解绑')
  } catch (error) {
    showStatus(getErrorMessage(error, '解绑失败'), true)
  }
}

async function loadAiData(forceLlm = false) {
  if (!selectedDeviceId.value) return

  try {
    const [score, suggestions, risks, weekly] = await Promise.all([
      api.getScore(selectedDeviceId.value),
      api.getSuggestions(selectedDeviceId.value, forceLlm),
      api.getRisks(selectedDeviceId.value),
      api.getWeeklyReport(selectedDeviceId.value, forceLlm),
    ])

    environmentScore.value = score.score ?? 0
    scoreSummary.value = score.summary || getScoreSummary(score.score)
    aiSuggestions.value = suggestions.suggestions || []
    suggestionSource.value = suggestions.source || 'rule'
    riskItems.value = risks.risks || []
    weeklySummary.value = weekly.summary || ''
    weeklySource.value = weekly.source === 'llm' ? 'LLM 周报' : '规则周报'
    weeklyDays.value = weekly.days || []
  } catch (error) {
    if (forceLlm) throw error
    showStatus(getErrorMessage(error, 'AI 数据加载失败'), true)
  }
}

async function runAiAnalysis(forceLlm: boolean) {
  if (!selectedDeviceId.value) {
    showStatus('请先绑定或选择设备', true)
    return
  }

  aiLoading.value = true

  try {
    await loadAiData(forceLlm)
    showStatus(forceLlm ? 'LLM 分析完成' : 'AI 数据已更新')
  } catch (error) {
    showStatus(getErrorMessage(error, 'LLM 未返回结果，请检查 Ollama 或后端配置'), true)
  } finally {
    aiLoading.value = false
  }
}

async function setAiMode(mode: AiMode) {
  aiMode.value = mode
  await refreshAiPanel()
}

async function refreshAiPanel() {
  await runAiAnalysis(aiMode.value === 'llm')
}

async function loadOperationLogs() {
  try {
    const result = await api.getOperationLogs(selectedDeviceId.value || undefined)
    operationLogs.value = result.items || []
  } catch {
    operationLogs.value = []
  }
}

function getScoreSummary(score: number) {
  if (score >= 90) return '当前环境非常舒适，各项指标表现优秀。'
  if (score >= 70) return '当前环境整体良好，建议继续保持。'
  if (score >= 40) return '当前环境一般，部分指标需要关注。'
  return '当前环境较差，建议尽快通风并检查设备状态。'
}

function mapSuggestionTone(icon: string): 'green' | 'blue' | 'amber' {
  if (['wind', 'air', 'aqi', 'leaf', 'ok'].includes(icon)) return 'green'
  if (['humidity', 'water', 'temp', 'temperature'].includes(icon)) return 'blue'
  return 'amber'
}

function formatDate(value?: string) {
  if (!value) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  }).format(new Date(value))
}

function formatLogDetail(detail?: string) {
  if (!detail) return '无详情'
  try {
    const parsed = JSON.parse(detail)
    return Object.entries(parsed).map(([key, value]) => `${key}: ${formatLogValue(value)}`).join(' · ')
  } catch {
    return detail
  }
}

function formatLogValue(value: unknown): string {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (!entries.length) return '{}'
    return entries.map(([key, item]) => `${key}=${formatLogValue(item)}`).join(', ')
  }

  return String(value)
}

watch(activeView, (view) => {
  if (view === 'insight') loadAiData(false)
  if (view === 'logs') loadOperationLogs()
})

onMounted(() => {
  updateDeviceKind()
  window.addEventListener('resize', updateDeviceKind, { passive: true })

  ws.on('auth_result', () => {
    subscribeDevices()
  })
  ws.on('sensor_data', applyRealtimeSensorData)
  ws.on('device_heartbeat', applyRealtimeHardwareState)
  ws.on('device_status', () => {
    if (isSignedIn.value) refreshAll()
  })
  if (isSignedIn.value) {
    ws.connect()
    refreshAll()
  }
})

onBeforeUnmount(() => {
  clearNoticeTimer()
  window.removeEventListener('resize', updateDeviceKind)
})

</script>
