import { describe, expect, it } from 'vitest'
import {
  formatLogDetail,
  formatMetric,
  getWeeklyDayStatus,
  normalizeDeviceName,
} from '@/versions/public/utils/formatters'
import {
  getAqiStatus,
  getHumidityStatus,
  getTemperatureStatus,
} from '@/utils/sensorStatus'

describe('public formatters', () => {
  it('formats missing and decimal metrics', () => {
    expect(formatMetric(null)).toBe('--')
    expect(formatMetric(22.25)).toBe('22.3')
  })

  it('normalizes an empty device name', () => {
    expect(normalizeDeviceName({
      device_id: 'cube-1',
      device_name: ' ',
      status: 'online',
    })).toBe('cube-1')
  })

  it('classifies weekly environmental readings', () => {
    expect(getWeeklyDayStatus({
      date: '2026-07-29',
      temperature: 24,
      humidity: 50,
      aqi: 160,
    }).tone).toBe('alert')
  })

  it('formats structured operation details safely', () => {
    expect(formatLogDetail('{"light":true,"level":2}')).toBe(
      'light: true · level: 2',
    )
    expect(formatLogDetail('plain text')).toBe('plain text')
  })
})

describe('sensor status thresholds', () => {
  it('classifies temperature, humidity and AQI boundaries', () => {
    expect(getTemperatureStatus(31)).toBe('danger')
    expect(getHumidityStatus(75)).toBe('warning')
    expect(getAqiStatus(80)).toBe('normal')
  })
})
