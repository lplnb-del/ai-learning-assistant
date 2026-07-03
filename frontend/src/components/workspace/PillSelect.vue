<script setup lang="ts">
import { Check, ChevronDown } from '@lucide/vue'
import { computed, onMounted, onUnmounted, shallowRef, useTemplateRef } from 'vue'

interface PillSelectOption {
  value: string
  label: string
}

interface Props {
  label: string
  options: PillSelectOption[]
  placeholder?: string
  disabled?: boolean
  variant?: 'toolbar' | 'field'
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '请选择',
  disabled: false,
  variant: 'toolbar',
})

const model = defineModel<string>({ required: true })
const isOpen = shallowRef(false)
const rootRef = useTemplateRef('root')

const selectedOption = computed(
  () => props.options.find((option) => option.value === model.value) ?? null,
)

const displayLabel = computed(() => selectedOption.value?.label ?? props.placeholder)

function toggleOpen() {
  if (props.disabled || props.options.length === 0) {
    return
  }
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function selectOption(value: string) {
  model.value = value
  close()
}

function handleDocumentPointerDown(event: Event) {
  if (!isOpen.value) {
    return
  }

  const rootElement = rootRef.value
  if (!(event.target instanceof globalThis.Node) || !rootElement || rootElement.contains(event.target)) {
    return
  }

  close()
}

function handleTriggerKeydown(event: Event) {
  if (!(event instanceof globalThis.KeyboardEvent)) {
    return
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleOpen()
  }

  if (event.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})
</script>

<template>
  <div
    ref="root"
    class="pill-select"
    :class="[`pill-select-${variant}`, { 'pill-select-open': isOpen, 'pill-select-disabled': disabled }]"
  >
    <button
      class="pill-select-trigger"
      type="button"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      :aria-label="label"
      :disabled="disabled"
      @click="toggleOpen"
      @keydown="handleTriggerKeydown"
    >
      <span class="pill-select-label">{{ displayLabel }}</span>
      <ChevronDown class="pill-select-chevron" :size="14" aria-hidden="true" />
    </button>

    <Transition name="pill-select-popup">
      <div v-if="isOpen" class="pill-select-menu" role="listbox" :aria-label="label">
        <button
          v-for="option in options"
          :key="option.value"
          class="pill-select-option"
          :class="{ 'pill-select-option-active': option.value === model }"
          type="button"
          role="option"
          :aria-selected="option.value === model"
          @click="selectOption(option.value)"
        >
          <span>{{ option.label }}</span>
          <Check v-if="option.value === model" :size="14" aria-hidden="true" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.pill-select {
  position: relative;
  min-width: 0;
}

.pill-select-trigger {
  display: inline-flex;
  min-width: 120px;
  max-width: min(240px, 46vw);
  min-height: 26px;
  align-items: center;
  gap: 10px;
  border: 0;
  padding: 0;
  background: transparent;
  color: inherit;
  transition:
    color var(--motion-micro) var(--ease-standard),
    transform var(--motion-micro) var(--ease-standard);
}

.pill-select-field {
  width: 100%;
}

.pill-select-field .pill-select-trigger {
  width: 100%;
  max-width: none;
  min-height: 42px;
  justify-content: space-between;
  border: 1px solid var(--color-border-soft);
  border-radius: 14px;
  padding: 0 14px;
  background: color-mix(in srgb, var(--color-input-bg) 92%, transparent);
  color: var(--color-text-primary);
  box-shadow: inset 0 1px 0 color-mix(in srgb, #ffffff 4%, transparent);
}

.pill-select-field.pill-select-open .pill-select-trigger,
.pill-select-field .pill-select-trigger:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--color-accent-text) 24%, transparent);
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-accent-text) 8%, transparent);
}

.pill-select-label {
  overflow: hidden;
  min-width: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pill-select-chevron {
  flex: 0 0 auto;
  color: var(--color-text-tertiary);
  transition:
    color var(--motion-micro) var(--ease-standard),
    transform var(--motion-micro) var(--ease-standard);
}

.pill-select-open .pill-select-trigger,
.pill-select-trigger:hover:not(:disabled) {
  color: var(--color-text-primary);
}

.pill-select-open .pill-select-chevron {
  color: var(--color-accent-text);
  transform: rotate(180deg);
}

.pill-select-disabled {
  opacity: 0.6;
}

.pill-select-menu {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  z-index: 40;
  display: grid;
  min-width: max(100%, 212px);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--color-accent-text) 16%, var(--color-border-soft));
  border-radius: 14px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.16);
  backdrop-filter: blur(18px);
}

.pill-select-field .pill-select-menu {
  top: calc(100% + 8px);
  right: 0;
  min-width: 100%;
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-surface-elevated, var(--color-surface)) 96%, transparent);
}

.pill-select-option {
  display: flex;
  min-height: 38px;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 0;
  padding: 0 12px;
  background: transparent;
  color: var(--color-text-secondary);
  text-align: left;
  transition:
    background-color var(--motion-micro) var(--ease-standard),
    color var(--motion-micro) var(--ease-standard),
    transform var(--motion-micro) var(--ease-standard);
}

.pill-select-option span {
  white-space: nowrap;
}

.pill-select-option:hover {
  background: color-mix(in srgb, var(--color-accent-bg) 72%, transparent);
  color: var(--color-text-primary);
}

.pill-select-option-active {
  background: color-mix(in srgb, var(--color-accent-bg) 88%, transparent);
  color: var(--color-accent-text);
}

.pill-select-popup-enter-active,
.pill-select-popup-leave-active {
  transition:
    opacity var(--motion-micro) var(--ease-standard),
    transform var(--motion-micro) var(--ease-standard);
}

.pill-select-popup-enter-from,
.pill-select-popup-leave-to {
  transform: translateY(-6px) scale(0.98);
  opacity: 0;
}
</style>
