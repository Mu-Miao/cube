// src/utils/format.ts
// 纯工具函数
// 提供时间格式化、数值格式化等通用方法

export const BEIJING_TIME_ZONE = 'Asia/Shanghai'

/**
 * 格式化时间为 时:分 格式
 * 用于控制日志和控制面板的时间显示
 */
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  })
}

/**
 * 格式化为完整的日期时间字符串
 * 用于设备列表的"最后在线时间"等场景
 */
export function formatDateTime(date: Date): string {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: BEIJING_TIME_ZONE,
  })
}

/**
 * 格式化数字，保留指定小数位数
 * 用于传感器数据（温度、湿度等）显示
 */
export function formatNumber(value: number, decimals = 1): string {
  return value.toFixed(decimals)
}

/**
 * 格式化数字为百分比形式
 * 用于灯光亮度、设备进度等场景
 */
export function formatPercentage(value: number): string {
  return `${Math.round(value)}%`
}
