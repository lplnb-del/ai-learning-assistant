import { computed, onMounted, readonly, ref, shallowRef, watch } from 'vue'
import { createQaCard, createQaLibrary, listQaLibraries, type QALibraryPayload } from '../api/cards'
import { listKnowledgeBases, type KnowledgeBasePayload } from '../api/knowledge'
import { askRagQuestion } from '../api/rag'
import { useConversationStore } from '../stores/conversations'
import type { RagConversationState, RagViewMessage } from '../types/conversations'

function createEmptyConversationState(): RagConversationState {
  return {
    messages: [],
    selectedKnowledgeBaseIds: [],
    selectedQaLibraryIds: [],
    topK: 3,
  }
}

function buildSessionTitle(messages: RagViewMessage[]) {
  const assistantSummary = messages.find((message) => message.role === 'assistant' && message.content.trim())
  if (assistantSummary) {
    return normalizeSessionLabel(assistantSummary.content, '新建 RAG 对话')
  }

  const firstUserMessage = messages.find((message) => message.role === 'user' && message.content.trim())
  return firstUserMessage ? normalizeSessionLabel(firstUserMessage.content, '新建 RAG 对话') : '新建 RAG 对话'
}

function buildSessionPreview(messages: RagViewMessage[]) {
  const lastMessage = [...messages].reverse().find((message) => message.content.trim())
  return lastMessage ? lastMessage.content.trim().slice(0, 40) : ''
}

export function useRagWorkspace() {
  const conversationStore = useConversationStore()
  const messages = ref<RagViewMessage[]>([])
  const knowledgeBases = ref<KnowledgeBasePayload[]>([])
  const qaLibraries = ref<QALibraryPayload[]>([])

  const selectedKnowledgeBaseIds = ref<string[]>([])
  const selectedQaLibraryIds = ref<string[]>([])
  const input = shallowRef('')
  const topK = shallowRef(3)

  const isLoadingBases = shallowRef(false)
  const isAsking = shallowRef(false)
  const isSavingCard = shallowRef(false)
  const errorMessage = shallowRef('')
  const cardMessage = shallowRef('')

  const activeSaveMessageId = shallowRef('')
  const saveCardLibraryId = shallowRef('')
  const saveCardNewLibraryName = shallowRef('')
  const saveCardNewLibraryDescription = shallowRef('')
  const isQaLibraryPickerOpen = shallowRef(false)
  const activeSessionId = computed(() => conversationStore.activeIds.rag)

  const selectedKnowledgeBases = computed(() =>
    knowledgeBases.value.filter((base) => selectedKnowledgeBaseIds.value.includes(base.id)),
  )
  const selectedQaLibraries = computed(() =>
    qaLibraries.value.filter((library) => selectedQaLibraryIds.value.includes(library.id)),
  )
  const canSubmit = computed(
    () => input.value.trim().length > 0 && selectedKnowledgeBaseIds.value.length > 0 && !isAsking.value,
  )

  onMounted(() => {
    void initialize()
  })

  function hydrateFromSession() {
    const fallbackState = createEmptyConversationState()
    if (!fallbackState.selectedKnowledgeBaseIds.length && knowledgeBases.value.length) {
      fallbackState.selectedKnowledgeBaseIds = [knowledgeBases.value[0].id]
    }

    const ensuredId = conversationStore.ensureSession('rag', {
      mode: 'rag',
      state: fallbackState,
    })
    const session = conversationStore.getSession(ensuredId)
    if (!session || session.payload.mode !== 'rag') {
      return
    }

    messages.value = [...session.payload.state.messages]
    selectedKnowledgeBaseIds.value = session.payload.state.selectedKnowledgeBaseIds.length
      ? [...session.payload.state.selectedKnowledgeBaseIds]
      : knowledgeBases.value[0]
        ? [knowledgeBases.value[0].id]
        : []
    selectedQaLibraryIds.value = [...session.payload.state.selectedQaLibraryIds]
    topK.value = session.payload.state.topK
    input.value = ''
    errorMessage.value = ''
    cardMessage.value = ''
    activeSaveMessageId.value = ''
    isQaLibraryPickerOpen.value = false
  }

  async function initialize() {
    isLoadingBases.value = true
    errorMessage.value = ''
    try {
      knowledgeBases.value = await listKnowledgeBases()
      qaLibraries.value = await listQaLibraries()
      hydrateFromSession()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '读取 RAG 资源失败'
    } finally {
      isLoadingBases.value = false
    }
  }

  watch(activeSessionId, () => {
    if (knowledgeBases.value.length || qaLibraries.value.length) {
      hydrateFromSession()
    }
  })

  watch(
    [messages, selectedKnowledgeBaseIds, selectedQaLibraryIds, topK],
    () => {
      const sessionId = activeSessionId.value
      if (!sessionId) {
        return
      }
      const currentSession = conversationStore.getSession(sessionId)

      conversationStore.updateSession(sessionId, {
        title: currentSession?.titleManuallyEdited ? undefined : buildSessionTitle(messages.value),
        preview: buildSessionPreview(messages.value),
        payload: {
          mode: 'rag',
          state: {
            messages: [...messages.value],
            selectedKnowledgeBaseIds: [...selectedKnowledgeBaseIds.value],
            selectedQaLibraryIds: [...selectedQaLibraryIds.value],
            topK: topK.value,
          },
        },
      })
    },
    { deep: true },
  )

  async function submit() {
    const question = input.value.trim()
    if (!canSubmit.value || !question) {
      return
    }

    errorMessage.value = ''
    cardMessage.value = ''
    input.value = ''
    isAsking.value = true

    const userMessage: RagViewMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
    }
    const assistantMessage: RagViewMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      status: '正在检索知识库和已选问答库',
      question,
      knowledgeBaseIds: [...selectedKnowledgeBaseIds.value],
    }
    messages.value = [...messages.value, userMessage, assistantMessage]

    try {
      const result = await askRagQuestion({
        knowledge_base_ids: [...selectedKnowledgeBaseIds.value],
        qa_library_ids: [...selectedQaLibraryIds.value],
        question,
        top_k: topK.value,
      })
      assistantMessage.content = result.answer
      assistantMessage.status =
        result.sources.length > 0
          ? `命中 ${result.sources.length} 条参考 · ${result.retrieval_mode}`
          : '未命中相关参考'
      assistantMessage.sources = result.sources
      assistantMessage.promptPreview = result.prompt_preview
      messages.value = [...messages.value]
    } catch (error) {
      const message = error instanceof Error ? error.message : 'RAG 问答失败'
      errorMessage.value = message
      assistantMessage.status = '检索失败'
      assistantMessage.content = message
      messages.value = [...messages.value]
    } finally {
      isAsking.value = false
    }
  }

  function toggleQaLibraryPicker() {
    isQaLibraryPickerOpen.value = !isQaLibraryPickerOpen.value
  }

  function toggleKnowledgeBaseSelection(baseId: string) {
    selectedKnowledgeBaseIds.value = selectedKnowledgeBaseIds.value.includes(baseId)
      ? selectedKnowledgeBaseIds.value.filter((item) => item !== baseId)
      : [...selectedKnowledgeBaseIds.value, baseId]
  }

  function toggleQaLibrarySelection(libraryId: string) {
    selectedQaLibraryIds.value = selectedQaLibraryIds.value.includes(libraryId)
      ? selectedQaLibraryIds.value.filter((item) => item !== libraryId)
      : [...selectedQaLibraryIds.value, libraryId]
  }

  function openSavePanel(messageId: string) {
    activeSaveMessageId.value = activeSaveMessageId.value === messageId ? '' : messageId
    if (activeSaveMessageId.value) {
      saveCardLibraryId.value = selectedQaLibraryIds.value[0] ?? qaLibraries.value[0]?.id ?? ''
      saveCardNewLibraryName.value = ''
      saveCardNewLibraryDescription.value = ''
    }
  }

  async function saveAsCard(messageId: string) {
    const message = messages.value.find((item) => item.id === messageId)
    if (!message || message.role !== 'assistant' || !message.question || !message.content.trim()) {
      return
    }

    isSavingCard.value = true
    errorMessage.value = ''
    cardMessage.value = ''
    try {
      let qaLibraryId = saveCardLibraryId.value
      if (!qaLibraryId) {
        const newLibraryName = saveCardNewLibraryName.value.trim()
        if (!newLibraryName) {
          throw new Error('请选择一个问答库，或先新建一个问答库')
        }
        const createdLibrary = await createQaLibrary({
          name: newLibraryName,
          description: saveCardNewLibraryDescription.value.trim(),
        })
        qaLibraries.value = [createdLibrary, ...qaLibraries.value]
        qaLibraryId = createdLibrary.id
      }

      const card = await createQaCard({
        qa_library_id: qaLibraryId,
        question: message.question,
        answer: message.content,
        knowledge_base_id: message.knowledgeBaseIds?.[0] || null,
        source_chunk_ids: message.sources
          ?.filter((source) => source.source_type === 'knowledge_chunk')
          .map((source) => source.chunk_id) ?? [],
        tags: ['RAG'],
      })
      message.savedCardId = card.id
      messages.value = [...messages.value]
      activeSaveMessageId.value = ''
      cardMessage.value = '已保存到问答库'
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '保存卡片失败'
    } finally {
      isSavingCard.value = false
    }
  }

  function startNewConversation() {
    const nextState = createEmptyConversationState()
    if (knowledgeBases.value.length) {
      nextState.selectedKnowledgeBaseIds = [knowledgeBases.value[0].id]
    }
    conversationStore.createSession('rag', {
      mode: 'rag',
      state: nextState,
    })
  }

  return {
    messages: readonly(messages),
    knowledgeBases: readonly(knowledgeBases),
    qaLibraries: readonly(qaLibraries),
    selectedKnowledgeBaseIds,
    toggleKnowledgeBaseSelection,
    selectedQaLibraryIds,
    selectedKnowledgeBases,
    selectedQaLibraries,
    input,
    topK,
    isLoadingBases,
    isAsking,
    isSavingCard,
    errorMessage,
    cardMessage,
    canSubmit,
    activeSaveMessageId,
    saveCardLibraryId,
    saveCardNewLibraryName,
    saveCardNewLibraryDescription,
    isQaLibraryPickerOpen,
    initialize,
    startNewConversation,
    submit,
    toggleQaLibraryPicker,
    toggleQaLibrarySelection,
    openSavePanel,
    saveAsCard,
  }
}

function normalizeSessionLabel(content: string, fallback: string) {
  const normalized = content
    .replace(/[#>*`_-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  return normalized ? normalized.slice(0, 24) : fallback
}
