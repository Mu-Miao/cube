import type { DeviceInfo } from '@/versions/public/api/client'
import { BEIJING_TIME_ZONE } from '@/utils/format'

export type WeeklyDayReading = {
  date: string
  temperature: number | null
  humidity: number | null
  aqi: number | null
  sample_count?: number
}

export function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function formatWeeklyMetric(
  value: number | null | undefined,
  unit: string,
) {
  const text = formatMetric(value)
  return text === '--' || !unit ? text : `${text}${unit}`
}

export function metricWidth(
  value: number | null | undefined,
  min: number,
  max: number,
) {
  if (value === null || value === undefined || Number.isNaN(value)) return '8%'
  const normalized = Math.max(0, Math.min(1, (value - min) / (max - min)))
  return `${Math.round(18 + normalized * 82)}%`
}

export function formatWeekdayLabel(date: string, index: number) {
  const parsed = new Date(date)
  if (!Number.isNaN(parsed.getTime())) {
    return new Intl.DateTimeFormat('zh-CN', { weekday: 'short' }).format(parsed)
  }
  return ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index % 7]
}

export function getWeeklyDayStatus(
  day: WeeklyDayReading,
): { label: string; tone: 'good' | 'watch' | 'alert' } {
  if ((day.aqi ?? 0) >= 150) return { label: '空气较差', tone: 'alert' }
  if ((day.aqi ?? 0) >= 100) return { label: '空气关注', tone: 'watch' }
  if ((day.humidity ?? 0) >= 75) return { label: '偏湿', tone: 'watch' }
  if ((day.humidity ?? 100) <= 35) return { label: '偏干', tone: 'watch' }
  if ((day.temperature ?? 22) >= 30) return { label: '偏热', tone: 'watch' }
  if ((day.temperature ?? 22) <= 18) return { label: '偏冷', tone: 'watch' }
  return { label: '舒适', tone: 'good' }
}

export function normalizeDeviceName(device: DeviceInfo) {
  return device.device_name?.trim() || device.device_id || '未命名设备'
}

export function normalizeDeviceSubtitle(device: DeviceInfo) {
  const parts = [device.device_id, device.chip_model].filter(
    (part): part is string => Boolean(part?.trim()),
  )
  return parts.length ? parts.join(' · ') : '无设备信息'
}

export function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

export function getScoreSummary(score: number) {
  if (score >= 90) return '当前环境非常舒适，各项指标表现优秀。'
  if (score >= 70) return '当前环境整体良好，建议继续保持。'
  if (score >= 40) return '当前环境一般，部分指标需要关注。'
  return '当前环境较差，建议尽快通风并检查设备状态。'
}

export function mapSuggestionTone(icon: string): 'green' | 'blue' | 'amber' {
  if (['wind', 'air', 'aqi', 'leaf', 'ok'].includes(icon)) return 'green'
  if (['humidity', 'water', 'temp', 'temperature'].includes(icon)) return 'blue'
  return 'amber'
}

export function formatDate(value?: string) {
  if (!value) return '--'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  }).format(new Date(value))
}

export function formatLogDetail(detail?: string) {
  if (!detail) return '无详情'
  try {
    const parsed = JSON.parse(detail)
    return Object.entries(parsed)
      .map(([key, value]) => `${key}: ${formatLogValue(value)}`)
      .join(' · ')
  } catch {
    return detail
  }
}

function formatLogValue(value: unknown): string {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (!entries.length) return '{}'
    return entries
      .map(([key, item]) => `${key}=${formatLogValue(item)}`)
      .join(', ')
  }
  return String(value)
}
