<script setup lang="ts">
import {
  AlertCircle,
  CheckCircle2,
  CloudUpload,
  FileText,
  Folder,
  Loader2,
  Play,
  Plus,
  Search,
  Settings2,
  Trash2,
} from '@lucide/vue'
import { useKnowledgeManager } from '../../composables/useKnowledgeManager'

const knowledge = useKnowledgeManager()

function onPdfFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  void knowledge.handlePdfFile(input.files?.[0] ?? null)
}
</script>

<template>
  <section class="resource-view" aria-label="知识库管理">
    <aside class="resource-sidebar">
      <header>
        <span>我的知识库</span>
        <button type="button" aria-label="新建知识库" :disabled="!knowledge.canCreateBase.value" @click="knowledge.createBase">
          <Plus :size="16" />
        </button>
      </header>
      <div class="base-create-form">
        <input v-model="knowledge.newBaseName.value" type="text" aria-label="知识库名称" placeholder="知识库名称" />
        <input
          v-model="knowledge.newBaseDescription.value"
          type="text"
          aria-label="知识库描述"
          placeholder="描述"
        />
      </div>
      <div
        v-for="base in knowledge.bases.value"
        :key="base.id"
        class="resource-nav-row"
        :class="{ 'resource-nav-active': base.id === knowledge.selectedBaseId.value }"
      >
        <button class="resource-nav-button" type="button" @click="knowledge.selectBase(base.id)">
          <Folder :size="17" />
          <span>{{ base.name }}</span>
          <code>{{ base.description || 'local' }}</code>
        </button>
        <button type="button" aria-label="删除知识库" @click="knowledge.requestDeleteBase(base)">
          <Trash2 :size="15" />
        </button>
      </div>
      <p v-if="!knowledge.bases.value.length && !knowledge.isLoading.value" class="resource-empty-text">暂无知识库</p>
    </aside>

    <main class="resource-main">
      <header class="resource-topbar">
        <div>
          <h2>{{ knowledge.selectedBase.value?.name || '知识库管理' }}</h2>
          <span>{{ knowledge.documents.value.length }} 文档</span>
        </div>
        <button type="button"><Search :size="16" />搜索文档</button>
      </header>

      <div class="resource-scroll">
        <form class="upload-zone import-panel" @submit.prevent="knowledge.submitImport">
          <span><CloudUpload :size="28" /></span>
          <strong>导入 Markdown / TXT 文本</strong>
          <input v-model="knowledge.importName.value" type="text" aria-label="文档名称" placeholder="文档名称，例如 rag.md" />
          <textarea
            v-model="knowledge.importContent.value"
            rows="7"
            aria-label="文档内容"
            placeholder="粘贴 Markdown 或 TXT 内容"
          ></textarea>
          <button type="submit" :disabled="!knowledge.canImport.value">
            <Loader2 v-if="knowledge.isImporting.value" :size="16" />
            <CloudUpload v-else :size="16" />
            导入并切分
          </button>
          <small>真实向量写入会在 RAG 阶段接入</small>
        </form>

        <form class="upload-zone import-panel pdf-import-panel" @submit.prevent="knowledge.submitPdfImport">
          <strong>导入 PDF 文档</strong>
          <input type="file" accept="application/pdf,.pdf" aria-label="选择 PDF 文件" @change="onPdfFileChange" />
          <div v-if="knowledge.pdfFileName.value" class="selected-file">
            <FileText :size="16" />
            <em>{{ knowledge.pdfFileName.value }}</em>
          </div>
          <button type="submit" :disabled="!knowledge.canImportPdf.value">
            <Loader2 v-if="knowledge.isImporting.value" :size="16" />
            <CloudUpload v-else :size="16" />
            抽取并切分
          </button>
          <small>后端只抽取文本，不保存前端密钥或调用外部服务</small>
        </form>

        <form class="upload-zone import-panel url-import-panel" @submit.prevent="knowledge.submitUrlImport">
          <strong>从 URL 抓取正文</strong>
          <input v-model="knowledge.importUrl.value" type="url" aria-label="网页 URL" placeholder="https://example.com/article" />
          <input
            v-model="knowledge.importUrlName.value"
            type="text"
            aria-label="URL 文档名称"
            placeholder="可选：文档名称"
          />
          <button type="submit" :disabled="!knowledge.canImportUrl.value">
            <Loader2 v-if="knowledge.isImporting.value" :size="16" />
            <CloudUpload v-else :size="16" />
            抓取并切分
          </button>
          <small>仅支持公开 http(s) 页面；内网和本机地址会被拒绝</small>
        </form>

        <p v-if="knowledge.errorMessage.value" class="resource-message resource-message-error">
          <AlertCircle :size="16" />{{ knowledge.errorMessage.value }}
        </p>
        <p v-if="knowledge.successMessage.value" class="resource-message resource-message-success">
          <CheckCircle2 :size="16" />{{ knowledge.successMessage.value }}
        </p>

        <section>
          <p class="resource-section-title">已上传文档 ({{ knowledge.documents.value.length }})</p>
          <div class="document-list">
            <article
              v-for="doc in knowledge.documents.value"
              :key="doc.id"
              class="document-row"
              :class="{ 'document-row-active': doc.id === knowledge.selectedDocumentId.value }"
              @click="knowledge.selectDocument(doc.id)"
            >
              <div class="document-main">
                <div class="file-icon"><FileText :size="17" /></div>
                <div>
                  <strong>{{ doc.name }}</strong>
                  <span>{{ doc.content_type }} · {{ new Date(doc.created_at).toLocaleString() }}</span>
                </div>
              </div>
              <div class="document-actions">
                <span class="doc-status doc-status-success">
                  {{ doc.status }}
                </span>
                <button type="button" aria-label="删除文档" @click.stop="knowledge.requestDeleteDocument(doc)">
                  <Trash2 :size="16" />
                </button>
              </div>
            </article>
          </div>
          <p v-if="!knowledge.documents.value.length" class="resource-empty-text">当前知识库还没有文档</p>
        </section>

        <section v-if="knowledge.chunks.value.length">
          <p class="resource-section-title">Chunk 预览 ({{ knowledge.chunks.value.length }})</p>
          <div class="chunk-preview-list">
            <article v-for="chunk in knowledge.chunks.value" :key="chunk.id" class="chunk-preview-item">
              <header>
                <strong>#{{ chunk.index + 1 }}</strong>
                <span>{{ chunk.title || knowledge.selectedDocument.value?.name }}</span>
              </header>
              <p>{{ chunk.text }}</p>
            </article>
          </div>
        </section>
      </div>
    </main>

    <aside class="resource-config">
      <header><Settings2 :size="17" />知识库处理配置</header>
      <div class="config-body">
        <div v-if="knowledge.pendingDelete.value" class="delete-confirm-panel">
          <strong>确认删除 {{ knowledge.pendingDelete.value.name }}？</strong>
          <p>
            {{
              knowledge.pendingDelete.value.kind === 'base'
                ? '会同时删除该知识库下的文档和 chunks。'
                : '会同时删除该文档的 chunks。'
            }}
          </p>
          <div>
            <button type="button" @click="knowledge.confirmDelete">确认删除</button>
            <button type="button" @click="knowledge.cancelDelete">取消</button>
          </div>
        </div>
        <label>文本切分策略<select><option>按标题段落</option></select></label>
        <div class="config-grid">
          <label>Chunk Size<input v-model.number="knowledge.chunkSize.value" type="number" min="200" max="3000" /></label>
          <label>Overlap<input v-model.number="knowledge.chunkOverlap.value" type="number" min="0" max="1000" /></label>
        </div>
        <label>向量模型<div class="readonly-input">text-embedding-v3-small</div></label>
        <div v-if="knowledge.indexBuildResult.value" class="index-status-panel">
          <strong>{{ knowledge.indexBuildResult.value.status }}</strong>
          <p>{{ knowledge.indexBuildResult.value.message }}</p>
          <span>{{ knowledge.indexBuildResult.value.document_count }} 文档 · {{ knowledge.indexBuildResult.value.chunk_count }} chunks</span>
        </div>
      </div>
      <footer>
        <button type="button" :disabled="!knowledge.canRebuildIndex.value" @click="knowledge.rebuildIndex">
          <Loader2 v-if="knowledge.isRebuildingIndex.value" :size="16" />
          <Play v-else :size="16" />
          开始构建向量索引
        </button>
      </footer>
    </aside>
  </section>
</template>
