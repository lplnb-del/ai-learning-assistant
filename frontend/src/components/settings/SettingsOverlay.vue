<script setup lang="ts">
import FloatingPanel from '../shell/FloatingPanel.vue'
import SettingsView from './SettingsView.vue'

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <FloatingPanel title="偏好设置" subtitle="模型、嵌入和运行偏好在这里统一配置" size="large" @close="emit('close')">
    <SettingsView />
  </FloatingPanel>
</template>
