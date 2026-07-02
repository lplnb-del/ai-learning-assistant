import { computed, onMounted, readonly, ref, shallowRef } from 'vue'
import {
  createQaCard,
  createQaLibrary,
  deleteQaCard,
  deleteQaLibrary,
  generateCardsFromChunks,
  generateCardsFromDocument,
  traceCardSources,
  type CardSourceTracePayload,
  listQaCards,
  listQaLibraries,
  updateQaCardMastery,
  type MasteryLevel,
  type QACardPayload,
  type QALibraryPayload,
} from '../api/cards'
import { listKnowledgeBases, listKnowledgeDocuments, listDocumentChunks, type KnowledgeBasePayload, type SourceDocumentPayload, type ChunkPayload } from '../api/knowledge'

const defaultQuestion = 'RAG 和普通 Chat 的区别是什么？'
const defaultAnswer = 'RAG 会先检索知识库资料，并基于来源片段组织回答；普通 Chat 不绑定指定知识库。'

export function useCardsManager() {
  const cards = ref<QACardPayload[]>([])
  const qaLibraries = ref<QALibraryPayload[]>([])
  const knowledgeBases = ref<KnowledgeBasePayload[]>([])

  const selectedLibraryId = shallowRef('')
  const selectedCardId = shallowRef('')
  const selectedKnowledgeBaseId = shallowRef('')
  const selectedMastery = shallowRef<MasteryLevel | ''>('')
  const tagFilter = shallowRef('')

  const generateKnowledgeBaseId = shallowRef('')
  const generateDocumentId = shallowRef('')
  const generateTagsDraft = shallowRef('')
  const isGenerating = shallowRef(false)
  const isTracing = shallowRef(false)
  const tracedSources = ref<CardSourceTracePayload[]>([])
  const showSourcePanel = shallowRef(false)
  const availableDocuments = ref<SourceDocumentPayload[]>([])
  const availableChunks = ref<ChunkPayload[]>([])
  const selectedChunkIds = ref<string[]>([])

  const isLoading = shallowRef(false)
  const isSaving = shallowRef(false)
  const isFlipped = shallowRef(false)
  const errorMessage = shallowRef('')
  const successMessage = shallowRef('')

  const libraryNameDraft = shallowRef('后端面试问答')
  const libraryDescriptionDraft = shallowRef('沉淀高频问题、标准答案和面试表达')
  const questionDraft = shallowRef(defaultQuestion)
  const answerDraft = shallowRef(defaultAnswer)
  const tagsDraft = shallowRef('RAG, 面试')
  const cardKnowledgeBaseIdDraft = shallowRef('')

  const selectedLibrary = computed(() => qaLibraries.value.find((library) => library.id === selectedLibraryId.value) ?? null)
  const selectedCard = computed(() => cards.value.find((card) => card.id === selectedCardId.value) ?? null)
  const cardPosition = computed(() => {
    const index = cards.value.findIndex((card) => card.id === selectedCardId.value)
    return index >= 0 ? index + 1 : 0
  })
  const canCreateLibrary = computed(() => libraryNameDraft.value.trim().length > 0 && !isSaving.value)
  const canGenerateFromDocument = computed(
    () =>
      Boolean(selectedLibraryId.value) &&
      Boolean(generateDocumentId.value) &&
      !isGenerating.value,
  )
  const canGenerateFromChunks = computed(
    () =>
      Boolean(selectedLibraryId.value) &&
      selectedChunkIds.value.length > 0 &&
      !isGenerating.value,
  )

  const canCreateCard = computed(
    () =>
      Boolean(selectedLibraryId.value) &&
      questionDraft.value.trim().length > 0 &&
      answerDraft.value.trim().length > 0 &&
      !isSaving.value,
  )

  onMounted(() => {
    void initialize()
  })

  async function initialize() {
    await runTask(async () => {
      knowledgeBases.value = await listKnowledgeBases()
      qaLibraries.value = await listQaLibraries()
      selectedLibraryId.value = selectedLibraryId.value || qaLibraries.value[0]?.id || ''
      await refreshCards()
    })
  }

  async function refreshCards() {
    cards.value = selectedLibraryId.value
      ? await listQaCards({
          qaLibraryId: selectedLibraryId.value,
          knowledgeBaseId: selectedKnowledgeBaseId.value,
          mastery: selectedMastery.value,
          tag: tagFilter.value,
        })
      : []
    if (!cards.value.some((card) => card.id === selectedCardId.value)) {
      selectedCardId.value = cards.value[0]?.id ?? ''
      isFlipped.value = false
    }
  }

  async function createLibrary() {
    if (!canCreateLibrary.value) {
      return
    }
    isSaving.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const created = await createQaLibrary({
        name: libraryNameDraft.value.trim(),
        description: libraryDescriptionDraft.value.trim(),
      })
      qaLibraries.value = [created, ...qaLibraries.value]
      selectedLibraryId.value = created.id
      selectedCardId.value = ''
      successMessage.value = '问答库已创建'
      await refreshCards()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '创建问答库失败'
    } finally {
      isSaving.value = false
    }
  }

  async function removeSelectedLibrary() {
    const library = selectedLibrary.value
    if (!library) {
      return
    }
    await runTask(async () => {
      await deleteQaLibrary(library.id)
      qaLibraries.value = qaLibraries.value.filter((item) => item.id !== library.id)
      selectedLibraryId.value = qaLibraries.value[0]?.id ?? ''
      selectedCardId.value = ''
      successMessage.value = '问答库已删除'
      await refreshCards()
    })
  }

  async function applyFilters() {
    await runTask(refreshCards)
  }

  async function selectLibrary(libraryId: string) {
    if (libraryId === selectedLibraryId.value) {
      return
    }
    selectedLibraryId.value = libraryId
    await runTask(refreshCards)
  }

  async function createManualCard() {
    if (!canCreateCard.value) {
      return
    }
    isSaving.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const created = await createQaCard({
        qa_library_id: selectedLibraryId.value,
        question: questionDraft.value.trim(),
        answer: answerDraft.value.trim(),
        knowledge_base_id: cardKnowledgeBaseIdDraft.value || null,
        tags: parseTags(tagsDraft.value),
      })
      cards.value = [created, ...cards.value]
      selectedCardId.value = created.id
      isFlipped.value = false
      successMessage.value = '卡片已创建'
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '创建卡片失败'
    } finally {
      isSaving.value = false
    }
  }

  async function setMastery(mastery: MasteryLevel) {
    const card = selectedCard.value
    if (!card) {
      return
    }
    isSaving.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const updated = await updateQaCardMastery(card.id, mastery)
      cards.value = cards.value.map((item) => (item.id === updated.id ? updated : item))
      successMessage.value = '掌握程度已更新'
      selectNextCard()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '更新掌握程度失败'
    } finally {
      isSaving.value = false
    }
  }

  async function removeSelectedCard() {
    const card = selectedCard.value
    if (!card) {
      return
    }
    await runTask(async () => {
      await deleteQaCard(card.id)
      cards.value = cards.value.filter((item) => item.id !== card.id)
      selectedCardId.value = cards.value[0]?.id ?? ''
      isFlipped.value = false
      successMessage.value = '卡片已删除'
    })
  }

  function selectCard(cardId: string) {
    selectedCardId.value = cardId
    isFlipped.value = false
  }

  function toggleFlip() {
    if (selectedCard.value) {
      isFlipped.value = !isFlipped.value
    }
  }

  function selectNextCard() {
    if (cards.value.length <= 1) {
      isFlipped.value = false
      return
    }
    const index = cards.value.findIndex((card) => card.id === selectedCardId.value)
    selectedCardId.value = cards.value[(index + 1) % cards.value.length].id
    isFlipped.value = false
  }

  async function runTask(task: () => Promise<void>) {
    isLoading.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      await task()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '请求失败'
    } finally {
      isLoading.value = false
    }
  }

  async function loadDocuments() {
    if (!generateKnowledgeBaseId.value) {
      availableDocuments.value = []
      availableChunks.value = []
      generateDocumentId.value = ''
      selectedChunkIds.value = []
      return
    }
    try {
      availableDocuments.value = await listKnowledgeDocuments(generateKnowledgeBaseId.value)
      generateDocumentId.value = availableDocuments.value[0]?.id ?? ''
      await loadChunks()
    } catch {
      availableDocuments.value = []
    }
  }

  async function loadChunks() {
    if (!generateDocumentId.value) {
      availableChunks.value = []
      selectedChunkIds.value = []
      return
    }
    try {
      availableChunks.value = await listDocumentChunks(generateDocumentId.value)
      selectedChunkIds.value = []
    } catch {
      availableChunks.value = []
    }
  }

  function toggleChunkSelection(chunkId: string) {
    const index = selectedChunkIds.value.indexOf(chunkId)
    if (index >= 0) {
      selectedChunkIds.value = selectedChunkIds.value.filter((id) => id !== chunkId)
    } else {
      selectedChunkIds.value = [...selectedChunkIds.value, chunkId]
    }
  }

  function selectAllChunks() {
    selectedChunkIds.value = availableChunks.value.map((chunk) => chunk.id)
  }

  function clearChunkSelection() {
    selectedChunkIds.value = []
  }

  async function generateFromDocument() {
    if (!canGenerateFromDocument.value) {
      return
    }
    isGenerating.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await generateCardsFromDocument({
        qa_library_id: selectedLibraryId.value,
        document_id: generateDocumentId.value,
        tags: generateTagsDraft.value
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      })
      successMessage.value = `已从文档生成 ${result.generated_count} 张候选卡片`
      await refreshCards()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '生成卡片失败'
    } finally {
      isGenerating.value = false
    }
  }

  async function generateFromChunks() {
    if (!canGenerateFromChunks.value) {
      return
    }
    isGenerating.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await generateCardsFromChunks({
        qa_library_id: selectedLibraryId.value,
        chunk_ids: selectedChunkIds.value,
        knowledge_base_id: generateKnowledgeBaseId.value || undefined,
        tags: generateTagsDraft.value
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      })
      successMessage.value = `已从选中的切片生成 ${result.generated_count} 张候选卡片`
      await refreshCards()
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '生成卡片失败'
    } finally {
      isGenerating.value = false
    }
  }

  async function traceSelectedCardSources() {
    if (!selectedCard.value) {
      tracedSources.value = []
      showSourcePanel.value = false
      return
    }
    if (!selectedCard.value.source_chunk_ids.length) {
      tracedSources.value = []
      showSourcePanel.value = false
      errorMessage.value = '当前卡片没有关联的知识库来源'
      return
    }
    isTracing.value = true
    errorMessage.value = ''
    try {
      tracedSources.value = await traceCardSources(selectedCard.value.id)
      showSourcePanel.value = true
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '追溯来源失败'
    } finally {
      isTracing.value = false
    }
  }

  function closeSourcePanel() {
    showSourcePanel.value = false
    tracedSources.value = []
  }

  return {
    cards: readonly(cards),
    qaLibraries: readonly(qaLibraries),
    knowledgeBases: readonly(knowledgeBases),
    selectedLibrary,
    selectedCard,
    cardPosition,
    selectedLibraryId,
    selectedCardId,
    selectedKnowledgeBaseId,
    selectedMastery,
    tagFilter,
    isLoading,
    isSaving,
    isFlipped,
    errorMessage,
    successMessage,
    libraryNameDraft,
    libraryDescriptionDraft,
    questionDraft,
    answerDraft,
    tagsDraft,
    cardKnowledgeBaseIdDraft,
    canCreateLibrary,
    canCreateCard,
    createLibrary,
    removeSelectedLibrary,
    applyFilters,
    selectLibrary,
    createManualCard,
    setMastery,
    removeSelectedCard,
    selectCard,
    toggleFlip,
      // Generation
    generateKnowledgeBaseId,
    generateDocumentId,
    generateTagsDraft,
    isGenerating,
    availableDocuments,
    availableChunks,
    selectedChunkIds,
    canGenerateFromDocument,
    canGenerateFromChunks,
    loadDocuments,
    loadChunks,
    toggleChunkSelection,
    selectAllChunks,
    clearChunkSelection,
    generateFromDocument,
    generateFromChunks,
    isTracing,
    tracedSources,
    showSourcePanel,
    traceSelectedCardSources,
    closeSourcePanel,
  }
}

function parseTags(rawTags: string): string[] {
  return rawTags
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}
