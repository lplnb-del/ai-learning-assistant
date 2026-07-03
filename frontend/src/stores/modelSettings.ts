import { computed, ref, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import { getPresets, getSettings, type DetectedModel, type PresetInfo, type SettingsResponse } from '../api/settings'

const DETECTED_MODELS_KEY = 'ai-study-agent.detected-models.v1'

interface CachedDetectedModels {
  chat: DetectedModel[]
  embedding: DetectedModel[]
}

function loadDetectedModels(): CachedDetectedModels {
  if (typeof window === 'undefined') {
    return { chat: [], embedding: [] }
  }

  try {
    const raw = window.localStorage.getItem(DETECTED_MODELS_KEY)
    if (!raw) {
      return { chat: [], embedding: [] }
    }

    const parsed = JSON.parse(raw) as Partial<CachedDetectedModels>
    return {
      chat: Array.isArray(parsed.chat) ? parsed.chat : [],
      embedding: Array.isArray(parsed.embedding) ? parsed.embedding : [],
    }
  } catch {
    return { chat: [], embedding: [] }
  }
}

function persistDetectedModels(value: CachedDetectedModels) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(DETECTED_MODELS_KEY, JSON.stringify(value))
}

function buildModelOptions(models: DetectedModel[], currentModel?: string | null, presetModel?: string) {
  const optionMap = new Map<string, { value: string; label: string }>()

  for (const model of models) {
    optionMap.set(model.id, { value: model.id, label: model.name || model.id })
  }

  if (currentModel) {
    optionMap.set(currentModel, { value: currentModel, label: currentModel })
  }

  if (presetModel) {
    optionMap.set(presetModel, { value: presetModel, label: presetModel })
  }

  return [...optionMap.values()]
}

export const useModelSettingsStore = defineStore('model-settings', () => {
  const loading = shallowRef(false)
  const loaded = shallowRef(false)
  const settings = shallowRef<SettingsResponse | null>(null)
  const presets = ref<PresetInfo[]>([])
  const detectedModels = ref<CachedDetectedModels>(loadDetectedModels())

  const currentChatPreset = computed(
    () => presets.value.find((preset) => preset.key === settings.value?.chat_preset) ?? null,
  )

  const currentEmbeddingPreset = computed(
    () => presets.value.find((preset) => preset.key === settings.value?.embedding_preset) ?? null,
  )

  const chatModelOptions = computed(() =>
    buildModelOptions(
      detectedModels.value.chat,
      settings.value?.chat_model,
      currentChatPreset.value?.default_chat_model,
    ),
  )

  const embeddingModelOptions = computed(() =>
    buildModelOptions(
      detectedModels.value.embedding,
      settings.value?.embedding_model,
      currentEmbeddingPreset.value?.default_embedding_model,
    ),
  )

  const defaultChatModel = computed(
    () => settings.value?.chat_model || currentChatPreset.value?.default_chat_model || chatModelOptions.value[0]?.value || '',
  )

  async function loadRemoteSettings(force = false) {
    if (loading.value || (loaded.value && !force)) {
      return
    }

    loading.value = true
    try {
      const [nextSettings, nextPresets] = await Promise.all([getSettings(), getPresets()])
      settings.value = nextSettings
      presets.value = nextPresets.presets
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  function updateSettings(nextSettings: SettingsResponse) {
    settings.value = nextSettings
    loaded.value = true
  }

  function updatePresets(nextPresets: PresetInfo[]) {
    presets.value = nextPresets
  }

  function setDetectedModels(target: 'chat' | 'embedding', models: DetectedModel[]) {
    detectedModels.value = {
      ...detectedModels.value,
      [target]: models,
    }
    persistDetectedModels(detectedModels.value)
  }

  return {
    loading,
    loaded,
    settings,
    presets,
    currentChatPreset,
    currentEmbeddingPreset,
    chatModelOptions,
    embeddingModelOptions,
    defaultChatModel,
    loadRemoteSettings,
    updateSettings,
    updatePresets,
    setDetectedModels,
  }
})
