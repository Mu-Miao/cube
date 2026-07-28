<template>
  <div class="version-switcher" :class="`version-switcher--${variant}`">
    <button
      class="version-switcher__button"
      type="button"
      title="切换前端版本"
      aria-label="切换前端版本"
      :aria-expanded="menuOpen"
      @click="menuOpen = !menuOpen"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Zm8 4a7.8 7.8 0 0 0-.1-1l2-1.6-2-3.5-2.4 1a7.4 7.4 0 0 0-1.8-1L15.4 3h-4l-.4 2.7c-.6.2-1.2.6-1.8 1l-2.4-1-2 3.5 2 1.6a7.8 7.8 0 0 0 0 2l-2 1.6 2 3.5 2.4-1c.6.4 1.2.7 1.8 1l.4 2.7h4l.4-2.7c.6-.2 1.2-.6 1.8-1l2.4 1 2-3.5-2-1.6c.1-.3.1-.7.1-1Z" />
      </svg>
      <span class="version-switcher__label">设置</span>
      <small>{{ currentModeTitle }}</small>
    </button>

    <div v-if="menuOpen" class="version-switcher__panel">
      <p>前端版本</p>
      <a
        v-for="mode in appModes"
        :key="mode.id"
        class="version-switcher__option"
        :class="{ 'version-switcher__option--active': mode.id === currentMode }"
        :href="getModeHref(mode.id)"
        :aria-current="mode.id === currentMode ? 'page' : undefined"
        @click="mode.id === currentMode && $event.preventDefault()"
      >
        <span>
          {{ mode.title }}
          <svg v-if="mode.id === currentMode" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9.2 16.6 4.9 12.3l-1.4 1.4 5.7 5.7L21 7.6 19.6 6.2 9.2 16.6Z" />
          </svg>
        </span>
        <small>{{ mode.description }}</small>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

type AppModeId = 'teen' | 'public' | 'senior'

withDefaults(defineProps<{
  variant?: 'toolbar' | 'dark' | 'senior'
}>(), {
  variant: 'toolbar',
})

const route = useRoute()
const menuOpen = ref(false)

const currentMode = computed<AppModeId>(() => {
  if (route.path.startsWith('/public') || route.path === '/login' || route.path === '/register') return 'public'
  if (route.path.startsWith('/senior')) return 'senior'
  return 'teen'
})

const appModes: Array<{ id: AppModeId; title: string; description: string }> = [
  { id: 'teen', title: '青少年版', description: '完整控制台与 AI 分析界面' },
  { id: 'public', title: '大众版', description: '轻量、安静的日常查看界面' },
  { id: 'senior', title: '老年版', description: '大字号、低密度照护界面' },
]

const entryPaths: Record<AppModeId, string> = {
  teen: '/teen/dashboard',
  public: '/public',
  senior: '/senior',
}

const currentModeTitle = computed(() => appModes.find((mode) => mode.id === currentMode.value)?.title || '当前版本')

function getModeHref(mode: AppModeId) {
  return entryPaths[mode]
}

watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
  },
)
</script>

<style scoped>
.version-switcher {
  position: relative;
  z-index: 20;
}

.version-switcher__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 36px;
  min-width: 172px;
  border: 1px solid rgba(190, 231, 255, 0.2);
  border-radius: 12px;
  padding: 0 12px;
  color: rgba(245, 250, 255, 0.9);
  background:
    linear-gradient(145deg, rgba(34, 211, 238, 0.12), rgba(105, 165, 255, 0.08)),
    rgba(115, 196, 255, 0.075);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 8px 18px rgba(0, 4, 20, 0.12);
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}

.version-switcher__button:hover {
  border-color: rgba(34, 211, 238, 0.34);
  background:
    linear-gradient(145deg, rgba(34, 211, 238, 0.18), rgba(105, 165, 255, 0.12)),
    rgba(255, 255, 255, 0.09);
  transform: translateY(-1px);
}

.version-switcher__button svg {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  fill: currentColor;
}

.version-switcher__button small {
  color: rgba(215, 230, 245, 0.62);
  font-size: 11px;
  font-weight: 700;
}

.version-switcher__label {
  font-size: 13px;
  font-weight: 800;
}

.version-switcher__panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: min(282px, calc(100vw - 36px));
  padding: 10px;
  border: 1px solid rgba(188, 232, 255, 0.22);
  border-radius: 18px;
  background: rgba(5, 18, 40, 0.9);
  box-shadow: 0 24px 64px rgba(0, 5, 20, 0.36);
  backdrop-filter: blur(24px) saturate(1.75);
  -webkit-backdrop-filter: blur(24px) saturate(1.75);
}

.version-switcher__panel p {
  margin: 4px 8px 8px;
  color: rgba(245, 245, 247, 0.64);
  font-size: 12px;
  font-weight: 800;
}

.version-switcher__option {
  display: grid;
  gap: 4px;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  color: rgba(245, 245, 247, 0.88);
  text-decoration: none;
}

.version-switcher__option:hover,
.version-switcher__option--active {
  border-color: rgba(188, 232, 255, 0.24);
  background: rgba(255, 255, 255, 0.08);
}

.version-switcher__option--active {
  border-color: rgba(96, 165, 250, 0.56);
  background: rgba(37, 99, 235, 0.22);
  box-shadow: inset 0 0 0 1px rgba(147, 197, 253, 0.18);
}

.version-switcher__option span {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-weight: 800;
}

.version-switcher__option span svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  fill: #93c5fd;
}

.version-switcher__option small {
  color: rgba(245, 245, 247, 0.56);
  line-height: 1.45;
}

.version-switcher__option--active small {
  color: rgba(245, 245, 247, 0.72);
}

.version-switcher--dark .version-switcher__button {
  min-width: 128px;
  border-radius: 999px;
  color: var(--text-primary, #f5f5f7);
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.12);
}

.version-switcher--dark .version-switcher__button small {
  display: none;
}

.version-switcher--senior .version-switcher__button {
  min-height: 54px;
  height: 54px;
  min-width: 7.2rem;
  border: 0;
  border-radius: 12px;
  color: var(--green, #217344);
  background: var(--green-soft, #e3f3e7);
  box-shadow: none;
}

.version-switcher--senior .version-switcher__button small {
  display: none;
}

@media (max-width: 760px) {
  .version-switcher__button {
    min-width: 42px;
    width: 42px;
    padding: 0;
  }

  .version-switcher__label,
  .version-switcher__button small {
    display: none;
  }

  .version-switcher--dark .version-switcher__button {
    min-width: 42px;
    width: 42px;
  }

  .version-switcher--senior .version-switcher__button {
    width: auto;
    min-width: 6rem;
  }

  .version-switcher--senior .version-switcher__label {
    display: inline;
  }
}
</style>
