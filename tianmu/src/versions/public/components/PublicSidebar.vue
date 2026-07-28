<template>
  <aside class="sidebar">
    <div class="brand">
      <img src="/tmzc-logo.svg" alt="" class="brand__mark" />
      <span>智能魔方</span>
    </div>

    <nav class="nav-list" aria-label="主导航">
      <button
        v-for="item in items"
        :key="item.id"
        class="nav-item"
        :class="{ 'nav-item--active': activeView === item.id }"
        @click="$emit('select', item.id)"
      >
        <span class="nav-item__icon" v-html="item.icon"></span>
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </aside>
</template>

<script setup lang="ts">
defineProps<{
  items: ReadonlyArray<{ id: string; label: string; icon: string }>
  activeView: string
}>()

defineEmits<{
  select: [view: string]
}>()
</script>
