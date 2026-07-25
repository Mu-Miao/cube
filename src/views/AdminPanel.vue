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
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'
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
/* ---- Liquid Glass Tokens ---- */
.admin-page {
  --glass-bg: linear-gradient(145deg, rgba(102, 198, 255, 0.075), rgba(5, 22, 49, 0.31));
  --glass-border: 1px solid rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  --glass-inner-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15);
  --glass-radius: 20px;
  --glass-blur: blur(18px);
  --glass-saturation: saturate(1.6);

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
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturation);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  transition:
    transform var(--transition-spring),
    background var(--transition-base),
    border-color var(--transition-base),
    box-shadow var(--transition-base);
}

/* Soft white top-edge highlight arc */
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.35),
    transparent
  );
  opacity: 0.8;
}

.stat-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.28);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow), 0 12px 40px rgba(0, 0, 0, 0.18);
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
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur) var(--glass-saturation);
  -webkit-backdrop-filter: var(--glass-blur) var(--glass-saturation);
  border: var(--glass-border);
  border-radius: var(--glass-radius);
  box-shadow: var(--glass-shadow), var(--glass-inner-shadow);
  transition:
    background var(--transition-base),
    box-shadow var(--transition-base);
}

/* Soft white top-edge highlight arc */
.admin-tabs::before {
  content: '';
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.35),
    transparent
  );
  opacity: 0.8;
}

.admin-tabs:hover {
  background: rgba(255, 255, 255, 0.095);
}

@media (max-width: 960px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
