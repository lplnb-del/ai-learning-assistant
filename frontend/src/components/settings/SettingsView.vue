<script setup lang="ts">
import {
  Bot,
  CheckCircle2,
  Cpu,
  Globe,
  Loader2,
  Plug,
  RefreshCw,
  Save,
  Server,
  Sparkles,
  Wand2,
} from '@lucide/vue'
import { useSettingsManager } from '../../composables/useSettingsManager'

const s = useSettingsManager()

function onChatPresetChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  if (value) s.applyChatPreset(value)
}

function onEmbeddingPresetChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  if (value) s.applyEmbeddingPreset(value)
}
</script>

<template>
  <section class="settings-view" aria-label="偏好设置">
    <header class="settings-header">
      <div class="settings-title-row">
        <Wand2 :size="22" aria-hidden="true" />
        <h1>偏好设置</h1>
      </div>
      <p class="settings-subtitle">配置对话模型和嵌入模型。支持任何 OpenAI 兼容协议的云端/本地模型，以及 HuggingFace 本地嵌入。</p>
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
      <!-- ======== Chat Model Card ======== -->
      <div class="settings-card">
        <div class="card-header">
          <Bot :size="20" aria-hidden="true" />
          <h2>对话模型</h2>
        </div>
        <p class="card-desc">Chat / RAG 问答 / Agent 推理所用的大语言模型</p>

        <!-- Provider type -->
        <div class="form-group">
          <label>接入方式</label>
          <select v-model="s.chatProvider.value" class="form-select">
            <option v-for="p in s.PROVIDER_OPTIONS" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
          <span class="form-hint">{{ s.PROVIDER_OPTIONS.find(o => o.value === s.chatProvider.value)?.desc }}</span>
        </div>

        <!-- Preset selector (only for openai_compatible) -->
        <div v-if="s.chatProvider.value === 'openai_compatible'" class="form-group">
          <label>预设服务</label>
          <select class="form-select" :value="s.chatPreset.value" @change="onChatPresetChange">
            <option value="">请选择或手动配置</option>
            <option v-for="p in s.chatPresetOptions.value" :key="p.key" :value="p.key">{{ p.name }}</option>
          </select>
        </div>

        <!-- API Key (not needed for ollama) -->
        <div v-if="s.chatProvider.value !== 'ollama'" class="form-group">
          <label>API Key</label>
          <input v-model="s.chatApiKey.value" type="password" class="form-input" placeholder="sk-..." />
        </div>

        <!-- Base URL -->
        <div class="form-group">
          <label>Base URL</label>
          <input
            v-model="s.chatBaseUrl.value"
            type="text"
            class="form-input"
            :placeholder="s.chatProvider.value === 'ollama' ? 'http://localhost:11434' : 'https://api.example.com/v1'"
          />
        </div>

        <!-- Model name -->
        <div class="form-group">
          <label>模型名称</label>
          <div class="model-input-row">
            <input v-model="s.chatModel.value" type="text" class="form-input" placeholder="模型 ID" />
            <button
              type="button"
              class="btn-detect"
              :disabled="s.detecting.value"
              @click="s.runDetection('chat')"
            >
              <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
              <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
              检测模型
            </button>
          </div>
          <span v-if="s.currentChatPreset.value?.default_chat_model" class="form-hint">
            推荐: {{ s.currentChatPreset.value.default_chat_model }}
          </span>
        </div>

        <!-- Detected models -->
        <div v-if="s.detectedModels.value.length" class="detected-list">
          <p class="detected-label">可用模型：</p>
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

      <!-- ======== Embedding Model Card ======== -->
      <div class="settings-card">
        <div class="card-header">
          <Sparkles :size="20" aria-hidden="true" />
          <h2>嵌入模型</h2>
        </div>
        <p class="card-desc">知识库文档向量化和 Chroma 向量检索所用的嵌入模型</p>

        <!-- Provider type -->
        <div class="form-group">
          <label>接入方式</label>
          <select v-model="s.embeddingProvider.value" class="form-select">
            <option v-for="p in s.EMBEDDING_PROVIDER_OPTIONS" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
          <span class="form-hint">{{ s.EMBEDDING_PROVIDER_OPTIONS.find(o => o.value === s.embeddingProvider.value)?.desc }}</span>
        </div>

        <!-- Preset selector (only for openai_compatible) -->
        <div v-if="s.embeddingProvider.value === 'openai_compatible'" class="form-group">
          <label>预设服务</label>
          <select class="form-select" :value="s.embeddingPreset.value" @change="onEmbeddingPresetChange">
            <option value="">请选择或手动配置</option>
            <option v-for="p in s.embeddingPresetOptions.value" :key="p.key" :value="p.key">{{ p.name }}</option>
          </select>
        </div>

        <!-- API Key -->
        <div v-if="s.embeddingProvider.value !== 'ollama' && s.embeddingProvider.value !== 'huggingface'" class="form-group">
          <label>API Key</label>
          <input v-model="s.embeddingApiKey.value" type="password" class="form-input" placeholder="sk-..." />
        </div>

        <!-- Base URL -->
        <div v-if="s.embeddingProvider.value !== 'huggingface'" class="form-group">
          <label>Base URL</label>
          <input
            v-model="s.embeddingBaseUrl.value"
            type="text"
            class="form-input"
            :placeholder="s.embeddingProvider.value === 'ollama' ? 'http://localhost:11434' : 'https://api.example.com/v1'"
          />
        </div>

        <!-- Model name -->
        <div class="form-group">
          <label>{{ s.embeddingProvider.value === 'huggingface' ? 'HuggingFace 模型名称' : '模型名称' }}</label>
          <div class="model-input-row">
            <input
              v-model="s.embeddingModel.value"
              type="text"
              class="form-input"
              :placeholder="s.embeddingProvider.value === 'huggingface' ? 'sentence-transformers/all-MiniLM-L6-v2' : '嵌入模型 ID'"
            />
            <button
              type="button"
              class="btn-detect"
              :disabled="s.detecting.value"
              @click="s.runDetection('embedding')"
            >
              <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
              <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
              检测模型
            </button>
          </div>
          <span v-if="s.currentEmbeddingPreset.value?.default_embedding_model" class="form-hint">
            推荐: {{ s.currentEmbeddingPreset.value.default_embedding_model }}
          </span>
        </div>

        <!-- Detected models -->
        <div v-if="s.detectedModels.value.length" class="detected-list">
          <p class="detected-label">可用模型：</p>
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

      <!-- ======== Status Card ======== -->
      <div class="settings-card settings-status-card">
        <div class="card-header">
          <CheckCircle2 :size="20" aria-hidden="true" />
          <h2>当前生效配置</h2>
        </div>
        <div class="status-rows">
          <div class="status-row">
            <span class="status-label"><Bot :size="14" aria-hidden="true" /> 对话模型</span>
            <span class="status-value">{{ s.settings.value?.chat_provider === 'openai_compatible' ? (s.settings.value?.chat_preset ?? '自定义') : s.settings.value?.chat_provider }} / {{ s.settings.value?.chat_model ?? '默认' }}</span>
          </div>
          <div class="status-row">
            <span class="status-label"><Sparkles :size="14" aria-hidden="true" /> 嵌入模型</span>
            <span class="status-value">{{ s.settings.value?.embedding_provider === 'openai_compatible' ? (s.settings.value?.embedding_preset ?? '自定义') : s.settings.value?.embedding_provider }} / {{ s.settings.value?.embedding_model ?? '默认' }}</span>
          </div>
          <div class="status-row">
            <span class="status-label"><Server :size="14" aria-hidden="true" /> 向量存储</span>
            <span class="status-value">Chroma (LangChain)</span>
          </div>
          <div class="status-row">
            <span class="status-label"><Plug :size="14" aria-hidden="true" /> AI 编排</span>
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