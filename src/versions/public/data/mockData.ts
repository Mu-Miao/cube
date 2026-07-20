export type DeviceState = 'online' | 'offline'

export type Device = {
  id: string
  name: string
  subtitle: string
  status: DeviceState
  temperature: number | null
  humidity: number | null
  aqi: number | null
}

export type Insight = {
  title: string
  body: string
  tone: 'green' | 'blue' | 'amber'
  time: string
}
