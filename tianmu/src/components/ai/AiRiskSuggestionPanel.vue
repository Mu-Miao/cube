<template>
  <section class="alert-suggest-row">
    <div class="panel animate-fade-up-blur">
      <h2 class="section-title">风险预警</h2>
      <div class="risk-list">
        <div class="risk-item" :class="mold.className">
          <span class="risk-icon">{{ mold.icon }}</span>
          <div class="risk-info">
            <span class="risk-label">霉菌风险</span>
            <span class="risk-value">{{ mold.text }}</span>
          </div>
        </div>
        <div class="risk-item" :class="gas.className">
          <span class="risk-icon">{{ gas.icon }}</span>
          <div class="risk-info">
            <span class="risk-label">燃气安全</span>
            <span class="risk-value">{{ gas.text }}</span>
          </div>
        </div>
        <div
          v-for="risk in risks"
          :key="`${risk.field}-${risk.title}`"
          class="risk-item"
          :class="risk.level === 'critical' ? 'risk-critical' : 'risk-medium'"
        >
          <span class="risk-icon">{{ risk.level === 'critical' ? '⚠' : '!' }}</span>
          <div class="risk-info">
            <span class="risk-label">{{ risk.title }}</span>
            <span class="risk-value">{{ risk.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="panel animate-fade-up-blur">
      <h2 class="section-title">智能建议</h2>
      <div class="suggest-list">
        <div v-for="item in suggestions" :key="`${item.title}-${item.desc}`" class="suggest-item">
          <span class="suggest-icon">{{ item.icon }}</span>
          <div class="suggest-info">
            <span class="suggest-title">{{ item.title }}</span>
            <span class="suggest-desc">{{ item.desc }}</span>
          </div>
        </div>
      </div>
      <div class="suggest-footer">
        <span class="ai-disclaimer">仅供参考</span>
        <span class="source-badge" :class="source === 'llm' ? 'badge-llm' : 'badge-rule'">
          {{ source === 'llm' ? '🤖 LLM 生成' : '⚙️ 规则引擎' }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
type RiskStatus = { text: string; className: string; icon: string }
type RiskItem = {
  field: string
  level: 'warning' | 'critical'
  title: string
  message: string
}
type Suggestion = { icon: string; title: string; desc: string }

defineProps<{
  mold: RiskStatus
  gas: RiskStatus
  risks: RiskItem[]
  suggestions: Suggestion[]
  source: 'llm' | 'rule' | ''
}>()
</script>

<style scoped>
.alert-suggest-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.panel {
  border-radius: 20px;
  padding: 24px;
  background: linear-gradient(145deg, rgba(102, 198, 255, 0.075), rgba(5, 22, 49, 0.31));
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}
.section-title { margin: 0 0 18px; font-size: 18px; color: rgba(255, 255, 255, 0.92); }
.risk-list,
.suggest-list { display: flex; flex-direction: column; gap: 12px; }
.risk-item,
.suggest-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.055);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.risk-low { border-color: rgba(16, 185, 129, 0.32); }
.risk-medium,
.risk-high { border-color: rgba(245, 158, 11, 0.36); }
.risk-critical { border-color: rgba(239, 68, 68, 0.4); }
.risk-icon,
.suggest-icon { flex: 0 0 auto; font-size: 20px; }
.risk-info,
.suggest-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.risk-label,
.suggest-title { font-weight: 600; color: rgba(255, 255, 255, 0.9); }
.risk-value,
.suggest-desc { font-size: 13px; color: rgba(255, 255, 255, 0.62); }
.suggest-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
.ai-disclaimer { font-size: 12px; color: rgba(255, 255, 255, 0.42); }
.source-badge { padding: 4px 9px; border-radius: 999px; font-size: 11px; }
.badge-llm { background: rgba(6, 182, 212, 0.16); color: #67e8f9; }
.badge-rule { background: rgba(163, 230, 53, 0.12); color: #bef264; }
@media (max-width: 768px) {
  .alert-suggest-row { grid-template-columns: 1fr; }
}
</style>
