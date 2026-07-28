// src/store/device.ts
// 设备状态管理（Pinia Store）
// 管理设备列表、选中设备、设备状态更新
// 供 Dashboard 和控制面板页面共享设备状态

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** 设备信息数据结构 */
export interface DeviceInfo {
  device_id: string       // 设备唯一标识
  device_name: string     // 设备名称
  status: 'online' | 'offline'  // 在线状态
  last_seen: string       // 最后在线时间
  chip_model: string      // 芯片型号
  firmware_version: string // 固件版本
}

export const useDeviceStore = defineStore('device', () => {
  // 设备列表
  const devices = ref<DeviceInfo[]>([])
  // 加载状态（请求中）
  const loading = ref(false)
  // 当前选中的设备 ID
  const selectedDeviceId = ref<string | null>(null)

  // 计算属性：当前选中的设备对象
  const selectedDevice = computed(() => {
    if (!selectedDeviceId.value) return null
    return devices.value.find(d => d.device_id === selectedDeviceId.value)
  })

  /**
   * 设置设备列表（全量替换）
   * 从后端 API 获取到设备列表后调用
   */
  function setDevices(deviceList: DeviceInfo[]) {
    devices.value = deviceList
  }

  /**
   * 更新单个设备信息
   * 用于 WebSocket 推送的设备状态变更，按 device_id 查找并更新
   */
  function updateDevice(device: DeviceInfo) {
    const index = devices.value.findIndex(d => d.device_id === device.device_id)
    if (index >= 0) {
      devices.value[index] = device
    } else {
      devices.value.push(device)
    }
  }

  /**
   * 选择设备
   * 设置当前操作的目标设备，页面会据此显示对应的数据和控制选项
   */
  function selectDevice(deviceId: string | null) {
    selectedDeviceId.value = deviceId
  }

  return {
    devices,
    loading,
    selectedDeviceId,
    selectedDevice,
    setDevices,
    updateDevice,
    selectDevice,
  }
})
