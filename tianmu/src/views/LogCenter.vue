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
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { getOperationLogs, getVoiceLogs, type OperationLogItem, type VoiceLogItem } from '@/api/log'
import { BEIJING_TIME_ZONE } from '@/utils/format'

defineOptions({ name: 'LogCenterPage' })

const activeTab = ref<'operation' | 'voice'>('operation')
const loading = ref(false)
const operationLogs = ref<OperationLogItem[]>([])
const voiceLogs = ref<VoiceLogItem[]>([])

function formatDateTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    hour12: false,
    timeZone: BEIJING_TIME_ZONE,
  })
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
/* ---- Liquid Glass Tokens ---- */
.log-center-page {
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
  background: linear-gradient(180deg, var(--color-cube-primary), var(--color-cube-accent));
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
.log-tabs::before {
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

.log-tabs:hover {
  background: rgba(255, 255, 255, 0.095);
}

.data-table {
  width: 100%;
}
</style>
