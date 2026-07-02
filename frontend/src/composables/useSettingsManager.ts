import { computed, onMounted, ref, shallowRef } from 'vue'
import {
  detectModels,
  getSettings,
  updateChatModel,
  updateEmbeddingModel,
  type DetectedModel,
  type ModelDetectionResponse,
  type ModelProviderConfig,
  type SettingsResponse,
} from '../api/settings'

export function useSettingsManager() {
  const loading = ref(false)
  const saving = ref(false)
  const detecting = ref(false)
  const error = ref<string | null>(null)
  const detectResult = ref<ModelDetectionResponse | null>(null)

  const settings = shallowRef<SettingsResponse | null>(null)

  const chatProvider = ref('deepseek')
  const chatApiKey = ref('')
  const chatBaseUrl = ref('')
  const chatModel = ref('')

  const embeddingProvider = ref('deepseek')
  const embeddingApiKey = ref('')
  const embeddingBaseUrl = ref('')
  const embeddingModel = ref('')

  const detectedModels = ref<DetectedModel[]>([])

  async function loadSettings() {
    loading.value = true
    error.value = null
    try {
      const data = await getSettings()
      settings.value = data
      chatProvider.value = data.chat_provider
      chatModel.value = data.chat_model ?? ''
      chatBaseUrl.value = data.chat_base_url ?? ''
      embeddingProvider.value = data.embedding_provider
      embeddingModel.value = data.embedding_model ?? ''
      embeddingBaseUrl.value = data.embedding_base_url ?? ''
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
        api_key: chatApiKey.value || undefined,
        base_url: chatBaseUrl.value || undefined,
        model: chatModel.value || undefined,
      }
      const data = await updateChatModel(config)
      settings.value = data
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
        api_key: embeddingApiKey.value || undefined,
        base_url: embeddingBaseUrl.value || undefined,
        model: embeddingModel.value || undefined,
      }
      const data = await updateEmbeddingModel(config)
      settings.value = data
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
    try {
      const provider = target === 'chat' ? chatProvider.value : embeddingProvider.value
      const apiKey = target === 'chat' ? chatApiKey.value : embeddingApiKey.value
      const baseUrl = target === 'chat' ? chatBaseUrl.value : embeddingBaseUrl.value
      const result = await detectModels(provider, apiKey || undefined, baseUrl || undefined)
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

  const chatProviderLabel = computed(() => {
    const map: Record<string, string> = { deepseek: 'DeepSeek', openai: 'OpenAI', ollama: 'Ollama (本地)' }
    return map[chatProvider.value] ?? chatProvider.value
  })

  const embeddingProviderLabel = computed(() => {
    const map: Record<string, string> = { deepseek: 'DeepSeek', openai: 'OpenAI', ollama: 'Ollama (本地)' }
    return map[embeddingProvider.value] ?? embeddingProvider.value
  })

  return {
    loading,
    saving,
    detecting,
    error,
    settings,
    chatProvider,
    chatApiKey,
    chatBaseUrl,
    chatModel,
    embeddingProvider,
    embeddingApiKey,
    embeddingBaseUrl,
    embeddingModel,
    detectedModels,
    detectResult,
    chatProviderLabel,
    embeddingProviderLabel,
    loadSettings,
    saveChatConfig,
    saveEmbeddingConfig,
    runDetection,
    selectDetectedModel,
  }
}
