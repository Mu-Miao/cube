import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElNotification } from 'element-plus/es/components/notification/index.mjs'

// 普通提示（右上角弹出，5秒自动消失）
export function showInfoToast(message: string) {
  ElMessage({ message, type: 'info', duration: 5000 })
}

export function showSuccessToast(message: string) {
  ElMessage({ message, type: 'success', duration: 5000 })
}

export function showWarningToast(message: string) {
  ElMessage({ message, type: 'warning', duration: 5000 })
}

export function showErrorToast(message: string) {
  ElMessage({ message, type: 'error', duration: 5000 })
}

// 严重告警通知（右上角弹出，需手动关闭）
export function showDangerNotification(title: string, message: string) {
  ElNotification({
    title,
    message,
    type: 'error',
    duration: 0, // 不自动关闭
    position: 'top-right',
  })
}
