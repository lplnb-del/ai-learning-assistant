import { computed, onMounted, ref, shallowRef } from 'vue'
import {
  deleteSkillSetting,
  deleteMcpServer,
  deleteSubagent,
  detectModels,
  generateSubagentPrompt,
  getPresets,
  getSettings,
  listMcpServers,
  listSkillSettings,
  listSubagents,
  saveMcpServer,
  saveSkillSetting,
  saveSubagent,
  updateChatModel,
  updateEmbeddingModel,
  updateSkillSetting,
  type DetectedModel,
  type McpServerConfig,
  type ModelDetectionResponse,
  type ModelProviderConfig,
  type PresetInfo,
  type SettingsResponse,
  type SkillConfigResponse,
  type SubAgentRoleConfig,
} from '../api/settings'
import { useModelSettingsStore } from '../stores/modelSettings'

export type ProviderType = 'openai_compatible' | 'ollama' | 'huggingface'
export type SettingsSection = 'models' | 'subagents' | 'mcp' | 'skills'

const PROVIDER_OPTIONS: { value: ProviderType; label: string; desc: string }[] = [
  { value: 'openai_compatible', label: 'OpenAI 兼容协议', desc: '支持 DeepSeek / OpenAI / Moonshot / Qwen / Groq / 自部署等' },
  { value: 'ollama', label: 'Ollama (本地)', desc: '本地运行的 Ollama 模型服务' },
]

const EMBEDDING_PROVIDER_OPTIONS: { value: ProviderType; label: string; desc: string }[] = [
  { value: 'openai_compatible', label: 'OpenAI 兼容协议', desc: '云端嵌入 API（DeepSeek / OpenAI / Qwen 等）' },
  { value: 'ollama', label: 'Ollama (本地)', desc: '本地 Ollama 嵌入模型' },
  { value: 'huggingface', label: 'HuggingFace (本地)', desc: '本地 sentence-transformers，首次使用自动下载' },
]

const SETTINGS_SECTIONS: { id: SettingsSection; label: string; description: string }[] = [
  { id: 'models', label: '模型配置', description: '聊天与嵌入模型' },
  { id: 'subagents', label: 'Subagent配置', description: '角色与提示词' },
  { id: 'mcp', label: 'MCP配置', description: '外部工具服务' },
  { id: 'skills', label: 'Skills配置', description: '工作台技能目录' },
]

export function useSettingsManager() {
  const modelSettingsStore = useModelSettingsStore()
  const loading = ref(false)
  const saving = ref(false)
  const detecting = ref(false)
  const generatingPrompt = ref(false)
  const error = ref<string | null>(null)
  const detectResult = ref<ModelDetectionResponse | null>(null)
  const activeSection = shallowRef<SettingsSection>('models')

  const settings = shallowRef<SettingsResponse | null>(null)
  const presets = ref<PresetInfo[]>([])

  const chatProvider = ref<ProviderType>('openai_compatible')
  const chatPreset = ref('')
  const chatApiKey = ref('')
  const chatBaseUrl = ref('')
  const chatModel = ref('')

  const embeddingProvider = ref<ProviderType>('openai_compatible')
  const embeddingPreset = ref('')
  const embeddingApiKey = ref('')
  const embeddingBaseUrl = ref('')
  const embeddingModel = ref('')
  const detectedModels = ref<DetectedModel[]>([])

  const subagents = ref<SubAgentRoleConfig[]>([])
  const selectedSubagentId = shallowRef('')
  const isSubagentModalOpen = shallowRef(false)
  const subagentName = ref('')
  const subagentTitle = ref('')
  const subagentDescription = ref('')
  const subagentPrompt = ref('')
  const subagentGreeting = ref('')
  const subagentTags = ref('')
  const subagentMission = ref('')

  const mcpServers = ref<McpServerConfig[]>([])
  const editingMcpId = shallowRef('')
  const isMcpModalOpen = shallowRef(false)
  const mcpName = ref('')
  const mcpDescription = ref('')
  const mcpCommand = ref('')
  const mcpEnabled = ref(false)

  const skillSettings = ref<SkillConfigResponse[]>([])
  const selectedSkillId = shallowRef('')
  const isSkillModalOpen = shallowRef(false)
  const skillName = ref('')
  const skillDescription = ref('')
  const skillTags = ref('')
  const skillSource = ref('custom')
  const skillEnabled = ref(true)

  const chatPresetOptions = computed(() => presets.value.filter((preset) => preset.default_chat_model))
  const embeddingPresetOptions = computed(() => presets.value.filter((preset) => preset.default_embedding_model || preset.key === 'custom'))
  const currentChatPreset = computed(() => presets.value.find((preset) => preset.key === chatPreset.value))
  const currentEmbeddingPreset = computed(() => presets.value.find((preset) => preset.key === embeddingPreset.value))
  const selectedSubagent = computed(() => subagents.value.find((item) => item.id === selectedSubagentId.value) ?? null)
  const selectedMcp = computed(() => mcpServers.value.find((item) => item.id === editingMcpId.value) ?? null)
  const selectedSkill = computed(() => skillSettings.value.find((item) => item.id === selectedSkillId.value) ?? null)
  const enabledMcpCount = computed(() => mcpServers.value.filter((item) => item.enabled).length)
  const enabledSkillsCount = computed(() => skillSettings.value.filter((item) => item.enabled).length)

  function selectSection(section: SettingsSection) {
    activeSection.value = section
  }

  function applyChatPreset(presetKey: string) {
    chatPreset.value = presetKey
    const preset = presets.value.find((item) => item.key === presetKey)
    if (preset) {
      chatBaseUrl.value = preset.base_url
      if (preset.default_chat_model && !chatModel.value) {
        chatModel.value = preset.default_chat_model
      }
    }
  }

  function applyEmbeddingPreset(presetKey: string) {
    embeddingPreset.value = presetKey
    const preset = presets.value.find((item) => item.key === presetKey)
    if (preset) {
      embeddingBaseUrl.value = preset.base_url
      if (preset.default_embedding_model && !embeddingModel.value) {
        embeddingModel.value = preset.default_embedding_model
      }
    }
  }

  function hydrateModelSettings(data: SettingsResponse, presetsData: PresetInfo[]) {
    settings.value = data
    presets.value = presetsData
    modelSettingsStore.updateSettings(data)
    modelSettingsStore.updatePresets(presetsData)

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
  }

  function resetSubagentEditor(role?: SubAgentRoleConfig | null) {
    selectedSubagentId.value = role?.id ?? ''
    subagentName.value = role?.name ?? ''
    subagentTitle.value = role?.title ?? ''
    subagentDescription.value = role?.description ?? ''
    subagentPrompt.value = role?.system_prompt ?? ''
    subagentGreeting.value = role?.greeting ?? ''
    subagentTags.value = role?.tags.join(', ') ?? ''
    subagentMission.value = role?.description ?? ''
  }

  function selectSubagent(roleId: string) {
    const role = subagents.value.find((item) => item.id === roleId) ?? null
    selectedSubagentId.value = role?.id ?? ''
  }

  function openCreateSubagent() {
    resetSubagentEditor(null)
    isSubagentModalOpen.value = true
  }

  function openEditSubagent(roleId: string) {
    const role = subagents.value.find((item) => item.id === roleId) ?? null
    resetSubagentEditor(role)
    isSubagentModalOpen.value = true
  }

  function closeSubagentModal() {
    isSubagentModalOpen.value = false
  }

  function editMcpServer(server?: McpServerConfig | null) {
    editingMcpId.value = server?.id ?? ''
    mcpName.value = server?.name ?? ''
    mcpDescription.value = server?.description ?? ''
    mcpCommand.value = server?.command ?? ''
    mcpEnabled.value = server?.enabled ?? false
  }

  function openCreateMcp() {
    editMcpServer(null)
    isMcpModalOpen.value = true
  }

  function openEditMcp(serverId: string) {
    const server = mcpServers.value.find((item) => item.id === serverId) ?? null
    editMcpServer(server)
    isMcpModalOpen.value = true
  }

  function closeMcpModal() {
    isMcpModalOpen.value = false
  }

  function editSkill(skill?: SkillConfigResponse | null) {
    selectedSkillId.value = skill?.id ?? ''
    skillName.value = skill?.name ?? ''
    skillDescription.value = skill?.description ?? ''
    skillTags.value = skill?.tags.join(', ') ?? ''
    skillSource.value = skill?.source ?? 'custom'
    skillEnabled.value = skill?.enabled ?? true
  }

  function selectSkill(skillId: string) {
    selectedSkillId.value = skillId
  }

  function openCreateSkill() {
    editSkill(null)
    isSkillModalOpen.value = true
  }

  function openEditSkill(skillId: string) {
    const skill = skillSettings.value.find((item) => item.id === skillId) ?? null
    editSkill(skill)
    isSkillModalOpen.value = true
  }

  function closeSkillModal() {
    isSkillModalOpen.value = false
  }

  async function loadSettings() {
    loading.value = true
    error.value = null
    try {
      const [modelData, presetsData, roleData, mcpData, skillData] = await Promise.all([
        getSettings(),
        getPresets(),
        listSubagents(),
        listMcpServers(),
        listSkillSettings(),
      ])

      hydrateModelSettings(modelData, presetsData.presets)
      subagents.value = roleData
      mcpServers.value = mcpData
      skillSettings.value = skillData
      if (!selectedSubagentId.value && roleData.length) {
        selectedSubagentId.value = roleData[0].id
      }
      if (!editingMcpId.value && mcpData.length) {
        editingMcpId.value = mcpData[0].id
      }
      if (!selectedSkillId.value && skillData.length) {
        selectedSkillId.value = skillData[0].id
      }
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
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
      modelSettingsStore.updateSettings(settings.value)
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
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
      modelSettingsStore.updateSettings(settings.value)
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
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
      modelSettingsStore.setDetectedModels(target, result.models)
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      detecting.value = false
    }
  }

  function selectDetectedModel(target: 'chat' | 'embedding', modelId: string) {
    if (target === 'chat') {
      chatModel.value = modelId
      return
    }
    embeddingModel.value = modelId
  }

  async function saveCurrentSubagent() {
    saving.value = true
    error.value = null
    try {
      const saved = await saveSubagent({
        id: selectedSubagentId.value || undefined,
        name: subagentName.value.trim(),
        title: subagentTitle.value.trim() || subagentName.value.trim(),
        description: subagentDescription.value.trim(),
        system_prompt: subagentPrompt.value.trim(),
        greeting: subagentGreeting.value.trim(),
        preferred_skills: selectedSubagent.value?.preferred_skills ?? [],
        tags: subagentTags.value.split(',').map((item) => item.trim()).filter(Boolean),
      })
      const existingIndex = subagents.value.findIndex((item) => item.id === saved.id)
      if (existingIndex >= 0) {
        subagents.value.splice(existingIndex, 1, saved)
      } else {
        subagents.value.unshift(saved)
      }
      selectedSubagentId.value = saved.id
      closeSubagentModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  async function removeCurrentSubagent() {
    if (!selectedSubagentId.value) {
      return
    }
    saving.value = true
    error.value = null
    try {
      await deleteSubagent(selectedSubagentId.value)
      subagents.value = subagents.value.filter((item) => item.id !== selectedSubagentId.value)
      selectedSubagentId.value = subagents.value[0]?.id ?? ''
      closeSubagentModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  async function autoGenerateSubagentPrompt() {
    generatingPrompt.value = true
    error.value = null
    try {
      const result = await generateSubagentPrompt(subagentName.value.trim(), subagentMission.value.trim() || subagentDescription.value.trim())
      subagentPrompt.value = result.system_prompt
      if (!subagentGreeting.value.trim()) {
        subagentGreeting.value = result.greeting
      }
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      generatingPrompt.value = false
    }
  }

  async function saveCurrentMcp() {
    saving.value = true
    error.value = null
    try {
      const saved = await saveMcpServer({
        id: editingMcpId.value || undefined,
        name: mcpName.value.trim(),
        description: mcpDescription.value.trim(),
        command: mcpCommand.value.trim(),
        enabled: mcpEnabled.value,
      })
      const existingIndex = mcpServers.value.findIndex((item) => item.id === saved.id)
      if (existingIndex >= 0) {
        mcpServers.value.splice(existingIndex, 1, saved)
      } else {
        mcpServers.value.unshift(saved)
      }
      editingMcpId.value = saved.id
      closeMcpModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  async function removeMcpServer(serverId: string) {
    saving.value = true
    error.value = null
    try {
      await deleteMcpServer(serverId)
      mcpServers.value = mcpServers.value.filter((item) => item.id !== serverId)
      if (editingMcpId.value === serverId) {
        editingMcpId.value = mcpServers.value[0]?.id ?? ''
      }
      closeMcpModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  async function toggleSkill(skillId: string, enabled: boolean) {
    error.value = null
    try {
      const updated = await updateSkillSetting(skillId, enabled)
      const existingIndex = skillSettings.value.findIndex((item) => item.id === skillId)
      if (existingIndex >= 0) {
        skillSettings.value.splice(existingIndex, 1, updated)
      }
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    }
  }

  async function saveCurrentSkill() {
    saving.value = true
    error.value = null
    try {
      const saved = await saveSkillSetting({
        id: selectedSkillId.value || undefined,
        name: skillName.value.trim(),
        description: skillDescription.value.trim(),
        enabled: skillEnabled.value,
        tags: skillTags.value.split(',').map((item) => item.trim()).filter(Boolean),
        source: skillSource.value.trim() || 'custom',
      })
      const existingIndex = skillSettings.value.findIndex((item) => item.id === saved.id)
      if (existingIndex >= 0) {
        skillSettings.value.splice(existingIndex, 1, saved)
      } else {
        skillSettings.value.unshift(saved)
      }
      selectedSkillId.value = saved.id
      closeSkillModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  async function removeCurrentSkill() {
    if (!selectedSkillId.value) {
      return
    }
    saving.value = true
    error.value = null
    try {
      await deleteSkillSetting(selectedSkillId.value)
      skillSettings.value = skillSettings.value.filter((item) => item.id !== selectedSkillId.value)
      selectedSkillId.value = skillSettings.value[0]?.id ?? ''
      closeSkillModal()
    } catch (unknownError: unknown) {
      error.value = unknownError instanceof Error ? unknownError.message : String(unknownError)
    } finally {
      saving.value = false
    }
  }

  onMounted(loadSettings)

  return {
    loading,
    saving,
    detecting,
    generatingPrompt,
    error,
    detectResult,
    activeSection,
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
    chatPresetOptions,
    embeddingPresetOptions,
    currentChatPreset,
    currentEmbeddingPreset,
    subagents,
    selectedSubagentId,
    selectedSubagent,
    isSubagentModalOpen,
    subagentName,
    subagentTitle,
    subagentDescription,
    subagentPrompt,
    subagentGreeting,
    subagentTags,
    subagentMission,
    mcpServers,
    editingMcpId,
    selectedMcp,
    isMcpModalOpen,
    mcpName,
    mcpDescription,
    mcpCommand,
    mcpEnabled,
    skillSettings,
    selectedSkillId,
    selectedSkill,
    isSkillModalOpen,
    skillName,
    skillDescription,
    skillTags,
    skillSource,
    skillEnabled,
    enabledMcpCount,
    enabledSkillsCount,
    SETTINGS_SECTIONS,
    PROVIDER_OPTIONS,
    EMBEDDING_PROVIDER_OPTIONS,
    selectSection,
    applyChatPreset,
    applyEmbeddingPreset,
    loadSettings,
    saveChatConfig,
    saveEmbeddingConfig,
    runDetection,
    selectDetectedModel,
    selectSubagent,
    openCreateSubagent,
    openEditSubagent,
    closeSubagentModal,
    saveCurrentSubagent,
    removeCurrentSubagent,
    autoGenerateSubagentPrompt,
    editMcpServer,
    openCreateMcp,
    openEditMcp,
    closeMcpModal,
    saveCurrentMcp,
    removeMcpServer,
    selectSkill,
    openCreateSkill,
    openEditSkill,
    closeSkillModal,
    toggleSkill,
    saveCurrentSkill,
    removeCurrentSkill,
  }
}
