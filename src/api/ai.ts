import api from './index'

export interface EnvironmentScore {
  score: number
  level: 'excellent' | 'good' | 'fair' | 'poor' | 'no_data'
  summary?: string
  breakdown?: {
    temperature: number
    humidity: number
    air_quality: number
    comfort: number
  }
}

export interface AiSuggestion {
  icon: string
  title: string
  desc: string
}

export interface AiSuggestions {
  suggestions: AiSuggestion[]
}

export interface RiskWarnings {
  risks: Array<{
    field: string
    level: 'warning' | 'critical'
    title: string
    message: string
  }>
  highest_level: 'none' | 'warning' | 'critical'
}

export interface WeeklyReport {
  days: Array<{
    date: string
    temperature: number | null
    humidity: number | null
    aqi: number | null
    sample_count: number
  }>
}

export const getEnvironmentScore = (deviceId: string) => {
  return api.get(`/ai/${deviceId}/score`) as Promise<EnvironmentScore>
}

export const getRiskWarnings = (deviceId: string) => {
  return api.get(`/ai/${deviceId}/risks`) as Promise<RiskWarnings>
}

export const getAiSuggestions = (deviceId: string) => {
  return api.get(`/ai/${deviceId}/suggestions`) as Promise<AiSuggestions>
}

export const getWeeklyReport = (deviceId: string) => {
  return api.get(`/ai/${deviceId}/weekly-report`) as Promise<WeeklyReport>
}
