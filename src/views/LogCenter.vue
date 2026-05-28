<template>
  <div class="log-center-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">日志中心</h1>
        <p class="page-desc">查看设备控制操作和语音交互记录</p>
      </div>
      <el-button :loading="loading" @click="fetchLogs">刷新</el-button>
    </div>

    <el-tabs v-model="activeTab" class="log-tabs">
      <el-tab-pane label="操作日志" name="operation">
        <el-table v-loading="loading" :data="operationLogs" class="data-table" height="560">
          <el-table-column prop="created_at" label="时间" min-width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="device_id" label="设备 ID" min-width="150" />
          <el-table-column prop="action" label="操作" min-width="140">
            <template #default="{ row }">
              <el-tag effect="plain">{{ row.action }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情" min-width="260" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP" min-width="130" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="语音日志" name="voice">
        <el-table v-loading="loading" :data="voiceLogs" class="data-table" height="560">
          <el-table-column prop="created_at" label="时间" min-width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="device_id" label="设备 ID" min-width="150" />
          <el-table-column prop="command_text" label="语音内容" min-width="220" />
          <el-table-column prop="intent" label="意图" min-width="130" />
          <el-table-column prop="executed" label="执行" width="90">
            <template #default="{ row }">
              <el-tag :type="row.executed ? 'success' : 'info'" effect="plain">
                {{ row.executed ? '已执行' : '未执行' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_text" label="回复" min-width="220" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getOperationLogs, getVoiceLogs, type OperationLogItem, type VoiceLogItem } from '@/api/log'

defineOptions({ name: 'LogCenterPage' })

const activeTab = ref<'operation' | 'voice'>('operation')
const loading = ref(false)
const operationLogs = ref<OperationLogItem[]>([])
const voiceLogs = ref<VoiceLogItem[]>([])

function formatDateTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

async function fetchLogs() {
  loading.value = true
  try {
    if (activeTab.value === 'operation') {
      const result = await getOperationLogs({ page: 1, page_size: 100 })
      operationLogs.value = result.items || []
    } else {
      const result = await getVoiceLogs({ page: 1, page_size: 100 })
      voiceLogs.value = result.items || []
    }
  } catch {
    ElMessage.error('日志加载失败')
  } finally {
    loading.value = false
  }
}

watch(activeTab, fetchLogs)
onMounted(fetchLogs)
</script>

<style scoped>
.log-center-page {
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
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-amber));
  box-shadow: 0 0 16px rgba(6, 182, 212, 0.42);
}

.page-desc {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.log-tabs {
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

.log-tabs::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-cube-primary), var(--color-cube-amber), transparent);
  opacity: 0.62;
}

.data-table {
  width: 100%;
}
</style>
