<script setup lang="ts">
import { X } from '@lucide/vue'

defineProps<{
  title: string
  subtitle?: string
  size?: 'medium' | 'large'
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay-fade">
      <div class="overlay-backdrop" @click.self="emit('close')">
        <section class="overlay-panel" :class="`overlay-panel-${size ?? 'medium'}`">
          <header class="overlay-header">
            <div>
              <h2>{{ title }}</h2>
              <p v-if="subtitle">{{ subtitle }}</p>
            </div>
            <button class="overlay-close-button" type="button" aria-label="关闭面板" @click="emit('close')">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="overlay-body">
            <slot />
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>
