type ApiValidationDetail = {
  loc?: Array<string | number>
  msg?: string
  type?: string
}

const fieldLabels: Record<string, string> = {
  username: '用户名',
  password: '密码',
  confirmPassword: '确认密码',
  email: '邮箱',
  device_id: '设备 ID',
  device_name: '设备名称',
}

function formatField(loc?: Array<string | number>) {
  const fields = loc?.filter((item) => item !== 'body') ?? []
  const field = fields[fields.length - 1]
  if (field === undefined) return ''
  const key = String(field)
  return fieldLabels[key] || key
}

function translateValidationMessage(detail: ApiValidationDetail) {
  const type = detail.type || ''
  const msg = detail.msg || '格式不正确'

  if (type.includes('missing')) return '不能为空'
  if (type.includes('string_too_short')) {
    const match = msg.match(/at least\s+(\d+)/i)
    return match?.[1] ? `长度至少 ${match[1]} 个字符` : '长度太短'
  }
  if (type.includes('string_too_long')) {
    const match = msg.match(/at most\s+(\d+)/i)
    return match?.[1] ? `长度最多 ${match[1]} 个字符` : '长度太长'
  }
  if (type.includes('value_error') && type.includes('email')) return '邮箱格式不正确'
  if (type.includes('string_type')) return '必须是文本'

  return msg
}

export function formatApiError(error: unknown, fallback = '请求失败，请重试') {
  const maybeError = error as {
    message?: unknown
    response?: {
      status?: number
      data?: {
        detail?: unknown
        message?: unknown
      } | null
    }
  }
  const data = maybeError.response?.data
  const detail = data?.detail
  const message = data?.message

  if (typeof detail === 'string' && detail.trim()) return detail
  if (typeof message === 'string' && message.trim()) return message

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (!item || typeof item !== 'object') return ''

        const validation = item as ApiValidationDetail
        const field = formatField(validation.loc)
        const text = translateValidationMessage(validation)
        return field ? `${field}：${text}` : text
      })
      .filter(Boolean)

    if (messages.length) return messages.join('；')
  }

  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail)
    } catch {
      return fallback
    }
  }

  if (error instanceof Error && error.message && error.message !== '[object Object]') {
    return error.message
  }
  if (typeof maybeError.message === 'string' && maybeError.message.trim()) {
    return maybeError.message
  }

  return fallback
}
