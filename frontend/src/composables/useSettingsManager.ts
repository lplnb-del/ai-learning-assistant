import { computed, onMounted, ref, shallowRef } from 'vue'
import {
  detectModels,
  getPresets,
  getSettings,
  updateChatModel,
  updateEmbeddingModel,
  type DetectedModel,
  type ModelDetectionResponse,
  type ModelProviderConfig,
  type PresetInfo,
  type SettingsResponse,
} from '../api/settings'

export type ProviderType = 'openai_compatible' | 'ollama' | 'huggingface'

const PROVIDER_OPTIONS: { value: ProviderType; label: string; desc: string }[] = [
  { value: 'openai_compatible', label: 'OpenAI 兼容协议', desc: '支持 DeepSeek / OpenAI / Moonshot / Qwen / Groq / 自部署等' },
  { value: 'ollama', label: 'Ollama (本地)', desc: '本地运行的 Ollama 模型服务' },
]

const EMBEDDING_PROVIDER_OPTIONS: { value: ProviderType; label: string; desc: string }[] = [
  { value: 'openai_compatible', label: 'OpenAI 兼容协议', desc: '云端嵌入 API（DeepSeek / OpenAI / Qwen 等）' },
  { value: 'ollama', label: 'Ollama (本地)', desc: '本地 Ollama 嵌入模型' },
  { value: 'huggingface', label: 'HuggingFace (本地)', desc: '本地 sentence-transformers，首次使用自动下载' },
]

export function useSettingsManager() {
  const loading = ref(false)
  const saving = ref(false)
  const detecting = ref(false)
  const error = ref<string | null>(null)
  const detectResult = ref<ModelDetectionResponse | null>(null)

  const settings = shallowRef<SettingsResponse | null>(null)
  const presets = ref<PresetInfo[]>([])

  // Chat config
  const chatProvider = ref<ProviderType>('openai_compatible')
  const chatPreset = ref('')
  const chatApiKey = ref('')
  const chatBaseUrl = ref('')
  const chatModel = ref('')

  // Embedding config
  const embeddingProvider = ref<ProviderType>('openai_compatible')
  const embeddingPreset = ref('')
  const embeddingApiKey = ref('')
  const embeddingBaseUrl = ref('')
  const embeddingModel = ref('')

  const detectedModels = ref<DetectedModel[]>([])

  const chatPresetOptions = computed(() =>
    presets.value.filter((p) => p.default_chat_model),
  )

  const embeddingPresetOptions = computed(() =>
    presets.value.filter((p) => p.default_embedding_model || p.key === 'custom'),
  )

  const currentChatPreset = computed(() =>
    presets.value.find((p) => p.key === chatPreset.value),
  )

  const currentEmbeddingPreset = computed(() =>
    presets.value.find((p) => p.key === embeddingPreset.value),
  )

  function applyChatPreset(presetKey: string) {
    chatPreset.value = presetKey
    const p = presets.value.find((x) => x.key === presetKey)
    if (p) {
      chatBaseUrl.value = p.base_url
      if (p.default_chat_model && !chatModel.value) {
        chatModel.value = p.default_chat_model
      }
    }
  }

  function applyEmbeddingPreset(presetKey: string) {
    embeddingPreset.value = presetKey
    const p = presets.value.find((x) => x.key === presetKey)
    if (p) {
      embeddingBaseUrl.value = p.base_url
      if (p.default_embedding_model && !embeddingModel.value) {
        embeddingModel.value = p.default_embedding_model
      }
    }
  }

  async function loadSettings() {
    loading.value = true
    error.value = null
    try {
      const [data, presetsData] = await Promise.all([getSettings(), getPresets()])
      settings.value = data
      presets.value = presetsData.presets

      chatProvider.value = (data.chat_provider as ProviderType) || 'openai_compatible'
      chatPreset.value = data.chat_preset ?? ''
      chatModel.value = data.chat_model ?? ''
      chatBaseUrl.value = data.chat_base_url ?? ''
      chatApiKey.value = ''

      embeddingProvider.value = (data.embedding_provider as ProviderType) || 'openai_compatible'
      embeddingPreset.value = data.embedding_preset ?? ''
      embeddingModel.value = data.embedding_model ?? ''
      embeddingBaseUrl.value = data.embedding_base_url ?? ''
      embeddingApiKey.value = ''
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      loading.value = false
    }
  }

  async function saveChatConfig() {
    saving.value = true
    error.value = null
    try {
      const config: ModelProviderConfig = {
        provider: chatProvider.value,
        preset: chatPreset.value || undefined,
        api_key: chatApiKey.value || undefined,
        base_url: chatBaseUrl.value || undefined,
        model: chatModel.value || undefined,
      }
      settings.value = await updateChatModel(config)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  async function saveEmbeddingConfig() {
    saving.value = true
    error.value = null
    try {
      const config: ModelProviderConfig = {
        provider: embeddingProvider.value,
        preset: embeddingPreset.value || undefined,
        api_key: embeddingApiKey.value || undefined,
        base_url: embeddingBaseUrl.value || undefined,
        model: embeddingModel.value || undefined,
      }
      settings.value = await updateEmbeddingModel(config)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      saving.value = false
    }
  }

  async function runDetection(target: 'chat' | 'embedding') {
    detecting.value = true
    detectResult.value = null
    error.value = null
    detectedModels.value = []
    try {
      const provider = target === 'chat' ? chatProvider.value : embeddingProvider.value
      const apiKey = target === 'chat' ? chatApiKey.value : embeddingApiKey.value
      const baseUrl = target === 'chat' ? chatBaseUrl.value : embeddingBaseUrl.value
      const preset = target === 'chat' ? chatPreset.value : embeddingPreset.value
      const result = await detectModels(provider, apiKey || undefined, baseUrl || undefined, preset || undefined)
      detectResult.value = result
      detectedModels.value = result.models
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : String(e)
    } finally {
      detecting.value = false
    }
  }

  function selectDetectedModel(target: 'chat' | 'embedding', modelId: string) {
    if (target === 'chat') {
      chatModel.value = modelId
    } else {
      embeddingModel.value = modelId
    }
  }

  onMounted(loadSettings)

  return {
    loading,
    saving,
    detecting,
    error,
    settings,
    presets,
    chatProvider,
    chatPreset,
    chatApiKey,
    chatBaseUrl,
    chatModel,
    embeddingProvider,
    embeddingPreset,
    embeddingApiKey,
    embeddingBaseUrl,
    embeddingModel,
    detectedModels,
    detectResult,
    chatPresetOptions,
    embeddingPresetOptions,
    currentChatPreset,
    currentEmbeddingPreset,
    loadSettings,
    saveChatConfig,
    saveEmbeddingConfig,
    runDetection,
    selectDetectedModel,
    applyChatPreset,
    applyEmbeddingPreset,
    PROVIDER_OPTIONS,
    EMBEDDING_PROVIDER_OPTIONS,
  }
}