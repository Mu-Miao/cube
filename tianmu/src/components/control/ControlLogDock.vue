<template>
  <section class="control-log-dock">
    <div class="control-panel">
      <div class="control-panel__header">
        <span class="control-panel__title">控制日志</span>
        <span class="control-panel__subtitle">近 3 天 · 最近 {{ maxLogs }} 条</span>
      </div>
      <div class="control-panel__body">
        <div v-if="logs.length === 0" class="log-empty">暂无操作记录</div>
        <div v-else class="log-list">
          <div v-for="log in logs" :key="log.id" class="log-item">
            <span class="log-item__time">{{ log.time }}</span>
            <span class="log-item__desc">{{ log.description }}</span>
            <el-tag
              :type="log.status === 'success' ? 'success' : 'danger'"
              size="small"
              effect="plain"
            >
              {{ log.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  logs: Array<{
    id: string | number
    time: string
    description: string
    status: 'success' | 'error'
  }>
  maxLogs: number
}>()
</script>

<style scoped>
.control-log-dock { position: relative; z-index: 2; }
.control-panel {
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 18px;
  padding: 18px;
  background: linear-gradient(145deg, rgba(102, 198, 255, 0.075), rgba(5, 22, 49, 0.31));
}
.control-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.control-panel__title { color: rgba(255, 255, 255, 0.9); font-weight: 600; }
.control-panel__subtitle { color: rgba(255, 255, 255, 0.48); font-size: 12px; }
.log-empty { padding: 20px; text-align: center; color: rgba(255, 255, 255, 0.42); }
.log-list { display: flex; flex-direction: column; gap: 8px; }
.log-item {
  display: grid;
  grid-template-columns: 72px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.045);
}
.log-item__time { font-family: var(--font-mono); font-size: 11px; color: rgba(255, 255, 255, 0.45); }
.log-item__desc { font-size: 13px; color: rgba(255, 255, 255, 0.75); }
</style>
