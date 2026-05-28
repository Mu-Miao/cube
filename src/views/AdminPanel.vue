<template>
  <div class="admin-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">管理员后台</h1>
        <p class="page-desc">系统统计、用户管理和设备管理</p>
      </div>
      <el-button :loading="loading" @click="fetchAdminData">刷新</el-button>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-label">用户数</span>
        <strong>{{ stats.user_count }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">设备数</span>
        <strong>{{ stats.device_count }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">在线设备</span>
        <strong>{{ stats.online_count }}</strong>
      </div>
      <div class="stat-card">
        <span class="stat-label">数据记录</span>
        <strong>{{ stats.data_count }}</strong>
      </div>
    </div>

    <el-tabs class="admin-tabs">
      <el-tab-pane label="用户管理">
        <el-table v-loading="loading" :data="users" height="460">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" min-width="140" />
          <el-table-column prop="email" label="邮箱" min-width="180">
            <template #default="{ row }">{{ row.email || '-' }}</template>
          </el-table-column>
          <el-table-column prop="role" label="角色" width="110">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" effect="plain">
                {{ row.role }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" effect="plain">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button
                size="small"
                :disabled="row.role === 'admin'"
                @click="handleUserStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="设备管理">
        <el-table v-loading="loading" :data="devices" height="460">
          <el-table-column prop="device_id" label="设备 ID" min-width="170" />
          <el-table-column prop="device_name" label="名称" min-width="140" />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === 'online' ? 'success' : 'info'" effect="plain">
                {{ row.status === 'online' ? '在线' : '离线' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="bound_user_id" label="绑定用户" width="110">
            <template #default="{ row }">{{ row.bound_user_id || '-' }}</template>
          </el-table-column>
          <el-table-column prop="chip_model" label="芯片" min-width="120" />
          <el-table-column prop="firmware_version" label="固件" min-width="110" />
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-button size="small" type="danger" plain @click="handleDeleteDevice(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  deleteAdminDevice,
  getAdminDevices,
  getAdminStats,
  getAdminUsers,
  updateUserStatus,
  type AdminDevice,
  type AdminStats,
  type AdminUser,
} from '@/api/admin'

defineOptions({ name: 'AdminPanelPage' })

const loading = ref(false)
const stats = reactive<AdminStats>({
  user_count: 0,
  device_count: 0,
  online_count: 0,
  data_count: 0,
})
const users = ref<AdminUser[]>([])
const devices = ref<AdminDevice[]>([])

async function fetchAdminData() {
  loading.value = true
  try {
    const [statsData, userList, deviceList] = await Promise.all([
      getAdminStats(),
      getAdminUsers(),
      getAdminDevices(),
    ])
    Object.assign(stats, statsData)
    users.value = userList || []
    devices.value = deviceList || []
  } catch {
    ElMessage.error('管理员数据加载失败，请确认当前账号具备管理员权限')
  } finally {
    loading.value = false
  }
}

async function handleUserStatus(user: AdminUser) {
  try {
    await updateUserStatus(user.id, !user.is_active)
    ElMessage.success('用户状态已更新')
    fetchAdminData()
  } catch {
    ElMessage.error('用户状态更新失败')
  }
}

async function handleDeleteDevice(device: AdminDevice) {
  try {
    await ElMessageBox.confirm(`确认删除设备 ${device.device_id}？`, '删除设备', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteAdminDevice(device.device_id)
    ElMessage.success('设备已删除')
    fetchAdminData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('设备删除失败')
    }
  }
}

onMounted(fetchAdminData)
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title::before {
  content: '';
  width: 4px;
  height: 23px;
  border-radius: var(--radius-full);
  background: linear-gradient(180deg, var(--color-cube-violet), var(--color-cube-primary));
  box-shadow: 0 0 16px rgba(139, 92, 246, 0.38);
}

.page-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  padding: 18px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.012)),
    var(--bg-card);
  border: var(--border-glass);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
  transition:
    transform var(--transition-spring),
    border-color var(--transition-base),
    box-shadow var(--transition-base);
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, var(--color-cube-violet), var(--color-cube-primary), transparent);
  opacity: 0.72;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(139, 92, 246, 0.34);
  box-shadow: var(--shadow-holo);
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-card strong {
  font-family: var(--font-mono);
  font-size: 28px;
  color: var(--text-primary);
}

.admin-tabs {
  position: relative;
  overflow: hidden;
  padding: 20px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.012)),
    var(--bg-card);
  border: var(--border-glass);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.admin-tabs::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-cube-violet), var(--color-cube-primary), transparent);
  opacity: 0.62;
}

@media (max-width: 960px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
