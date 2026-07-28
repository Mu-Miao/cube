export type SensorStatus = 'normal' | 'warning' | 'danger'

export function getTemperatureStatus(value: number): SensorStatus {
  if (value > 30) return 'danger'
  return value > 28 ? 'warning' : 'normal'
}

export function getHumidityStatus(value: number): SensorStatus {
  if (value > 80) return 'danger'
  return value > 70 ? 'warning' : 'normal'
}

export function getAqiStatus(value: number): SensorStatus {
  if (value > 150) return 'danger'
  return value > 100 ? 'warning' : 'normal'
}

export function getPm25Status(value: number): SensorStatus {
  if (value > 75) return 'danger'
  return value > 35 ? 'warning' : 'normal'
}

export function formatPm25(value: number | undefined): string {
  return Number.isFinite(value) && value ? value.toFixed(1) : '--'
}

export function getTvocStatus(value: number): SensorStatus {
  if (value > 300) return 'danger'
  return value > 200 ? 'warning' : 'normal'
}

export function getEco2Status(value: number): SensorStatus {
  if (value > 1000) return 'danger'
  return value > 800 ? 'warning' : 'normal'
}

export function getMoldRiskStatus(value: number): SensorStatus {
  if (value >= 3) return 'danger'
  return value >= 2 ? 'warning' : 'normal'
}
