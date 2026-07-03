import { computed, ref, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import type { ConversationPayload, ConversationSession } from '../types/conversations'
import type { WorkMode } from '../types/workspace'

const STORAGE_KEY = 'ai-study-agent.conversations.v1'

function defaultTitle(mode: WorkMode): string {
  const labelMap: Record<WorkMode, string> = {
    chat: '新建 Chat 对话',
    rag: '新建 RAG 对话',
    agent: '新建 Agent 对话',
  }
  return labelMap[mode]
}

function createBlankPayload(mode: WorkMode): ConversationPayload {
  if (mode === 'chat') {
    return {
      mode: 'chat',
      state: {
        messages: [],
        model: '',
        thinkingDepth: '标准',
        temperature: 0.7,
        keepContext: true,
        webSearch: true,
      },
    }
  }

  if (mode === 'rag') {
    return {
      mode: 'rag',
      state: {
        messages: [],
        selectedKnowledgeBaseIds: [],
        selectedQaLibraryIds: [],
        topK: 3,
      },
    }
  }

  return {
    mode: 'agent',
    state: {
      messages: [],
      selectedSkillId: '',
      selectedKnowledgeBaseId: '',
      selectedRoleId: '',
    },
  }
}

function loadSessions(): ConversationSession[] {
  if (typeof window === 'undefined') {
    return []
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw) as ConversationSession[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistSessions(sessions: ConversationSession[]) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

export const useConversationStore = defineStore('conversations', () => {
  const sessions = ref<ConversationSession[]>(loadSessions())
  const activeIds = ref<Record<WorkMode, string>>({
    chat: '',
    rag: '',
    agent: '',
  })
  const historyOverlayMode = shallowRef<WorkMode>('chat')
  const isHistoryOverlayOpen = shallowRef(false)
  const isSettingsOverlayOpen = shallowRef(false)

  const sortedSessions = computed(() =>
    [...sessions.value].sort((left, right) => {
      if (left.pinned !== right.pinned) {
        return left.pinned ? -1 : 1
      }
      return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
    }),
  )

  function sessionsForMode(mode: WorkMode) {
    return sortedSessions.value.filter((session) => session.mode === mode)
  }

  function getSession(sessionId: string) {
    return sessions.value.find((session) => session.id === sessionId) ?? null
  }

  function createSession(mode: WorkMode, payload: ConversationPayload): string {
    const sessionId = crypto.randomUUID()
    sessions.value = [
      {
        id: sessionId,
        mode,
        title: defaultTitle(mode),
        preview: '',
        titleManuallyEdited: false,
        pinned: false,
        updatedAt: new Date().toISOString(),
        payload,
      },
      ...sessions.value,
    ]
    activeIds.value = {
      ...activeIds.value,
      [mode]: sessionId,
    }
    persistSessions(sessions.value)
    return sessionId
  }

  function ensureSession(mode: WorkMode, payload: ConversationPayload) {
    const activeId = activeIds.value[mode]
    if (activeId && getSession(activeId)) {
      return activeId
    }

    const firstExisting = sessionsForMode(mode)[0]
    if (firstExisting) {
      activeIds.value = {
        ...activeIds.value,
        [mode]: firstExisting.id,
      }
      return firstExisting.id
    }

    return createSession(mode, payload)
  }

  function createBlankSession(mode: WorkMode) {
    return createSession(mode, createBlankPayload(mode))
  }

  function setActiveSession(mode: WorkMode, sessionId: string) {
    if (!getSession(sessionId)) {
      return
    }
    activeIds.value = {
      ...activeIds.value,
      [mode]: sessionId,
    }
  }

  function updateSession(
    sessionId: string,
    next: {
      title?: string
      preview?: string
      payload?: ConversationPayload
      pinned?: boolean
      titleManuallyEdited?: boolean
    },
  ) {
    sessions.value = sessions.value.map((session) =>
      session.id === sessionId
        ? {
            ...session,
            ...next,
            updatedAt: new Date().toISOString(),
          }
        : session,
    )
    persistSessions(sessions.value)
  }

  function togglePinned(sessionId: string) {
    const session = getSession(sessionId)
    if (!session) {
      return
    }
    updateSession(sessionId, { pinned: !session.pinned })
  }

  function renameSession(sessionId: string, title: string) {
    const normalizedTitle = title.trim()
    const session = getSession(sessionId)
    if (!session) {
      return
    }

    updateSession(sessionId, {
      title: normalizedTitle || defaultTitle(session.mode),
      titleManuallyEdited: normalizedTitle.length > 0,
    })
  }

  function deleteSession(mode: WorkMode, sessionId: string) {
    const remaining = sessions.value.filter((session) => session.id !== sessionId)
    sessions.value = remaining

    if (activeIds.value[mode] === sessionId) {
      const fallback = remaining.find((session) => session.mode === mode)
      activeIds.value = {
        ...activeIds.value,
        [mode]: fallback?.id ?? '',
      }
      if (!fallback) {
        createSession(mode, createBlankPayload(mode))
      }
    }

    persistSessions(sessions.value)
  }

  function openHistoryOverlay(mode: WorkMode) {
    historyOverlayMode.value = mode
    isHistoryOverlayOpen.value = true
  }

  function closeHistoryOverlay() {
    isHistoryOverlayOpen.value = false
  }

  function openSettingsOverlay() {
    isSettingsOverlayOpen.value = true
  }

  function closeSettingsOverlay() {
    isSettingsOverlayOpen.value = false
  }

  return {
    sessions,
    activeIds,
    historyOverlayMode,
    isHistoryOverlayOpen,
    isSettingsOverlayOpen,
    sortedSessions,
    sessionsForMode,
    getSession,
    createSession,
    createBlankSession,
    ensureSession,
    setActiveSession,
    updateSession,
    renameSession,
    togglePinned,
    deleteSession,
    openHistoryOverlay,
    closeHistoryOverlay,
    openSettingsOverlay,
    closeSettingsOverlay,
  }
})
