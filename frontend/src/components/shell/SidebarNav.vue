<script setup lang="ts">
import { GraduationCap, Moon, SlidersHorizontal, Sun } from '@lucide/vue'
import { computed } from 'vue'
import type { MainView, NavItem } from '../../types/workspace'

interface Props {
  items: NavItem[]
  activeView: MainView
  resolvedTheme: 'light' | 'dark'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectView: [view: MainView]
  toggleTheme: []
}>()

const workspaceItems = computed(() => props.items.filter((item) => item.group === 'workspace'))
const resourceItems = computed(() => props.items.filter((item) => item.group === 'resources'))
</script>

<template>
  <aside class="sidebar-shell" aria-label="主导航">
    <div class="sidebar-main">
      <button class="brand-button" type="button" aria-label="返回 AI 学习助理工作台" @click="emit('selectView', 'workspace')">
        <GraduationCap class="brand-icon" :size="24" aria-hidden="true" />
        <span class="brand-title">AI 学习助理</span>
      </button>

      <nav class="nav-section" aria-label="工作区">
        <p class="nav-heading">工作区</p>
        <button
          v-for="item in workspaceItems"
          :key="item.id"
          class="nav-item"
          :class="{ 'nav-item-active': item.id === activeView }"
          type="button"
          @click="emit('selectView', item.id)"
        >
          <component :is="item.icon" :size="18" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <nav class="nav-section" aria-label="资源库">
        <p class="nav-heading">资源库</p>
        <button
          v-for="item in resourceItems"
          :key="item.id"
          class="nav-item"
          :class="{ 'nav-item-active': item.id === activeView }"
          type="button"
          @click="emit('selectView', item.id)"
        >
          <component :is="item.icon" :size="18" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </div>

    <div class="sidebar-footer">
      <div class="footer-actions">
        <button class="nav-item footer-settings" type="button">
          <SlidersHorizontal :size="18" aria-hidden="true" />
          <span>偏好设置</span>
        </button>
        <button class="theme-button" type="button" :aria-label="`切换主题，当前为 ${resolvedTheme}`" @click="emit('toggleTheme')">
          <Sun v-if="resolvedTheme === 'dark'" :size="18" aria-hidden="true" />
          <Moon v-else :size="18" aria-hidden="true" />
        </button>
      </div>
      <div class="service-status">
        <span class="status-dot" aria-hidden="true"></span>
        <span>DeepSeek 在线</span>
      </div>
    </div>
  </aside>
</template>
