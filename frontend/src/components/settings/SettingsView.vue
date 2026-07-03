<script setup lang="ts">
import {
  Bot,
  CheckCircle2,
  Cpu,
  Globe,
  Loader2,
  PencilLine,
  Plus,
  Plug,
  RefreshCw,
  Save,
  Server,
  Sparkles,
  Trash2,
  Wand2,
  Wrench,
} from '@lucide/vue'
import { useSettingsManager } from '../../composables/useSettingsManager'
import FloatingPanel from '../shell/FloatingPanel.vue'
import PillSelect from '../workspace/PillSelect.vue'

const s = useSettingsManager()
</script>

<template>
  <section class="settings-view" aria-label="偏好设置">
    <header class="settings-header">
      <div class="settings-title-row">
        <Wand2 :size="22" aria-hidden="true" />
        <h1>偏好设置</h1>
      </div>
      <p class="settings-subtitle">模型、Subagent、MCP 与工作台 Skills 统一集中在这里维护。</p>
    </header>

    <div v-if="s.loading.value" class="settings-loading">
      <Loader2 :size="24" class="spin" aria-hidden="true" />
      <span>加载配置中...</span>
    </div>

    <div v-else-if="s.error.value" class="settings-error">
      {{ s.error.value }}
      <button type="button" class="btn-retry" @click="s.loadSettings">重试</button>
    </div>

    <div v-else class="settings-layout">
      <aside class="settings-nav" aria-label="设置分类">
        <button
          v-for="section in s.SETTINGS_SECTIONS"
          :key="section.id"
          type="button"
          class="settings-nav-item"
          :class="{ 'settings-nav-item-active': section.id === s.activeSection.value }"
          @click="s.selectSection(section.id)"
        >
          <strong>{{ section.label }}</strong>
          <span>{{ section.description }}</span>
        </button>
      </aside>

      <div class="settings-content">
        <section v-if="s.activeSection.value === 'models'" class="settings-section-stack">
          <div class="settings-grid">
            <div class="settings-card">
              <div class="card-header">
                <Bot :size="20" aria-hidden="true" />
                <h2>对话模型</h2>
              </div>
              <p class="card-desc">Chat / RAG / Agent 默认使用的对话模型。</p>

              <div class="form-group">
                <label>接入方式</label>
                <PillSelect v-model="s.chatProvider.value" label="对话模型接入方式" :options="s.PROVIDER_OPTIONS" variant="field" />
                <span class="form-hint">{{ s.PROVIDER_OPTIONS.find((item) => item.value === s.chatProvider.value)?.desc }}</span>
              </div>

              <div v-if="s.chatProvider.value === 'openai_compatible'" class="form-group">
                <label>预设服务</label>
                <PillSelect
                  :model-value="s.chatPreset.value"
                  label="对话模型预设服务"
                  :options="[{ value: '', label: '请选择或手动配置' }, ...s.chatPresetOptions.value.map((item) => ({ value: item.key, label: item.name }))]"
                  variant="field"
                  @update:model-value="s.applyChatPreset"
                />
              </div>

              <div v-if="s.chatProvider.value !== 'ollama'" class="form-group">
                <label>API Key</label>
                <input v-model="s.chatApiKey.value" type="password" class="form-input" placeholder="sk-..." />
              </div>

              <div class="form-group">
                <label>Base URL</label>
                <input
                  v-model="s.chatBaseUrl.value"
                  type="text"
                  class="form-input"
                  :placeholder="s.chatProvider.value === 'ollama' ? 'http://localhost:11434' : 'https://api.example.com/v1'"
                />
              </div>

              <div class="form-group">
                <label>模型名称</label>
                <div class="model-input-row">
                  <input v-model="s.chatModel.value" type="text" class="form-input" placeholder="模型 ID" />
                  <button type="button" class="btn-detect" :disabled="s.detecting.value" @click="s.runDetection('chat')">
                    <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
                    <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
                    检测模型
                  </button>
                </div>
              </div>

              <div v-if="s.detectedModels.value.length" class="detected-list">
                <p class="detected-label">可用模型：</p>
                <div class="detected-chips">
                  <button
                    v-for="modelItem in s.detectedModels.value"
                    :key="modelItem.id"
                    type="button"
                    class="model-chip"
                    :class="{ 'model-chip-active': s.chatModel.value === modelItem.id }"
                    @click="s.selectDetectedModel('chat', modelItem.id)"
                  >
                    <Cpu :size="14" aria-hidden="true" />
                    {{ modelItem.name }}
                  </button>
                </div>
              </div>

              <div class="card-footer">
                <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveChatConfig">
                  <Save :size="16" aria-hidden="true" />
                  保存对话配置
                </button>
              </div>
            </div>

            <div class="settings-card">
              <div class="card-header">
                <Sparkles :size="20" aria-hidden="true" />
                <h2>嵌入模型</h2>
              </div>
              <p class="card-desc">知识库文档向量化与 Chroma 检索使用的嵌入模型。</p>

              <div class="form-group">
                <label>接入方式</label>
                <PillSelect
                  v-model="s.embeddingProvider.value"
                  label="嵌入模型接入方式"
                  :options="s.EMBEDDING_PROVIDER_OPTIONS"
                  variant="field"
                />
                <span class="form-hint">{{ s.EMBEDDING_PROVIDER_OPTIONS.find((item) => item.value === s.embeddingProvider.value)?.desc }}</span>
              </div>

              <div v-if="s.embeddingProvider.value === 'openai_compatible'" class="form-group">
                <label>预设服务</label>
                <PillSelect
                  :model-value="s.embeddingPreset.value"
                  label="嵌入模型预设服务"
                  :options="[{ value: '', label: '请选择或手动配置' }, ...s.embeddingPresetOptions.value.map((item) => ({ value: item.key, label: item.name }))]"
                  variant="field"
                  @update:model-value="s.applyEmbeddingPreset"
                />
              </div>

              <div v-if="s.embeddingProvider.value !== 'ollama' && s.embeddingProvider.value !== 'huggingface'" class="form-group">
                <label>API Key</label>
                <input v-model="s.embeddingApiKey.value" type="password" class="form-input" placeholder="sk-..." />
              </div>

              <div v-if="s.embeddingProvider.value !== 'huggingface'" class="form-group">
                <label>Base URL</label>
                <input
                  v-model="s.embeddingBaseUrl.value"
                  type="text"
                  class="form-input"
                  :placeholder="s.embeddingProvider.value === 'ollama' ? 'http://localhost:11434' : 'https://api.example.com/v1'"
                />
              </div>

              <div class="form-group">
                <label>模型名称</label>
                <div class="model-input-row">
                  <input v-model="s.embeddingModel.value" type="text" class="form-input" placeholder="嵌入模型 ID" />
                  <button type="button" class="btn-detect" :disabled="s.detecting.value" @click="s.runDetection('embedding')">
                    <RefreshCw v-if="!s.detecting.value" :size="16" aria-hidden="true" />
                    <Loader2 v-else :size="16" class="spin" aria-hidden="true" />
                    检测模型
                  </button>
                </div>
              </div>

              <div class="card-footer">
                <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveEmbeddingConfig">
                  <Save :size="16" aria-hidden="true" />
                  保存嵌入配置
                </button>
              </div>
            </div>

            <div class="settings-card settings-status-card">
              <div class="card-header">
                <CheckCircle2 :size="20" aria-hidden="true" />
                <h2>当前生效配置</h2>
              </div>
              <div class="status-rows">
                <div class="status-row">
                  <span class="status-label"><Bot :size="14" aria-hidden="true" /> 对话模型</span>
                  <span class="status-value">{{ s.settings.value?.chat_provider }} / {{ s.settings.value?.chat_model ?? '默认' }}</span>
                </div>
                <div class="status-row">
                  <span class="status-label"><Sparkles :size="14" aria-hidden="true" /> 嵌入模型</span>
                  <span class="status-value">{{ s.settings.value?.embedding_provider }} / {{ s.settings.value?.embedding_model ?? '默认' }}</span>
                </div>
                <div class="status-row">
                  <span class="status-label"><Server :size="14" aria-hidden="true" /> 向量存储</span>
                  <span class="status-value">Chroma (LangChain)</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-else-if="s.activeSection.value === 'subagents'" class="settings-split-panel">
          <aside class="settings-subpanel-list">
            <div class="settings-subpanel-header">
              <strong>角色列表</strong>
              <button type="button" class="conversation-icon-button" aria-label="新增角色" @click="s.openCreateSubagent()">
                <Plus :size="15" aria-hidden="true" />
              </button>
            </div>
            <button
              v-for="role in s.subagents.value"
              :key="role.id"
              type="button"
              class="settings-subpanel-item"
              :class="{ 'settings-subpanel-item-active': role.id === s.selectedSubagentId.value }"
              @click="s.selectSubagent(role.id)"
            >
              <strong>{{ role.name }}</strong>
              <span>{{ role.description || '未填写角色使命' }}</span>
            </button>
          </aside>

          <div class="settings-card settings-detail-card">
            <template v-if="s.selectedSubagent.value">
              <div class="card-header">
                <Bot :size="20" aria-hidden="true" />
                <h2>{{ s.selectedSubagent.value.name }}</h2>
              </div>
              <p class="card-desc">{{ s.selectedSubagent.value.title }}</p>
              <div class="settings-detail-block">
                <span>角色使命</span>
                <p>{{ s.selectedSubagent.value.description || '未填写' }}</p>
              </div>
              <div class="settings-detail-block">
                <span>欢迎语</span>
                <p>{{ s.selectedSubagent.value.greeting || '未填写' }}</p>
              </div>
              <div class="settings-detail-block">
                <span>系统提示词</span>
                <pre>{{ s.selectedSubagent.value.system_prompt }}</pre>
              </div>
              <div v-if="s.selectedSubagent.value.tags.length" class="settings-tag-row">
                <span v-for="tag in s.selectedSubagent.value.tags" :key="tag" class="settings-tag-chip">{{ tag }}</span>
              </div>
              <div class="settings-editor-actions">
                <button type="button" class="btn-retry" @click="s.removeCurrentSubagent()">删除角色</button>
                <button type="button" class="btn-save" @click="s.openEditSubagent(s.selectedSubagent.value.id)">
                  <PencilLine :size="16" aria-hidden="true" />
                  编辑角色
                </button>
              </div>
            </template>
            <div v-else class="settings-empty-card">
              <p>还没有角色，点击左上角新增一个 Subagent。</p>
            </div>
          </div>
        </section>

        <section v-else-if="s.activeSection.value === 'mcp'" class="settings-split-panel">
          <aside class="settings-subpanel-list">
            <div class="settings-subpanel-header">
              <strong>MCP 服务</strong>
              <button type="button" class="conversation-icon-button" aria-label="新增 MCP" @click="s.openCreateMcp()">
                <Plus :size="15" aria-hidden="true" />
              </button>
            </div>
            <button
              v-for="server in s.mcpServers.value"
              :key="server.id"
              type="button"
              class="settings-subpanel-item"
              :class="{ 'settings-subpanel-item-active': server.id === s.editingMcpId.value }"
              @click="s.editingMcpId.value = server.id"
            >
              <strong>{{ server.name }}</strong>
              <span>{{ server.command || '未填写命令' }}</span>
            </button>
          </aside>

          <div class="settings-card settings-detail-card">
            <template v-if="s.selectedMcp.value">
              <div class="card-header">
                <Plug :size="20" aria-hidden="true" />
                <h2>{{ s.selectedMcp.value.name }}</h2>
              </div>
              <p class="card-desc">{{ s.selectedMcp.value.description || '未填写描述' }}</p>
              <div class="settings-detail-block">
                <span>启动命令</span>
                <pre>{{ s.selectedMcp.value.command || '未填写' }}</pre>
              </div>
              <div class="settings-summary-strip">
                <span><Plug :size="14" aria-hidden="true" /> {{ s.selectedMcp.value.enabled ? '当前启用中' : '当前未启用' }}</span>
              </div>
              <div class="settings-editor-actions">
                <button type="button" class="btn-retry" @click="s.removeMcpServer(s.selectedMcp.value.id)">删除 MCP</button>
                <button type="button" class="btn-save" @click="s.openEditMcp(s.selectedMcp.value.id)">
                  <PencilLine :size="16" aria-hidden="true" />
                  编辑 MCP
                </button>
              </div>
            </template>
            <div v-else class="settings-empty-card">
              <p>还没有 MCP 配置，点击左上角新增一个服务。</p>
            </div>
          </div>
        </section>

        <section v-else class="settings-split-panel">
          <aside class="settings-subpanel-list">
            <div class="settings-subpanel-header">
              <strong>工作台 Skills</strong>
              <button type="button" class="conversation-icon-button" aria-label="新增 Skill" @click="s.openCreateSkill()">
                <Plus :size="15" aria-hidden="true" />
              </button>
            </div>
            <button
              v-for="skill in s.skillSettings.value"
              :key="skill.id"
              type="button"
              class="settings-subpanel-item"
              :class="{ 'settings-subpanel-item-active': skill.id === s.selectedSkillId.value }"
              @click="s.selectSkill(skill.id)"
            >
              <strong>{{ skill.name }}</strong>
              <span>{{ skill.source || 'custom' }}</span>
            </button>
          </aside>

          <div class="settings-card settings-detail-card">
            <template v-if="s.selectedSkill.value">
              <div class="card-header">
                <Wrench :size="20" aria-hidden="true" />
                <h2>{{ s.selectedSkill.value.name }}</h2>
              </div>
              <p class="card-desc">{{ s.selectedSkill.value.description || '未填写描述' }}</p>
              <div class="settings-detail-block">
                <span>来源标识</span>
                <p>{{ s.selectedSkill.value.source }}</p>
              </div>
              <div v-if="s.selectedSkill.value.tags.length" class="settings-tag-row">
                <span v-for="tag in s.selectedSkill.value.tags" :key="tag" class="settings-tag-chip">{{ tag }}</span>
              </div>
              <label class="settings-switch-row">
                <div>
                  <strong>启用状态</strong>
                  <span>用于管理类似 `pdf`、`ppt`、`doc` 这类工作台技能。</span>
                </div>
                <input
                  type="checkbox"
                  :checked="s.selectedSkill.value.enabled"
                  @change="s.toggleSkill(s.selectedSkill.value.id, !s.selectedSkill.value.enabled)"
                />
              </label>
              <div class="settings-editor-actions">
                <button type="button" class="btn-retry" @click="s.removeCurrentSkill()">删除 Skill</button>
                <button type="button" class="btn-save" @click="s.openEditSkill(s.selectedSkill.value.id)">
                  <PencilLine :size="16" aria-hidden="true" />
                  编辑 Skill
                </button>
              </div>
            </template>
            <div v-else class="settings-empty-card">
              <p>目前还没有工作台 Skill，点击左上角新增例如 `pdf`、`ppt`、`doc` 之类的技能。</p>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div v-if="s.detectResult.value && !s.detectResult.value.success" class="detect-banner">
      <Globe :size="16" aria-hidden="true" />
      {{ s.detectResult.value.message }}
    </div>
  </section>

  <FloatingPanel
    v-if="s.isSubagentModalOpen.value"
    :title="s.selectedSubagentId.value ? '编辑角色' : '新增角色'"
    subtitle="在中心浮窗里完成角色信息与系统提示词编辑"
    size="large"
    @close="s.closeSubagentModal()"
  >
    <div class="settings-modal-stack">
      <div class="settings-editor-grid">
        <label class="form-group">
          <span>角色名称</span>
          <input v-model="s.subagentName.value" type="text" class="form-input" placeholder="例如：论文导师" />
        </label>
        <label class="form-group">
          <span>角色标题</span>
          <input v-model="s.subagentTitle.value" type="text" class="form-input" placeholder="例如：科研写作陪练" />
        </label>
      </div>

      <label class="form-group">
        <span>角色使命</span>
        <textarea v-model="s.subagentDescription.value" class="form-textarea" rows="3" placeholder="描述这个角色主要负责什么"></textarea>
      </label>

      <div class="settings-inline-actions">
        <label class="form-group settings-inline-grow">
          <span>AI 生成提示词参考</span>
          <input v-model="s.subagentMission.value" type="text" class="form-input" placeholder="例如：帮助用户拆解论文、检查逻辑并给出修改建议" />
        </label>
        <button type="button" class="btn-detect" :disabled="s.generatingPrompt.value" @click="s.autoGenerateSubagentPrompt()">
          <Loader2 v-if="s.generatingPrompt.value" :size="16" class="spin" aria-hidden="true" />
          <Wrench v-else :size="16" aria-hidden="true" />
          一键生成提示词
        </button>
      </div>

      <label class="form-group">
        <span>系统提示词</span>
        <textarea v-model="s.subagentPrompt.value" class="form-textarea form-textarea-prompt" rows="10" placeholder="角色系统提示词"></textarea>
      </label>

      <label class="form-group">
        <span>欢迎语</span>
        <textarea v-model="s.subagentGreeting.value" class="form-textarea" rows="2" placeholder="进入角色后的欢迎语"></textarea>
      </label>

      <label class="form-group">
        <span>标签</span>
        <input v-model="s.subagentTags.value" type="text" class="form-input" placeholder="用逗号分隔，例如：科研,写作,辅导" />
      </label>

      <div class="settings-editor-actions">
        <button v-if="s.selectedSubagentId.value" type="button" class="btn-retry" @click="s.removeCurrentSubagent()">
          <Trash2 :size="16" aria-hidden="true" />
          删除角色
        </button>
        <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveCurrentSubagent()">
          <Save :size="16" aria-hidden="true" />
          保存角色
        </button>
      </div>
    </div>
  </FloatingPanel>

  <FloatingPanel
    v-if="s.isMcpModalOpen.value"
    :title="s.editingMcpId.value ? '编辑 MCP' : '新增 MCP'"
    subtitle="通过中心浮窗维护 MCP 名称、说明和启动命令"
    @close="s.closeMcpModal()"
  >
    <div class="settings-modal-stack">
      <label class="form-group">
        <span>名称</span>
        <input v-model="s.mcpName.value" type="text" class="form-input" placeholder="例如：filesystem" />
      </label>
      <label class="form-group">
        <span>描述</span>
        <input v-model="s.mcpDescription.value" type="text" class="form-input" placeholder="这个 MCP 的作用" />
      </label>
      <label class="form-group">
        <span>启动命令</span>
        <input v-model="s.mcpCommand.value" type="text" class="form-input" placeholder="例如：npx @modelcontextprotocol/server-filesystem" />
      </label>
      <label class="settings-switch-row">
        <div>
          <strong>启用这个 MCP</strong>
          <span>保存后可在 Agent 配置中快捷启停。</span>
        </div>
        <input v-model="s.mcpEnabled.value" type="checkbox" />
      </label>
      <div class="settings-editor-actions">
        <button v-if="s.editingMcpId.value" type="button" class="btn-retry" @click="s.removeMcpServer(s.editingMcpId.value)">
          <Trash2 :size="16" aria-hidden="true" />
          删除 MCP
        </button>
        <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveCurrentMcp()">
          <Save :size="16" aria-hidden="true" />
          保存 MCP
        </button>
      </div>
    </div>
  </FloatingPanel>

  <FloatingPanel
    v-if="s.isSkillModalOpen.value"
    :title="s.selectedSkillId.value ? '编辑 Skill' : '新增 Skill'"
    subtitle="这里维护的是类似 pdf、ppt、doc 这类工作台技能，而不是 Agent 预设能力"
    @close="s.closeSkillModal()"
  >
    <div class="settings-modal-stack">
      <label class="form-group">
        <span>Skill 名称</span>
        <input v-model="s.skillName.value" type="text" class="form-input" placeholder="例如：pdf" />
      </label>
      <label class="form-group">
        <span>描述</span>
        <textarea v-model="s.skillDescription.value" class="form-textarea" rows="3" placeholder="这个 Skill 的主要用途"></textarea>
      </label>
      <div class="settings-editor-grid">
        <label class="form-group">
          <span>来源标识</span>
          <input v-model="s.skillSource.value" type="text" class="form-input" placeholder="例如：workspace / codex-skill / custom" />
        </label>
        <label class="form-group">
          <span>标签</span>
          <input v-model="s.skillTags.value" type="text" class="form-input" placeholder="用逗号分隔，例如：文档,pdf,导出" />
        </label>
      </div>
      <label class="settings-switch-row">
        <div>
          <strong>启用这个 Skill</strong>
          <span>关闭后仅保留配置，不在工作台中参与快捷选择。</span>
        </div>
        <input v-model="s.skillEnabled.value" type="checkbox" />
      </label>
      <div class="settings-editor-actions">
        <button v-if="s.selectedSkillId.value" type="button" class="btn-retry" @click="s.removeCurrentSkill()">
          <Trash2 :size="16" aria-hidden="true" />
          删除 Skill
        </button>
        <button type="button" class="btn-save" :disabled="s.saving.value" @click="s.saveCurrentSkill()">
          <Save :size="16" aria-hidden="true" />
          保存 Skill
        </button>
      </div>
    </div>
  </FloatingPanel>
</template>
