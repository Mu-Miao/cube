/**
 * 演示模式开关。
 * 独立于模拟数据实现，避免路由层为了读取开关而加载整套 demo 依赖。
 */
export function isDemoMode(): boolean {
  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('demo') === 'true') {
    // 侧栏路由不会持续携带查询参数，因此首次开启时同步持久化。
    localStorage.setItem('demo', 'true')
    return true
  }
  return localStorage.getItem('demo') === 'true'
}

export function enableDemoMode(): void {
  localStorage.setItem('demo', 'true')
}

export function disableDemoMode(): void {
  localStorage.removeItem('demo')
}
