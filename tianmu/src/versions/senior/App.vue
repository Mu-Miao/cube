<template>
  <main class="senior-app">
    <section v-if="!isSignedIn" class="login-page">
      <div class="login-copy">
        <img src="/tmzc-logo.svg" alt="" class="brand-logo" decoding="async" />
        <p class="eyebrow">天幕智护版</p>
        <h1>看得清，点得准，家里环境一眼明白。</h1>
        <p>
          老年人专用界面保留设备监测、灯光控制、提醒、AI 建议和操作记录，
          去掉复杂的数字孪生展示。
        </p>
      </div>

      <form class="login-card" @submit.prevent="handleAuth">
        <h2>{{ authMode === 'login' ? '登录账号' : '创建账号' }}</h2>
        <label>
          <span>账号</span>
          <input v-model.trim="authForm.username" autocomplete="username" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="authForm.password" type="password" autocomplete="current-password" />
        </label>
        <button class="primary-action" type="submit" :disabled="authLoading">
          {{ authLoading ? '正在处理' : authMode === 'login' ? '进入智护版' : '完成注册' }}
        </button>
        <button class="quiet-action" type="button" @click="toggleAuthMode">
          {{ authMode === 'login' ? '没有账号，去注册' : '已有账号，去登录' }}
        </button>
        <p v-if="authMessage" class="form-message" :class="{ 'is-error': authMessageIsError }">
          {{ authMessage }}
        </p>
      </form>
    </section>

    <template v-else>
      <header class="app-header">
        <div>
          <p class="eyebrow">{{ todayText }}</p>
          <h1>家中环境照护</h1>
          <p>{{ selectedDevice ? `${selectedDevice.name}，${selectedDevice.statusLabel}` : '请先绑定一个设备' }}</p>
        </div>
        <div class="header-actions">
          <button class="secondary-action" type="button" @click="refreshAll" :disabled="appLoading">
            {{ appLoading ? '刷新中' : '刷新' }}
          </button>
          <VersionSwitcher variant="senior" />
          <button class="quiet-action" type="button" @click="signOut">退出</button>
        </div>
      </header>

      <section v-if="noticeText" class="notice" :class="{ 'notice--error': noticeKind === 'error' }" role="status">
        <strong>{{ noticeKind === 'error' ? '需要注意' : '提示' }}</strong>
        <span>{{ noticeText }}</span>
      </section>

      <section v-if="gasAlertVisible" class="emergency-banner">
        <div>
          <strong>燃气提醒</strong>
          <p>检测到燃气异常，请马上开窗通风，并联系家人确认。</p>
        </div>
        <button type="button" @click="activeView = 'devices'">查看设备</button>
      </section>

      <nav class="large-tabs" aria-label="主导航">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          :class="{ active: activeView === item.id }"
          @click="activeView = item.id"
        >
          <span>{{ item.icon }}</span>
          {{ item.label }}
        </button>
      </nav>

      <section v-if="activeView === 'home'" class="view view-home">
        <div class="comfort-card">
          <img src="/smart-cube-transparent.png" alt="智能桌面魔方渲染图" class="comfort-card__render" decoding="async" />
          <p class="eyebrow">当前舒适度</p>
          <strong>{{ scoreText }}</strong>
          <span>{{ scoreSummary }}</span>
          <button class="primary-action" type="button" @click="runAiAnalysis(false)" :disabled="aiLoading || !selectedDevice">
            {{ aiLoading ? '分析中' : '查看建议' }}
          </button>
        </div>

        <div class="metric-grid" aria-label="环境数据">
          <article v-for="metric in primaryMetrics" :key="metric.label" class="metric-card" :class="`tone-${metric.tone}`">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
            <small>{{ metric.hint }}</small>
          </article>
        </div>

        <div class="home-columns">
          <section class="panel">
            <div class="panel-heading">
              <h2>常用控制</h2>
              <span>{{ selectedDevice?.status === 'online' ? '可操作' : '设备离线' }}</span>
            </div>
            <div class="control-list" :class="{ disabled: !canControl }">
              <button class="control-button" type="button" @click="toggleControl('light', !controlState.light)" :disabled="!canControl">
                <span>灯光</span>
                <strong>{{ controlState.light ? '已打开' : '已关闭' }}</strong>
              </button>
              <button class="control-button" type="button" @click="toggleControl('wechat_notify', !controlState.notify)" :disabled="!canControl">
                <span>提醒</span>
                <strong>{{ controlState.notify ? '已打开' : '已关闭' }}</strong>
              </button>
              <button class="control-button" type="button" @click="toggleControl('focus_mode', !controlState.focus)" :disabled="!canControl">
                <span>安静模式</span>
                <strong>{{ controlState.focus ? '已打开' : '已关闭' }}</strong>
              </button>
            </div>
          </section>

          <section class="panel">
            <div class="panel-heading">
              <h2>重要建议</h2>
              <button type="button" @click="activeView = 'advice'">全部</button>
            </div>
            <article v-for="item in topAdvice" :key="item.title" class="advice-row" :class="`tone-${item.tone}`">
              <strong>{{ item.title }}</strong>
              <p>{{ item.body }}</p>
            </article>
          </section>
        </div>
      </section>

      <section v-else-if="activeView === 'devices'" class="view">
        <div class="section-title">
          <h2>设备与控制</h2>
          <p>选择设备、绑定新设备，并查看在线状态。</p>
        </div>

        <div class="device-layout">
          <section class="panel">
            <div class="panel-heading">
              <h2>我的设备</h2>
              <span>{{ devices.length }} 台</span>
            </div>
            <button
              v-for="device in devices"
              :key="device.id"
              class="device-row"
              :class="{ active: selectedDeviceId === device.id }"
              type="button"
              @click="selectDevice(device.id)"
            >
              <span>
                <strong>{{ device.name }}</strong>
                <small>{{ device.id }}</small>
              </span>
              <em :class="{ online: device.status === 'online' }">{{ device.statusLabel }}</em>
            </button>
            <p v-if="devices.length === 0" class="empty-text">当前账号还没有绑定设备。</p>
          </section>

          <section class="panel">
            <div class="panel-heading">
              <h2>绑定设备</h2>
              <span>输入设备编号</span>
            </div>
            <form class="bind-form" @submit.prevent="bindNewDevice">
              <label>
                <span>设备 ID</span>
                <input v-model.trim="bindForm.deviceId" placeholder="例如 DEMO-CUBE-001" />
              </label>
              <label>
                <span>设备名称</span>
                <input v-model.trim="bindForm.deviceName" placeholder="例如 客厅魔方" />
              </label>
              <button class="primary-action" type="submit">绑定设备</button>
            </form>
          </section>
        </div>

        <section class="panel">
          <div class="panel-heading">
            <h2>详细控制</h2>
            <span>{{ canControl ? '发送到当前设备' : '离线时不可控制' }}</span>
          </div>
          <div class="settings-grid" :class="{ disabled: !canControl }">
            <label class="range-control">
              <span>屏幕亮度</span>
              <strong>{{ brightness }}%</strong>
              <input v-model.number="brightness" type="range" min="20" max="100" step="5" :disabled="!canControl" @change="sendSliderControl" />
            </label>
            <button class="control-button" type="button" :disabled="!canControl" @click="toggleControl('auto_screen_brightness', true)">
              <span>自动亮度</span>
              <strong>一键打开</strong>
            </button>
            <button class="danger-action" type="button" :disabled="!selectedDevice" @click="unbindSelectedDevice">
              解绑当前设备
            </button>
          </div>
        </section>
      </section>

      <section v-else-if="activeView === 'advice'" class="view">
        <div class="section-title">
          <h2>健康建议</h2>
          <p>AI 会把数据翻译成容易执行的提醒。</p>
        </div>

        <div class="advice-actions">
          <button class="primary-action" type="button" @click="runAiAnalysis(false)" :disabled="aiLoading || !selectedDevice">
            {{ aiLoading ? '分析中' : '规则分析' }}
          </button>
          <button class="secondary-action" type="button" @click="runAiAnalysis(true)" :disabled="aiLoading || !selectedDevice">
            {{ aiLoading ? '请稍等' : '调用 LLM 分析' }}
          </button>
        </div>

        <div class="advice-layout">
          <section class="panel weekly-panel">
            <div class="panel-heading">
              <h2>本周趋势</h2>
              <span>{{ weeklySource || '待获取' }}</span>
            </div>
            <div class="weekly-report" aria-label="本周环境周报">
              <article
                v-for="day in weeklyCards"
                :key="day.key"
                class="weekly-day"
                :class="`weekly-day--${day.tone}`"
              >
                <div class="weekly-day__header">
                  <strong>{{ day.label }}</strong>
                  <span>{{ day.status }}</span>
                </div>
                <div class="weekly-day__metrics">
                  <div>
                    <b>温度</b>
                    <i><em :style="{ width: day.temperatureWidth }"></em></i>
                    <small>{{ day.temperatureText }}</small>
                  </div>
                  <div>
                    <b>湿度</b>
                    <i><em :style="{ width: day.humidityWidth }"></em></i>
                    <small>{{ day.humidityText }}</small>
                  </div>
                  <div>
                    <b>AQI</b>
                    <i><em :style="{ width: day.aqiWidth }"></em></i>
                    <small>{{ day.aqiText }}</small>
                  </div>
                </div>
              </article>
            </div>
            <p class="weekly-text">{{ weeklySummary || weeklySummaryFallback }}</p>
          </section>

          <section class="panel reminders-panel">
            <div class="panel-heading">
              <h2>提醒列表</h2>
              <span>{{ adviceItems.length }} 条</span>
            </div>
            <article v-for="item in adviceItems" :key="item.title" class="advice-row" :class="`tone-${item.tone}`">
              <strong>{{ item.title }}</strong>
              <p>{{ item.body }}</p>
              <small>{{ item.source }}</small>
            </article>
          </section>

          <section class="panel score-panel">
            <span>今日评分</span>
            <strong>{{ scoreText }}</strong>
            <p>{{ scoreSummary }}</p>
          </section>
        </div>
      </section>

      <section v-else class="view">
        <div class="section-title">
          <h2>照护记录</h2>
          <p>最近的控制、绑定和系统操作。</p>
        </div>

        <section class="panel log-panel">
          <article v-for="log in operationLogs" :key="log.id" class="log-row">
            <span>{{ formatDate(log.created_at) }}</span>
            <strong>{{ log.action }}</strong>
            <p>{{ formatLogDetail(log.detail) }}</p>
          </article>
          <p v-if="operationLogs.length === 0" class="empty-text">暂无操作记录。</p>
        </section>
      </section>
    </template>

  </main>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import '@/versions/senior/styles/base.css'
import VersionSwitcher from '@/components/VersionSwitcher.vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { BEIJING_TIME_ZONE } from '@/utils/format'
import {
  api,
  clearToken,
  getToken,
  setToken,
  type AiSuggestion,
  type DeviceInfo,
  type OperationLog,
  type SensorData,
} from '@/versions/senior/api/client'

type ViewId = 'home' | 'devices' | 'advice' | 'logs'
type Tone = 'good' | 'calm' | 'warn'
type DeviceView = {
  id: string
  name: string
  status: 'online' | 'offline'
  statusLabel: string
  temperature: number | null
  humidity: number | null
  aqi: number | null
}

const navItems: Array<{ id: ViewId; label: string; icon: string }> = [
  { id: 'home', label: '总览', icon: '⌂' },
  { id: 'devices', label: '设备', icon: '□' },
  { id: 'advice', label: '建议', icon: '✓' },
  { id: 'logs', label: '记录', icon: '≡' },
]

const activeView = ref<ViewId>('home')
const isSignedIn = ref(Boolean(getToken()))
const authMode = ref<'login' | 'register'>('login')
const authLoading = ref(false)
const authMessage = ref('')
const authMessageIsError = ref(false)
const authForm = reactive({ username: localStorage.getItem('username') || '', password: '' })

const appLoading = ref(false)
const aiLoading = ref(false)
const noticeText = ref('')
const noticeKind = ref<'info' | 'error'>('info')
let noticeTimer: ReturnType<typeof window.setTimeout> | undefined
let sensorRefreshTimer: ReturnType<typeof window.setInterval> | undefined
const ws = useWebSocket('/ws')
const selectedDeviceId = ref(localStorage.getItem('seniorSelectedDeviceId') || '')
const rawDevices = ref<DeviceInfo[]>([])
const sensorMap = ref<Record<string, SensorData | null>>({})
const aiSuggestions = ref<AiSuggestion[]>([])
const suggestionSource = ref<'llm' | 'rule' | ''>('')
const riskItems = ref<Array<{ field: string; level: 'warning' | 'critical'; title: string; message: string }>>([])
const environmentScore = ref<number | null>(null)
const scoreSummary = ref('选择设备后，可以查看环境是否适合休息。')
const weeklySummary = ref('')
const weeklySource = ref('')
type WeeklyDayReading = {
  date: string
  temperature: number | null
  humidity: number | null
  aqi: number | null
  sample_count?: number
}

const weeklyDays = ref<WeeklyDayReading[]>([])
const operationLogs = ref<OperationLog[]>([])
const bindForm = reactive({ deviceId: '', deviceName: '' })
const brightness = ref(70)
const controlState = reactive({ light: true, notify: true, focus: false })

const todayText = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
  timeZone: BEIJING_TIME_ZONE,
}).format(new Date())

const devices = computed<DeviceView[]>(() =>
  rawDevices.value.map((device) => {
    const sensor = sensorMap.value[device.device_id]
    return {
      id: device.device_id,
      name: device.device_name || device.device_id,
      status: device.status,
      statusLabel: device.status === 'online' ? '在线' : '离线',
      temperature: sensor?.temperature ?? null,
      humidity: sensor?.humidity ?? null,
      aqi: sensor?.aqi ?? null,
    }
  }),
)

const selectedDevice = computed(() => devices.value.find((device) => device.id === selectedDeviceId.value) || devices.value[0] || null)
const selectedSensor = computed(() => (selectedDevice.value ? sensorMap.value[selectedDevice.value.id] || null : null))
const canControl = computed(() => Boolean(selectedDevice.value && selectedDevice.value.status === 'online'))
const gasAlertVisible = computed(() => Number(selectedSensor.value?.gas || 0) > 0)
const scoreText = computed(() => (environmentScore.value === null ? '--' : String(environmentScore.value)))

const primaryMetrics = computed(() => [
  {
    label: '温度',
    value: `${formatMetric(selectedSensor.value?.temperature)}℃`,
    hint: temperatureHint(selectedSensor.value?.temperature),
    tone: metricTone(selectedSensor.value?.temperature, 18, 28),
  },
  {
    label: '湿度',
    value: `${formatMetric(selectedSensor.value?.humidity)}%`,
    hint: humidityHint(selectedSensor.value?.humidity),
    tone: metricTone(selectedSensor.value?.humidity, 40, 65),
  },
  {
    label: '空气',
    value: `${formatMetric(selectedSensor.value?.aqi)} AQI`,
    hint: aqiHint(selectedSensor.value?.aqi),
    tone: metricTone(selectedSensor.value?.aqi, 0, 80, true),
  },
  {
    label: 'PM2.5',
    value: `${formatMetric(selectedSensor.value?.pm25)} μg/m³`,
    hint: '估算值，仅供参考',
    tone: metricTone(selectedSensor.value?.pm25, 0, 35, true),
  },
])

const adviceItems = computed(() => {
  const riskAdvice = riskItems.value.map((risk) => ({
    title: risk.title,
    body: risk.message,
    tone: risk.level === 'critical' ? 'warn' : 'calm',
    source: '风险提醒',
  }))

  const aiAdvice = aiSuggestions.value.map((item) => ({
    title: item.title,
    body: item.desc,
    tone: mapSuggestionTone(item.icon),
    source: suggestionSource.value === 'llm' ? 'LLM 分析' : '规则分析',
  }))

  return [...riskAdvice, ...aiAdvice].length
    ? [...riskAdvice, ...aiAdvice]
    : [
        {
          title: '等待分析',
          body: '点击“规则分析”或“调用 LLM 分析”后，这里会显示建议。',
          tone: 'calm' as Tone,
          source: '未开始',
        },
      ]
})

const topAdvice = computed(() => adviceItems.value.slice(0, 2))
const weeklyCards = computed(() => {
  const readings = weeklyDays.value.length ? weeklyDays.value : buildFallbackWeeklyDays()

  return readings.slice(-7).map((day, index) => {
    const status = getWeeklyDayStatus(day)
    return {
      key: `${day.date || 'day'}-${index}`,
      label: formatWeekdayLabel(day.date, index),
      status: status.label,
      tone: status.tone,
      temperatureText: formatWeeklyMetric(day.temperature, '℃'),
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
  if (!selectedDevice.value) return '请选择设备后刷新周报。'
  return latest ? `最近状态为「${latest.status}」，重点看温度、湿度和空气质量。` : '暂无周报，请先选择设备并刷新。'
})

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
  if (value === null || value === undefined || Number.isNaN(value)) return '10%'
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
  if ((day.aqi ?? 0) >= 150) return { label: '空气差', tone: 'alert' }
  if ((day.aqi ?? 0) >= 100) return { label: '留意空气', tone: 'watch' }
  if ((day.humidity ?? 0) >= 75) return { label: '偏湿', tone: 'watch' }
  if ((day.humidity ?? 100) <= 35) return { label: '偏干', tone: 'watch' }
  if ((day.temperature ?? 22) >= 30) return { label: '偏热', tone: 'watch' }
  if ((day.temperature ?? 22) <= 18) return { label: '偏冷', tone: 'watch' }
  return { label: '舒适', tone: 'good' }
}

function buildFallbackWeeklyDays(): WeeklyDayReading[] {
  const today = new Date()
  const sensor = selectedSensor.value

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (6 - index))
    const drift = index - 3
    return {
      date: date.toISOString(),
      temperature: typeof sensor?.temperature === 'number' ? Math.max(0, sensor.temperature + drift * 0.25) : null,
      humidity: typeof sensor?.humidity === 'number' ? Math.max(0, sensor.humidity + drift * 0.8) : null,
      aqi: typeof sensor?.aqi === 'number' ? Math.max(0, sensor.aqi + drift * 1.5) : null,
    }
  })
}

function metricTone(value: number | null | undefined, min: number, max: number, lowerIsBetter = false): Tone {
  if (value === null || value === undefined || Number.isNaN(value)) return 'calm'
  if (lowerIsBetter) return value <= max ? 'good' : 'warn'
  return value >= min && value <= max ? 'good' : 'warn'
}

function temperatureHint(value: number | null | undefined) {
  if (value === null || value === undefined) return '暂无数据'
  if (value < 18) return '偏冷，注意保暖'
  if (value > 28) return '偏热，建议通风'
  return '适合休息'
}

function humidityHint(value: number | null | undefined) {
  if (value === null || value === undefined) return '暂无数据'
  if (value < 40) return '偏干，适当补水'
  if (value > 65) return '偏潮，注意除湿'
  return '体感舒适'
}

function aqiHint(value: number | null | undefined) {
  if (value === null || value === undefined) return '暂无数据'
  if (value > 100) return '建议减少开窗'
  if (value > 80) return '稍差，留意变化'
  return '空气良好'
}

function mapSuggestionTone(icon: string): Tone {
  if (icon.includes('temp') || icon.includes('wind')) return 'calm'
  if (icon.includes('warning') || icon.includes('risk')) return 'warn'
  return 'good'
}

function showNotice(message: string, kind: 'info' | 'error' = 'info') {
  clearNoticeTimer()
  noticeText.value = message
  noticeKind.value = kind
  noticeTimer = window.setTimeout(dismissNotice, 5000)
}

function dismissNotice() {
  clearNoticeTimer()
  noticeText.value = ''
}

function clearNoticeTimer() {
  if (!noticeTimer) return
  window.clearTimeout(noticeTimer)
  noticeTimer = undefined
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

function toggleAuthMode() {
  authMode.value = authMode.value === 'login' ? 'register' : 'login'
  authMessage.value = ''
  authMessageIsError.value = false
}

async function handleAuth() {
  if (!authForm.username || !authForm.password) {
    authMessage.value = '请输入账号和密码'
    authMessageIsError.value = true
    return
  }
  if (authMode.value === 'register' && authForm.username.trim().length < 2) {
    authMessage.value = '用户名至少 2 个字符'
    authMessageIsError.value = true
    return
  }
  if (authMode.value === 'register' && authForm.password.length < 6) {
    authMessage.value = '密码至少 6 个字符'
    authMessageIsError.value = true
    return
  }

  authLoading.value = true
  authMessage.value = ''

  try {
    if (authMode.value === 'register') {
      await api.register(authForm.username, authForm.password)
      authMode.value = 'login'
      authMessage.value = '注册成功，请登录'
      authMessageIsError.value = false
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
    authMessageIsError.value = true
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
  showNotice('正在同步数据')

  try {
    await loadDevices()
    await Promise.all([loadAiData(false), loadOperationLogs()])
    showNotice('数据已更新')
  } catch (error) {
    showNotice(getErrorMessage(error, '同步失败，请检查后端服务'), 'error')
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
  if (typeof data.light === 'boolean') controlState.light = data.light
  if (typeof data.wechat_notify === 'boolean') controlState.notify = data.wechat_notify
  if (typeof data.focus_mode === 'boolean') controlState.focus = data.focus_mode
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

async function refreshDeviceData(deviceId: string, notify = true) {
  try {
    const data = await api.getLatestData(deviceId)
    sensorMap.value = {
      ...sensorMap.value,
      [deviceId]: data,
    }
    applyHardwareControlState(deviceId, data)
    if (notify) showNotice('设备数据已刷新')
  } catch (error) {
    if (notify) showNotice(getErrorMessage(error, '读取设备数据失败'), 'error')
  }
}

async function selectDevice(deviceId: string) {
  selectedDeviceId.value = deviceId
  localStorage.setItem('seniorSelectedDeviceId', deviceId)
  await Promise.all([refreshDeviceData(deviceId, false), loadAiData(false), loadOperationLogs()])
  showNotice('已切换设备')
}

async function loadAiData(forceLlm: boolean) {
  if (!selectedDevice.value) return

  aiLoading.value = true
  try {
    const deviceId = selectedDevice.value.id
    const [score, risks, suggestions, weekly] = await Promise.all([
      api.getScore(deviceId),
      api.getRisks(deviceId),
      api.getSuggestions(deviceId, forceLlm),
      api.getWeeklyReport(deviceId, forceLlm),
    ])

    environmentScore.value = score.score
    scoreSummary.value = score.summary || '当前环境整体平稳。'
    riskItems.value = risks.risks || []
    aiSuggestions.value = suggestions.suggestions || []
    suggestionSource.value = suggestions.source || (forceLlm ? 'llm' : 'rule')
    weeklySummary.value = weekly.summary || ''
    weeklySource.value = weekly.source === 'llm' ? 'LLM 周报' : '规则周报'
    weeklyDays.value = weekly.days || []
  } catch (error) {
    showNotice(getErrorMessage(error, 'AI 分析失败'), 'error')
  } finally {
    aiLoading.value = false
  }
}

async function runAiAnalysis(forceLlm: boolean) {
  await loadAiData(forceLlm)
  if (noticeKind.value !== 'error') showNotice(forceLlm ? 'LLM 分析已完成' : '规则分析已完成')
}

async function loadOperationLogs() {
  try {
    const page = await api.getOperationLogs(selectedDevice.value?.id)
    operationLogs.value = page.items || []
  } catch {
    operationLogs.value = []
  }
}

async function toggleControl(command: string, enabled: boolean) {
  if (!selectedDevice.value) return

  try {
    await api.sendControl(selectedDevice.value.id, command, enabled ? 'on' : 'off')
    if (command === 'light') controlState.light = enabled
    if (command === 'wechat_notify') controlState.notify = enabled
    if (command === 'focus_mode') controlState.focus = enabled
    showNotice('控制指令已发送')
    await loadOperationLogs()
  } catch (error) {
    showNotice(getErrorMessage(error, '发送控制失败'), 'error')
  }
}

async function sendSliderControl() {
  if (!selectedDevice.value) return

  try {
    await api.sendControl(selectedDevice.value.id, 'screen_brightness', String(brightness.value))
    showNotice('亮度已发送')
    await loadOperationLogs()
  } catch (error) {
    showNotice(getErrorMessage(error, '亮度设置失败'), 'error')
  }
}

async function bindNewDevice() {
  if (!bindForm.deviceId || !bindForm.deviceName) {
    showNotice('请填写设备 ID 和设备名称', 'error')
    return
  }

  try {
    await api.bindDevice(bindForm.deviceId, bindForm.deviceName)
    bindForm.deviceId = ''
    bindForm.deviceName = ''
    await refreshAll()
    showNotice('设备已绑定')
  } catch (error) {
    showNotice(getErrorMessage(error, '绑定设备失败'), 'error')
  }
}

async function unbindSelectedDevice() {
  if (!selectedDevice.value) return

  try {
    await api.unbindDevice(selectedDevice.value.id)
    selectedDeviceId.value = ''
    await refreshAll()
    showNotice('设备已解绑')
  } catch (error) {
    showNotice(getErrorMessage(error, '解绑失败'), 'error')
  }
}

function formatDate(value?: string) {
  if (!value) return '刚刚'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  }).format(new Date(value))
}

function formatLogDetail(value?: string) {
  if (!value) return '无详细信息'
  try {
    const parsed = JSON.parse(value) as Record<string, unknown>
    return Object.entries(parsed)
      .map(([key, item]) => `${key}: ${String(item)}`)
      .join('，')
  } catch {
    return value
  }
}

onMounted(() => {
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
  sensorRefreshTimer = window.setInterval(() => {
    if (isSignedIn.value && selectedDeviceId.value) {
      void refreshDeviceData(selectedDeviceId.value, false)
    }
  }, 5000)
})

onBeforeUnmount(() => {
  clearNoticeTimer()
  if (sensorRefreshTimer) window.clearInterval(sensorRefreshTimer)
})
</script>
