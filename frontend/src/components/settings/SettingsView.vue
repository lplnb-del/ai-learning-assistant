<script setup lang="ts">
import {
  Bot,
  CheckCircle2,
  Cpu,
  Globe,
  Loader2,
  RefreshCw,
  Save,
  Sparkles,
  Wand2,
} from '@lucide/vue'
import { useSettingsManager } from '../../composables/useSettingsManager'

const s = useSettingsManager()

const providers = [
  { value: 'deepseek', label: 'DeepSeek（云端）' },
  { value: 'openai', label: 'OpenAI（云端）' },
  { value: 'ollama', label: 'Ollama（本地）' },
]
</script>

<template>
  <section class="settings-view" aria-label="偏好设置">
    <header class="settings-header">
      <div class="settings-title-row">
        <Wand2 :size="22" aria-hidden="true" />
        <h1>偏好设置</h1>
      </div>
      <p class="settings-subtitle">配置对话模型和嵌入模型，支持云端与本地混合使用</p>
    </header>

    <div v-if="s.loading.value" class="settings-loading">
      <Loader2 :size="24" class="spin" aria-hidden="true" />
      <span>加载配置中...</span>
    </div>

    <div v-else-if="s.error.value" class="settings-error">
      {{ s.error.value }}
      <button type="button" class="btn-retry" @click="s.loadSettings">重试</button>
    </div>

    <div v-else class="settings-grid">
      <!-- Chat Model Card -->
      <div class="settings-card">
        <div class="card-header">
          <Bot :size="20" aria-hidden="true" />
          <h2>对话模型</h2>
          <span class="card-badge">{{ s.chatProviderLabel.value }}</span>
        </div>
        <p class="card-desc">用于 Chat、RAG 问答和 Agent 推理的大语言模型</p>

        <div class="form-group">
          <label>模型提供商</label>
          <select v-model="s.chatProvider.value" class="form-select">
            <option v-for="p in providers" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>

        <div v-if="s.chatProvider.value !== 'ollama'" class="form-group">
          <label>API Key</label>
          <input
            v-model="s.chatApiKey.value"
            type="password"
            class="form-input"
            placeholder="sk-..."
          />
        </div>

        <div class="form-group">
          <label>Base URL</label>
          <input
            v-model="s.chatBaseUrl.value"
            type="text"
            class="form-input"
            :placeholder="s.chatProvider.value === 'ollama' ? 'http://localhost:11434' : '留空使用默认地址'"
          />
        </div>

        <div class="form-group">
          <label>模型名称</label>
          <div class="model-input-row">
            <input
              v-model="s.chatModel.value"
              type="text"
              class="form-input"
              placeholder="deepseek-chat"
            />
            <button
              type="button"
              class="btn-detect"
              :disabled="s.detecting.value"
              @click="s.runDetection('chat')"
            >
              <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
              <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
              自动检测
            </button>
          </div>
        </div>

        <div v-if="s.detectedModels.value.length" class="detected-list">
          <p class="detected-label">检测到的模型：</p>
          <div class="detected-chips">
            <button
              v-for="m in s.detectedModels.value"
              :key="m.id"
              type="button"
              class="model-chip"
              :class="{ 'model-chip-active': s.chatModel.value === m.id }"
              @click="s.selectDetectedModel('chat', m.id)"
            >
              <Cpu :size="14" aria-hidden="true" />
              {{ m.name }}
            </button>
          </div>
        </div>

        <div class="card-footer">
          <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveChatConfig">
            <Save :size="16" aria-hidden="true" />
            {{ s.saving.value ? '保存中...' : '保存对话配置' }}
          </button>
        </div>
      </div>

      <!-- Embedding Model Card -->
      <div class="settings-card">
        <div class="card-header">
          <Sparkles :size="20" aria-hidden="true" />
          <h2>嵌入模型</h2>
          <span class="card-badge">{{ s.embeddingProviderLabel.value }}</span>
        </div>
        <p class="card-desc">用于知识库文档向量化和 Chroma 向量检索的嵌入模型</p>

        <div class="form-group">
          <label>模型提供商</label>
          <select v-model="s.embeddingProvider.value" class="form-select">
            <option v-for="p in providers" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>

        <div v-if="s.embeddingProvider.value !== 'ollama'" class="form-group">
          <label>API Key</label>
          <input
            v-model="s.embeddingApiKey.value"
            type="password"
            class="form-input"
            placeholder="sk-..."
          />
        </div>

        <div class="form-group">
          <label>Base URL</label>
          <input
            v-model="s.embeddingBaseUrl.value"
            type="text"
            class="form-input"
            :placeholder="s.embeddingProvider.value === 'ollama' ? 'http://localhost:11434' : '留空使用默认地址'"
          />
        </div>

        <div class="form-group">
          <label>模型名称</label>
          <div class="model-input-row">
            <input
              v-model="s.embeddingModel.value"
              type="text"
              class="form-input"
              placeholder="text-embedding-v3"
            />
            <button
              type="button"
              class="btn-detect"
              :disabled="s.detecting.value"
              @click="s.runDetection('embedding')"
            >
              <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
              <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
              自动检测
            </button>
          </div>
        </div>

        <div v-if="s.detectedModels.value.length" class="detected-list">
          <p class="detected-label">检测到的模型：</p>
          <div class="detected-chips">
            <button
              v-for="m in s.detectedModels.value"
              :key="m.id"
              type="button"
              class="model-chip"
              :class="{ 'model-chip-active': s.embeddingModel.value === m.id }"
              @click="s.selectDetectedModel('embedding', m.id)"
            >
              <Cpu :size="14" aria-hidden="true" />
              {{ m.name }}
            </button>
          </div>
        </div>

        <div class="card-footer">
          <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveEmbeddingConfig">
            <Save :size="16" aria-hidden="true" />
            {{ s.saving.value ? '保存中...' : '保存嵌入配置' }}
          </button>
        </div>
      </div>

      <!-- Status Card -->
      <div class="settings-card settings-status-card">
        <div class="card-header">
          <CheckCircle2 :size="20" aria-hidden="true" />
          <h2>当前状态</h2>
        </div>
        <div class="status-rows">
          <div class="status-row">
            <span class="status-label">对话模型</span>
            <span class="status-value">{{ s.settings.value?.chat_provider }} / {{ s.settings.value?.chat_model ?? '默认' }}</span>
          </div>
          <div class="status-row">
            <span class="status-label">嵌入模型</span>
            <span class="status-value">{{ s.settings.value?.embedding_provider }} / {{ s.settings.value?.embedding_model ?? '默认' }}</span>
          </div>
          <div class="status-row">
            <span class="status-label">向量存储</span>
            <span class="status-value">Chroma（LangChain）</span>
          </div>
          <div class="status-row">
            <span class="status-label">AI 编排</span>
            <span class="status-value">LangChain + LangGraph</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="s.detectResult.value && !s.detectResult.value.success" class="detect-banner">
      <Globe :size="16" aria-hidden="true" />
      {{ s.detectResult.value.message }}
    </div>
  </section>
</template>
