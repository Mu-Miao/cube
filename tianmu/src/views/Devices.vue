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
      <DeviceManagementCard
        v-for="device in filteredDevices"
        :key="device.device_id"
        :device="device"
        :selected="deviceStore.selectedDeviceId === device.device_id"
        @select="selectDevice(device.device_id)"
        @details="goToControl(device.device_id)"
        @unbind="confirmUnbind(device)"
      />

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
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { Plus, Search, Box, WarningFilled } from '@element-plus/icons-vue'
import DeviceManagementCard from '@/components/devices/DeviceManagementCard.vue'
import { useDeviceStore, type DeviceInfo } from '@/stores/device'
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
 * 选中设备（供 AI 分析等其他页面使用）
 */
function selectDevice(deviceId: string) {
  deviceStore.selectDevice(deviceId)
  ElMessage.success('设备已选中，可前往 AI 分析页查看结果')
}

/**
 * 跳转到控制面板页
 */
function goToControl(deviceId: string) {
  const query: Record<string, string> = { deviceId }
  if (demoMode) {
    query.demo = 'true'
  }
  router.push({ path: '/teen/control', query })
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

<style scoped src="./styles/Devices.css"></style>
