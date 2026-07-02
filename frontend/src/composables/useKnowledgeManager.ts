import { computed, onMounted, readonly, ref, shallowRef } from 'vue'
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  deleteKnowledgeDocument,
  importPdfDocument,
  importTextDocument,
  importUrlDocument,
  listDocumentChunks,
  listKnowledgeBases,
  listKnowledgeDocuments,
  rebuildKnowledgeIndex,
  type ChunkPayload,
  type KnowledgeIndexBuildPayload,
  type KnowledgeBasePayload,
  type SourceDocumentPayload,
} from '../api/knowledge'

type PendingDelete =
  | { kind: 'base'; id: string; name: string }
  | { kind: 'document'; id: string; name: string }

const sampleMarkdown = `# RAG 入门

RAG 会先检索资料，再把命中的上下文交给大模型组织答案。

## 适合场景

课程资料、项目文档、论文笔记和面试复习都适合使用 RAG。`

export function useKnowledgeManager() {
  const bases = ref<KnowledgeBasePayload[]>([])
  const documents = ref<SourceDocumentPayload[]>([])
  const chunks = ref<ChunkPayload[]>([])
  const selectedBaseId = shallowRef('')
  const selectedDocumentId = shallowRef('')
  const isLoading = shallowRef(false)
  const isImporting = shallowRef(false)
  const isRebuildingIndex = shallowRef(false)
  const errorMessage = shallowRef('')
  const successMessage = shallowRef('')
  const indexBuildResult = shallowRef<KnowledgeIndexBuildPayload | null>(null)
  const pendingDelete = shallowRef<PendingDelete | null>(null)

  const newBaseName = shallowRef('项目文档')
  const newBaseDescription = shallowRef('用于 RAG 演示')
  const importName = shallowRef('rag-note.md')
  const importContent = shallowRef(sampleMarkdown)
  const importUrl = shallowRef('https://example.com/rag')
  const importUrlName = shallowRef('')
  const pdfFileName = shallowRef('')
  const pdfContentBase64 = shallowRef('')
  const chunkSize = shallowRef(800)
  const chunkOverlap = shallowRef(120)

  const selectedBase = computed(() => bases.value.find((base) => base.id === selectedBaseId.value) ?? null)
  const selectedDocument = computed(
    () => documents.value.find((document) => document.id === selectedDocumentId.value) ?? null,
  )
  const canCreateBase = computed(() => newBaseName.value.trim().length > 0 && !isLoading.value)
  const canImport = computed(
    () =>
      Boolean(selectedBaseId.value) &&
      importName.value.trim().length > 0 &&
      importContent.value.trim().length > 0 &&
      !isImporting.value,
  )
  const canImportUrl = computed(
    () => Boolean(selectedBaseId.value) && importUrl.value.trim().length > 0 && !isImporting.value,
  )
  const canImportPdf = computed(
    () =>
      Boolean(selectedBaseId.value) &&
      pdfFileName.value.trim().length > 0 &&
      Boolean(pdfContentBase64.value) &&
      !isImporting.value,
  )
  const canRebuildIndex = computed(
    () =>
      Boolean(selectedBaseId.value) &&
      documents.value.length > 0 &&
      !isLoading.value &&
      !isImporting.value &&
      !isRebuildingIndex.value,
  )

  onMounted(() => {
    void refreshBases()
  })

  async function refreshBases() {
    await runTask(async () => {
      bases.value = await listKnowledgeBases()
      if (!selectedBaseId.value && bases.value[0]) {
        selectedBaseId.value = bases.value[0].id
      }
      if (selectedBaseId.value) {
        await refreshDocuments()
      }
    })
  }

  async function createBase() {
    if (!canCreateBase.value) {
      return
    }
    await runTask(async () => {
      const created = await createKnowledgeBase({
        name: newBaseName.value.trim(),
        description: newBaseDescription.value.trim(),
      })
      bases.value = [created, ...bases.value]
      selectedBaseId.value = created.id
      documents.value = []
      chunks.value = []
      selectedDocumentId.value = ''
      indexBuildResult.value = null
      successMessage.value = '知识库已创建'
    })
  }

  function requestDeleteBase(base: KnowledgeBasePayload) {
    pendingDelete.value = { kind: 'base', id: base.id, name: base.name }
  }

  function requestDeleteDocument(document: SourceDocumentPayload) {
    pendingDelete.value = { kind: 'document', id: document.id, name: document.name }
  }

  function cancelDelete() {
    pendingDelete.value = null
  }

  async function confirmDelete() {
    const target = pendingDelete.value
    if (!target) {
      return
    }
    await runTask(async () => {
      if (target.kind === 'base') {
        await deleteKnowledgeBase(target.id)
        bases.value = bases.value.filter((base) => base.id !== target.id)
        if (selectedBaseId.value === target.id) {
          selectedBaseId.value = bases.value[0]?.id ?? ''
          selectedDocumentId.value = ''
          indexBuildResult.value = null
          chunks.value = []
          documents.value = []
          if (selectedBaseId.value) {
            await refreshDocuments()
          }
        }
        successMessage.value = '知识库已删除'
      } else {
        await deleteKnowledgeDocument(target.id)
        documents.value = documents.value.filter((document) => document.id !== target.id)
        indexBuildResult.value = null
        if (selectedDocumentId.value === target.id) {
          selectedDocumentId.value = documents.value[0]?.id ?? ''
          chunks.value = []
          if (selectedDocumentId.value) {
            await selectDocument(selectedDocumentId.value)
          }
        }
        successMessage.value = '文档已删除'
      }
      pendingDelete.value = null
    })
  }

  async function selectBase(baseId: string) {
    if (baseId === selectedBaseId.value) {
      return
    }
    await runTask(async () => {
      selectedBaseId.value = baseId
      selectedDocumentId.value = ''
      chunks.value = []
      indexBuildResult.value = null
      await refreshDocuments()
    })
  }

  async function refreshDocuments() {
    if (!selectedBaseId.value) {
      documents.value = []
      return
    }
    documents.value = await listKnowledgeDocuments(selectedBaseId.value)
    if (!selectedDocumentId.value && documents.value[0]) {
      await selectDocument(documents.value[0].id)
    }
  }

  async function submitImport() {
    if (!canImport.value) {
      return
    }
    isImporting.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await importTextDocument(selectedBaseId.value, {
        name: importName.value.trim(),
        source_uri: importName.value.trim(),
        content: importContent.value.trim(),
        content_type: inferContentType(importName.value),
        chunk_size: chunkSize.value,
        chunk_overlap: chunkOverlap.value,
      })
      documents.value = [result.document, ...documents.value]
      chunks.value = result.chunks
      selectedDocumentId.value = result.document.id
      indexBuildResult.value = null
      successMessage.value = `已导入 ${result.chunk_count} 个 chunks`
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '导入失败'
    } finally {
      isImporting.value = false
    }
  }

  async function submitUrlImport() {
    if (!canImportUrl.value) {
      return
    }
    isImporting.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await importUrlDocument(selectedBaseId.value, {
        url: importUrl.value.trim(),
        name: importUrlName.value.trim(),
        chunk_size: chunkSize.value,
        chunk_overlap: chunkOverlap.value,
      })
      documents.value = [result.document, ...documents.value]
      chunks.value = result.chunks
      selectedDocumentId.value = result.document.id
      indexBuildResult.value = null
      successMessage.value = `已从 URL 导入 ${result.chunk_count} 个 chunks`
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'URL 导入失败'
    } finally {
      isImporting.value = false
    }
  }

  async function handlePdfFile(file: File | null) {
    errorMessage.value = ''
    successMessage.value = ''
    pdfFileName.value = ''
    pdfContentBase64.value = ''
    if (!file) {
      return
    }
    if (file.type && file.type !== 'application/pdf') {
      errorMessage.value = '请选择 PDF 文件'
      return
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      errorMessage.value = '请选择 .pdf 文件'
      return
    }
    try {
      const dataUrl = await readFileAsDataUrl(file)
      const [, base64Content = ''] = dataUrl.split(',', 2)
      if (!base64Content) {
        throw new Error('PDF 文件读取失败')
      }
      pdfFileName.value = file.name
      pdfContentBase64.value = base64Content
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'PDF 文件读取失败'
    }
  }

  async function submitPdfImport() {
    if (!canImportPdf.value) {
      return
    }
    isImporting.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await importPdfDocument(selectedBaseId.value, {
        name: pdfFileName.value.trim(),
        content_base64: pdfContentBase64.value,
        chunk_size: chunkSize.value,
        chunk_overlap: chunkOverlap.value,
      })
      documents.value = [result.document, ...documents.value]
      chunks.value = result.chunks
      selectedDocumentId.value = result.document.id
      indexBuildResult.value = null
      successMessage.value = `已从 PDF 导入 ${result.chunk_count} 个 chunks`
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : 'PDF 导入失败'
    } finally {
      isImporting.value = false
    }
  }

  async function rebuildIndex() {
    if (!canRebuildIndex.value) {
      return
    }
    isRebuildingIndex.value = true
    errorMessage.value = ''
    successMessage.value = ''
    try {
      const result = await rebuildKnowledgeIndex(selectedBaseId.value)
      indexBuildResult.value = result
      successMessage.value = `索引准备完成：${result.document_count} 文档 / ${result.chunk_count} chunks`
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '重建索引失败'
    } finally {
      isRebuildingIndex.value = false
    }
  }

  async function selectDocument(documentId: string) {
    selectedDocumentId.value = documentId
    try {
      chunks.value = await listDocumentChunks(documentId)
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : '读取 chunks 失败'
    }
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

  return {
    bases: readonly(bases),
    documents: readonly(documents),
    chunks: readonly(chunks),
    selectedBase,
    selectedDocument,
    selectedBaseId,
    selectedDocumentId,
    isLoading,
    isImporting,
    isRebuildingIndex,
    errorMessage,
    successMessage,
    indexBuildResult,
    pendingDelete,
    newBaseName,
    newBaseDescription,
    importName,
    importContent,
    importUrl,
    importUrlName,
    pdfFileName,
    chunkSize,
    chunkOverlap,
    canCreateBase,
    canImport,
    canImportUrl,
    canImportPdf,
    canRebuildIndex,
    createBase,
    requestDeleteBase,
    requestDeleteDocument,
    cancelDelete,
    confirmDelete,
    selectBase,
    submitImport,
    submitUrlImport,
    handlePdfFile,
    submitPdfImport,
    rebuildIndex,
    selectDocument,
  }
}

function inferContentType(name: string): string {
  return name.toLowerCase().endsWith('.md') || name.toLowerCase().endsWith('.markdown')
    ? 'text/markdown'
    : 'text/plain'
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('PDF 文件读取失败'))
    reader.readAsDataURL(file)
  })
}
