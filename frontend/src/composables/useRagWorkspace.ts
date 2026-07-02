import { computed, onMounted, readonly, ref, shallowRef } from 'vue'
import { createQaCard, createQaLibrary, listQaLibraries, type QALibraryPayload } from '../api/cards'
import { listKnowledgeBases, type KnowledgeBasePayload } from '../api/knowledge'
import { askRagQuestion, type RagSourcePayload } from '../api/rag'

export interface RagViewMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: string
  sources?: readonly RagSourcePayload[]
  promptPreview?: string
  question?: string
  knowledgeBaseIds?: string[]
  savedCardId?: string
}

const initialMessages: RagViewMessage[] = [
  {
    id: 'sample-user',
    role: 'user',
    content: '基于资料，RAG 是怎么回答问题的？',
  },
  {
    id: 'sample-assistant',
    role: 'assistant',
    status: '本地 RAG 已就绪，可选择知识库和问答库后提问',
    content:
      'RAG 会先从知识库检索相关 chunks，也可以补充匹配问答库里的已有答案表达，再把问题和参考资料组装成 prompt。',
  },
]

const demoQuestions = [
  'RAG 是怎么回答问题的？',
  '根据资料总结 3 个适合面试的要点。',
  '当前知识库里有哪些核心概念？',
]

export function useRagWorkspace() {
  const messages = ref<RagViewMessage[]>([...initialMessages])
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

  async function initialize() {
    isLoadingBases.value = true
    errorMessage.value = ''
    try {
      knowledgeBases.value = await listKnowledgeBases()
      qaLibraries.value = await listQaLibraries()
      if (!selectedKnowledgeBaseIds.value.length && knowledgeBases.value.length) {
        selectedKnowledgeBaseIds.value = [knowledgeBases.value[0].id]
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '读取 RAG 资源失败'
    } finally {
      isLoadingBases.value = false
    }
  }

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

  function useDemoQuestion(question: string) {
    input.value = question
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

  return {
    messages: readonly(messages),
    demoQuestions,
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
    useDemoQuestion,
    submit,
    toggleQaLibraryPicker,
    toggleQaLibrarySelection,
    openSavePanel,
    saveAsCard,
  }
}
