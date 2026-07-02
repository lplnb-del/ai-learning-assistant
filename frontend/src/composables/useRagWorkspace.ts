import { computed, onMounted, readonly, ref, shallowRef } from 'vue'
import { listKnowledgeBases, type KnowledgeBasePayload } from '../api/knowledge'
import { askRagQuestion, type RagSourcePayload } from '../api/rag'

export interface RagViewMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: string
  sources?: RagSourcePayload[]
  promptPreview?: string
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
    status: '本地 RAG 已就绪，可选择知识库后提问',
    content:
      'RAG 会先从知识库检索相关 chunks，再把问题和资料片段组装成 prompt。当前阶段先返回本地检索摘要和来源，后续会接入 Embedding/Chroma 与模型生成。',
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
  const selectedKnowledgeBaseId = shallowRef('')
  const input = shallowRef('')
  const topK = shallowRef(3)
  const isLoadingBases = shallowRef(false)
  const isAsking = shallowRef(false)
  const errorMessage = shallowRef('')

  const selectedKnowledgeBase = computed(
    () => knowledgeBases.value.find((base) => base.id === selectedKnowledgeBaseId.value) ?? null,
  )
  const canSubmit = computed(
    () => input.value.trim().length > 0 && Boolean(selectedKnowledgeBaseId.value) && !isAsking.value,
  )
  onMounted(() => {
    void refreshKnowledgeBases()
  })

  async function refreshKnowledgeBases() {
    isLoadingBases.value = true
    errorMessage.value = ''
    try {
      knowledgeBases.value = await listKnowledgeBases()
      if (!selectedKnowledgeBaseId.value && knowledgeBases.value[0]) {
        selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
      }
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '读取知识库失败'
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
      status: '正在检索本地知识库',
    }
    messages.value = [...messages.value, userMessage, assistantMessage]

    try {
      const result = await askRagQuestion({
        knowledge_base_id: selectedKnowledgeBaseId.value,
        question,
        top_k: topK.value,
      })
      assistantMessage.content = result.answer
      assistantMessage.status =
        result.sources.length > 0
          ? `命中 ${result.sources.length} 个片段 · ${result.retrieval_mode}`
          : '未命中相关片段'
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

  return {
    messages: readonly(messages),
    demoQuestions,
    knowledgeBases: readonly(knowledgeBases),
    selectedKnowledgeBaseId,
    selectedKnowledgeBase,
    input,
    topK,
    isLoadingBases,
    isAsking,
    errorMessage,
    canSubmit,
    refreshKnowledgeBases,
    useDemoQuestion,
    submit,
  }
}
