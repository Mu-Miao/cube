<!-- Devices.vue -->
<!-- 设备管理页 -->
<!-- 功能：设备列表展示、搜索筛选排序、绑定/解绑设备、查看详情跳转控制面板 -->
<template>
  <div class="devices-page">
    <!-- 页面标题栏 -->
    <div class="devices-header">
      <h1 class="devices-title">设备管理</h1>
      <el-button type="primary" @click="showBindDialog = true">
        <el-icon><Plus /></el-icon>
        绑定新设备
      </el-button>
    </div>

    <!-- 搜索与筛选栏 -->
    <div class="devices-toolbar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索设备名称或ID"
        clearable
        class="devices-search"
        :prefix-icon="Search"
      />
      <el-select v-model="statusFilter" placeholder="状态筛选" class="devices-filter">
        <el-option label="全部" value="all" />
        <el-option label="在线" value="online" />
        <el-option label="离线" value="offline" />
      </el-select>
      <el-select v-model="sortBy" placeholder="排序" class="devices-sort">
        <el-option label="按名称" value="name" />
        <el-option label="按状态" value="status" />
        <el-option label="按最后在线时间" value="last_seen" />
      </el-select>
    </div>

    <!-- 设备卡片网格 -->
    <div v-loading="loading" class="devices-grid">
      <div
        v-for="device in filteredDevices"
        :key="device.device_id"
        class="device-card"
        :class="{ 'device-card--offline': device.status === 'offline' }"
      >
        <!-- 设备名称 -->
        <div class="device-card__name">{{ device.device_name }}</div>
        <!-- 设备 ID -->
        <div class="device-card__id">{{ device.device_id }}</div>

        <!-- 状态与芯片信息 -->
        <div class="device-card__info">
          <div class="device-card__status">
            <DeviceStatusDot :status="device.status" />
            <span :class="device.status === 'online' ? 'text-online' : 'text-offline'">
              {{ device.status === 'online' ? '在线' : '离线' }}
            </span>
          </div>
          <div class="device-card__chip">
            {{ device.chip_model || 'ESP32-S3' }}
          </div>
        </div>

        <!-- 固件版本 -->
        <div class="device-card__firmware">
          固件: {{ device.firmware_version || '-' }}
        </div>

        <!-- 最后心跳 -->
        <div class="device-card__heartbeat">
          最后心跳: {{ formatRelativeTime(device.last_seen) }}
        </div>

        <!-- 操作按钮 -->
        <div class="device-card__actions">
          <el-button size="small" @click="goToControl(device.device_id)">
            查看详情
          </el-button>
          <el-button size="small" type="danger" plain @click="confirmUnbind(device)">
            解绑
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && filteredDevices.length === 0" class="devices-empty">
        <div class="devices-empty__icon">
          <el-icon :size="48"><Box /></el-icon>
        </div>
        <div class="devices-empty__text">暂无设备</div>
        <div class="devices-empty__hint">点击右上角「绑定新设备」添加</div>
      </div>
    </div>

    <!-- 绑定设备对话框 -->
    <el-dialog
      v-model="showBindDialog"
      title="绑定新设备"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form :model="bindForm" label-position="top">
        <el-form-item label="设备 ID（MAC 地址）">
          <el-input
            v-model="bindForm.device_id"
            placeholder="例如: AABBCCDDEEFF"
            maxlength="12"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input
            v-model="bindForm.device_name"
            placeholder="例如: 魔方终端-客厅"
            maxlength="32"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" :loading="bindLoading" @click="handleBind">
          确认绑定
        </el-button>
      </template>
    </el-dialog>

    <!-- 解绑确认对话框 -->
    <el-dialog
      v-model="showUnbindDialog"
      title="确认解绑"
      width="400px"
    >
      <div class="unbind-warning">
        <el-icon :size="24" color="var(--color-warning)"><WarningFilled /></el-icon>
        <span>解绑后设备将停止上报数据，确认？</span>
      </div>
      <div v-if="unbindTarget" class="unbind-device-info">
        设备：{{ unbindTarget.device_name }}（{{ unbindTarget.device_id }}）
      </div>
      <template #footer>
        <el-button @click="showUnbindDialog = false">取消</el-button>
        <el-button type="danger" :loading="unbindLoading" @click="handleUnbind">
          确认解绑
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search, Box, WarningFilled } from '@element-plus/icons-vue'
import DeviceStatusDot from '@/components/DeviceStatusDot.vue'
import { useDeviceStore, type DeviceInfo } from '@/store/device'
import { getDeviceList, bindDevice, unbindDevice } from '@/api/device'
import { isDemoMode } from '@/utils/demo'

defineOptions({ name: 'DevicesPage' })

const router = useRouter()
const deviceStore = useDeviceStore()
const demoMode = isDemoMode()

// 状态
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('all')
const sortBy = ref('name')

// 绑定对话框
const showBindDialog = ref(false)
const bindLoading = ref(false)
const bindForm = reactive({
  device_id: '',
  device_name: '',
})

// 解绑对话框
const showUnbindDialog = ref(false)
const unbindLoading = ref(false)
const unbindTarget = ref<DeviceInfo | null>(null)

/**
 * 相对时间格式化
 * 将 ISO 时间字符串转换为「刚刚 / X分钟前 / X小时前 / X天前」
 */
function formatRelativeTime(timeStr: string): string {
  if (!timeStr) return '-'
  const now = Date.now()
  const then = new Date(timeStr).getTime()
  const diff = now - then

  if (diff < 0) return '刚刚'
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000))
    return `${minutes}分钟前`
  }
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000))
    return `${hours}小时前`
  }
  const days = Math.floor(diff / (24 * 60 * 60 * 1000))
  return `${days}天前`
}

/**
 * 经过搜索、筛选、排序后的设备列表
 */
const filteredDevices = computed(() => {
  let list = [...deviceStore.devices]

  // 搜索过滤：按名称或 ID
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(
      (d) =>
        d.device_name.toLowerCase().includes(q) ||
        d.device_id.toLowerCase().includes(q)
    )
  }

  // 状态筛选
  if (statusFilter.value !== 'all') {
    list = list.filter((d) => d.status === statusFilter.value)
  }

  // 排序
  if (sortBy.value === 'name') {
    list.sort((a, b) => a.device_name.localeCompare(b.device_name, 'zh-CN'))
  } else if (sortBy.value === 'status') {
    // 在线优先
    list.sort((a, b) => {
      if (a.status === b.status) return 0
      return a.status === 'online' ? -1 : 1
    })
  } else if (sortBy.value === 'last_seen') {
    list.sort((a, b) => {
      const ta = new Date(a.last_seen).getTime()
      const tb = new Date(b.last_seen).getTime()
      return tb - ta // 最近在线的排前面
    })
  }

  return list
})

/**
 * 获取设备列表
 */
async function fetchDevices() {
  loading.value = true
  try {
    const res = await getDeviceList()
    deviceStore.setDevices(res || [])
  } catch {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到控制面板页
 */
function goToControl(deviceId: string) {
  const query: Record<string, string> = { deviceId }
  if (demoMode) {
    query.demo = 'true'
  }
  router.push({ path: '/control', query })
}

/**
 * 打开解绑确认弹窗
 */
function confirmUnbind(device: DeviceInfo) {
  unbindTarget.value = device
  showUnbindDialog.value = true
}

/**
 * 处理绑定设备
 */
async function handleBind() {
  if (!bindForm.device_id.trim()) {
    ElMessage.warning('请输入设备 ID')
    return
  }
  if (!bindForm.device_name.trim()) {
    ElMessage.warning('请输入设备名称')
    return
  }

  bindLoading.value = true
  try {
    await bindDevice({
      device_id: bindForm.device_id.trim(),
      device_name: bindForm.device_name.trim(),
    })
    ElMessage.success('绑定成功')
    showBindDialog.value = false
    bindForm.device_id = ''
    bindForm.device_name = ''
    fetchDevices()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg = error.response?.data?.detail || error.response?.data?.message || '绑定失败'
    ElMessage.error(msg)
  } finally {
    bindLoading.value = false
  }
}

/**
 * 处理解绑设备
 */
async function handleUnbind() {
  if (!unbindTarget.value) return

  unbindLoading.value = true
  try {
    await unbindDevice({ device_id: unbindTarget.value.device_id })
    ElMessage.success('解绑成功')
    showUnbindDialog.value = false
    unbindTarget.value = null
    fetchDevices()
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string; message?: string } } }
    const msg = error.response?.data?.detail || error.response?.data?.message || '解绑失败'
    ElMessage.error(msg)
  } finally {
    unbindLoading.value = false
  }
}

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.devices-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* === 页面标题栏 === */
.devices-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.devices-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

/* === 搜索与筛选栏 === */
.devices-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.devices-search {
  max-width: 320px;
}
.devices-filter {
  width: 120px;
}
.devices-sort {
  width: 160px;
}

/* === 设备卡片网格 === */
.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  min-height: 200px;
}

/* === 设备卡片 === */
.device-card {
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: var(--border-default);
  border-radius: var(--radius-card);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all var(--transition-base);
  animation: fade-up-blur 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.device-card:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-elevated);
  transform: translateY(-2px);
}

/* 离线设备降低对比度 */
.device-card--offline {
  opacity: 0.6;
}

/* 设备名称 */
.device-card__name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 设备 ID */
.device-card__id {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

/* 状态与芯片信息 */
.device-card__info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.device-card__status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}
.device-card__chip {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

/* 固件版本 */
.device-card__firmware {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 最后心跳 */
.device-card__heartbeat {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 操作按钮 */
.device-card__actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

/* === 空状态 === */
.devices-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-disabled);
}
.devices-empty__icon {
  margin-bottom: 16px;
  opacity: 0.4;
}
.devices-empty__text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}
.devices-empty__hint {
  font-size: 13px;
  color: var(--text-disabled);
}

/* === 解绑警告 === */
.unbind-warning {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.unbind-device-info {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 10px 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-button);
  font-family: var(--font-mono);
}

/* === Element Plus 覆盖 === */
.devices-toolbar :deep(.el-input__wrapper),
.devices-toolbar :deep(.el-select .el-input__wrapper) {
  background: var(--bg-surface);
  border: var(--border-default);
  box-shadow: none;
}
.devices-toolbar :deep(.el-input__wrapper:hover),
.devices-toolbar :deep(.el-select .el-input__wrapper:hover) {
  border-color: var(--border-hover);
}
.devices-toolbar :deep(.el-input__wrapper.is-focus),
.devices-toolbar :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: var(--color-cube-primary);
  box-shadow: 0 0 0 1px rgba(6, 182, 212, 0.2);
}
.devices-toolbar :deep(.el-input__inner) {
  color: var(--text-primary);
}
.devices-toolbar :deep(.el-input__inner::placeholder) {
  color: var(--text-disabled);
}
.devices-toolbar :deep(.el-select__placeholder) {
  color: var(--text-disabled);
}
</style>
