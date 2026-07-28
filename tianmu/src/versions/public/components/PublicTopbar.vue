<template>
  <header class="topbar">
    <div>
      <p class="topbar__date">{{ dateText }}</p>
      <strong>{{ title }}</strong>
    </div>
    <div class="topbar__actions">
      <button
        class="icon-button"
        aria-label="刷新"
        title="刷新数据"
        @click="$emit('refresh')"
        v-html="refreshIcon"
      ></button>
      <button class="icon-button" aria-label="通知" v-html="bellIcon"></button>
      <VersionSwitcher variant="dark" />
      <button class="profile-button" @click="$emit('sign-out')">
        <span>J</span>
        <strong>{{ username || 'User' }}</strong>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import VersionSwitcher from '@/components/VersionSwitcher.vue'

defineProps<{
  dateText: string
  title: string
  username: string
  refreshIcon: string
  bellIcon: string
}>()

defineEmits<{
  refresh: []
  'sign-out': []
}>()
</script>
