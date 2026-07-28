<!-- ChatPanel.vue -->
<!-- 小眠 AI 对话面板 — 液态玻璃风格 -->
<!-- 右侧固定面板，支持流式输出 -->
<template>
  <transition name="chat-slide">
    <aside v-show="visible" class="chat-panel" :style="{ width: width + 'px' }">
      <!-- 顶部标题栏 -->
      <div class="chat-header">
        <div class="chat-header__info">
          <img :src="mascotImg" alt="小眠" class="chat-header__avatar" />
          <div>
            <h3 class="chat-header__title">小眠</h3>
            <span class="chat-header__status">{{ statusText }}</span>
          </div>
        </div>
        <button class="chat-header__close" @click="$emit('toggle')" title="收起">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M12 4L4 12M4 4l8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </button>
      </div>

      <!-- 消息列表 -->
      <div ref="messagesRef" class="chat-messages">
        <!-- 欢迎消息 -->
        <div class="chat-welcome">
          <img :src="mascotImg" alt="小眠" class="chat-welcome__icon" />
          <p class="chat-welcome__text">嗨！我是小眠，你的桌面魔方小助手~</p>
          <p class="chat-welcome__hint">可以问我关于设备状态、环境数据的问题哦</p>
        </div>

        <!-- 消息气泡 -->
        <div
          v-for="(msg, index) in displayMessages"
          :key="index"
          class="chat-bubble"
          :class="[
            `chat-bubble--${msg.role}`,
            { 'chat-bubble--typing': msg.role === 'assistant' && index === typingIndex },
          ]"
        >
          <div class="chat-bubble__content">{{ msg.content }}</div>
          <span v-if="msg.role === 'assistant' && index === typingIndex && !streamDone" class="chat-bubble__cursor" />
        </div>
      </div>

      <!-- 快捷提问 -->
      <div v-if="messages.length === 0" class="chat-quick">
        <button
          v-for="q in quickQuestions"
          :key="q"
          class="chat-quick__btn"
          @click="sendQuick(q)"
        >
          {{ q }}
        </button>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <div class="chat-input-wrap">
          <textarea
            ref="inputRef"
            v-model="inputText"
            class="chat-input"
            placeholder="问问小眠..."
            rows="1"
            :disabled="isLoading"
            @keydown.enter.exact.prevent="handleSend"
            @input="autoResize"
          />
          <button
            class="chat-send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="handleSend"
          >
            <svg v-if="!isLoading" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M3 9l12-6-4 6 4 6z" fill="currentColor" />
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="4" y="4" width="10" height="10" rx="2" fill="currentColor" opacity="0.6" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { streamChat, type ChatMessage } from '@/api/chat'
import { useDeviceStore } from '@/store/device'
import mascotImg from '@/assets/mascot/role_normal.webp'

defineOptions({ name: 'ChatPanel' })

const deviceStore = useDeviceStore()

const props = defineProps<{
  visible: boolean
  width?: number
}>()

defineEmits<{
  (e: 'toggle'): void
}>()

// ====== 状态 ======
const messages = ref<ChatMessage[]>([])
const streamingText = ref('')
const isLoading = ref(false)
const streamDone = ref(true)
const inputText = ref('')
const messagesRef = ref<HTMLElement>()
const inputRef = ref<HTMLTextAreaElement>()

// 快捷提问
const quickQuestions = ['当前温度怎么样？', '空气质量如何？', '帮我开一下灯']

// 展示消息列表
const displayMessages = computed(() => {
  const list = [...messages.value]
  if (streamingText.value) {
    list.push({ role: 'assistant' as const, content: streamingText.value })
  }
  return list
})

// 正在打字的消息索引
const typingIndex = computed(() => displayMessages.value.length - 1)

// 状态文字
const statusText = computed(() => {
  if (isLoading.value) return '正在思考...'
  return '在线 · 随时陪你聊天'
})

// ====== 方法 ======
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function autoResize() {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 100) + 'px'
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  scrollToBottom()

  // 开始流式请求
  isLoading.value = true
  streamDone.value = false
  streamingText.value = ''

  streamChat(
    messages.value,
    (chunk) => {
      streamingText.value += chunk
      scrollToBottom()
    },
    () => {
      // 完成：将流式文本存入消息列表
      if (streamingText.value) {
        messages.value.push({ role: 'assistant', content: streamingText.value })
      }
      streamingText.value = ''
      streamDone.value = true
      isLoading.value = false
      scrollToBottom()
    },
    (err) => {
      messages.value.push({
        role: 'assistant',
        content: `抱歉，小眠出了点问题：${err.message}。请稍后再试试~`,
      })
      streamingText.value = ''
      streamDone.value = true
      isLoading.value = false
      scrollToBottom()
    },
    deviceStore.selectedDeviceId || undefined,
  )
}

function sendQuick(text: string) {
  inputText.value = text
  handleSend()
}

// 面板打开时自动聚焦输入框
watch(
  () => props.visible,
  (val) => {
    if (val) {
      nextTick(() => inputRef.value?.focus())
    }
  },
)
</script>

<style scoped>
.chat-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(15, 18, 32, 0.88), rgba(12, 15, 28, 0.92)),
    rgba(14, 17, 30, 0.85);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    -8px 0 32px rgba(0, 0, 0, 0.15),
    inset 1px 0 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.6);
  -webkit-backdrop-filter: blur(18px) saturate(1.6);
  z-index: 90;
  overflow: hidden;
}

/* 左侧高光边线 */
.chat-panel::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 1px;
  height: 100%;
  background: linear-gradient(
    180deg,
    transparent 5%,
    rgba(255, 255, 255, 0.2) 25%,
    rgba(34, 211, 238, 0.25) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 95%
  );
  opacity: 0.5;
}

/* ====== 顶部标题栏 ====== */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.chat-header__info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header__avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: contain;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(167, 139, 250, 0.08));
  border: 1px solid rgba(34, 211, 238, 0.2);
  padding: 3px;
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.12);
}

.chat-header__title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
}

.chat-header__status {
  font-size: 11px;
  color: var(--text-disabled);
  letter-spacing: 0.2px;
}

.chat-header__close {
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: var(--text-disabled);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.chat-header__close:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

/* ====== 消息列表 ====== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

/* ====== 欢迎区 ====== */
.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px 12px 8px;
  gap: 8px;
}

.chat-welcome__icon {
  width: 64px;
  height: 64px;
  object-fit: contain;
  filter: drop-shadow(0 0 16px rgba(34, 211, 238, 0.2));
  margin-bottom: 4px;
}

.chat-welcome__text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.chat-welcome__hint {
  font-size: 12px;
  color: var(--text-disabled);
  margin: 0;
}

/* ====== 消息气泡 ====== */
.chat-bubble {
  max-width: 88%;
  animation: bubble-in 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.chat-bubble--user {
  align-self: flex-end;
}

.chat-bubble--assistant {
  align-self: flex-start;
}

.chat-bubble__content {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 用户消息 */
.chat-bubble--user .chat-bubble__content {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.15), rgba(167, 139, 250, 0.1));
  border: 1px solid rgba(34, 211, 238, 0.18);
  color: var(--text-primary);
  border-bottom-right-radius: 4px;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.06);
}

/* AI 消息 */
.chat-bubble--assistant .chat-bubble__content {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.04);
}

/* 打字光标 */
.chat-bubble__cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: var(--color-cube-primary);
  border-radius: 1px;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.8s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes bubble-in {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ====== 快捷提问 ====== */
.chat-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 8px;
}

.chat-quick__btn {
  padding: 6px 12px;
  font-size: 12px;
  font-family: var(--font-body);
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.04);
}

.chat-quick__btn:hover {
  background: rgba(34, 211, 238, 0.08);
  border-color: rgba(34, 211, 238, 0.2);
  color: var(--color-cube-primary);
}

/* ====== 输入区 ====== */
.chat-input-area {
  padding: 12px 16px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  flex-shrink: 0;
}

.chat-input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 8px 8px 8px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.04);
}

.chat-input-wrap:focus-within {
  border-color: rgba(34, 211, 238, 0.35);
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.06),
    inset 0 1px 1px rgba(255, 255, 255, 0.06);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.5;
  resize: none;
  min-height: 20px;
  max-height: 100px;
}

.chat-input::placeholder {
  color: var(--text-disabled);
}

.chat-input:disabled {
  opacity: 0.5;
}

.chat-send-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(167, 139, 250, 0.15));
  border: 1px solid rgba(34, 211, 238, 0.2);
  color: var(--color-cube-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.chat-send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.3), rgba(167, 139, 250, 0.2));
  border-color: rgba(34, 211, 238, 0.35);
  transform: scale(1.05);
}

.chat-send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ====== 面板滑入/滑出动画 ====== */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
