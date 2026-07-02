import {
  Book,
  BookMarked,
  BookOpenCheck,
  BrainCircuit,
  BrainCog,
  Database,
  Globe,
  Library,
  MessageCircleQuestion,
  ScrollText,
  UserCog,
  Workflow,
} from '@lucide/vue'
import type {
  FlashCard,
  KnowledgeDocument,
  ModeTab,
  NavItem,
  SourceSnippet,
  WorkMode,
} from '../types/workspace'

export const navItems: NavItem[] = [
  { id: 'workspace', label: 'AI 推理台', icon: Library, group: 'workspace' },
  { id: 'knowledge', label: '知识库管理', icon: BookMarked, group: 'resources' },
  { id: 'cards', label: 'QA 记忆卡片', icon: BrainCog, group: 'resources' },
  { id: 'history', label: '问答历史', icon: ScrollText, group: 'resources' },
]

export const modeTabs: ModeTab[] = [
  { id: 'chat', label: 'Chat', icon: MessageCircleQuestion },
  { id: 'rag', label: 'RAG', icon: BookOpenCheck },
  { id: 'agent', label: 'Agent', icon: Workflow },
]

export const chatSources: SourceSnippet[] = [
  {
    id: 'web-1',
    title: '什么是检索增强生成（RAG）？',
    source: 'ibm.com/cn-zh/topics',
    excerpt: 'RAG 通过检索外部知识提升生成答案的可靠性。',
  },
  {
    id: 'web-2',
    title: '大模型 RAG 技术详解与实践',
    source: 'zhihu.com/question',
    excerpt: '检索、排序和上下文注入是 RAG 的关键链路。',
  },
]

export const ragSources: SourceSnippet[] = [
  {
    id: 'chunk-1',
    title: '04-Redis持久化.md',
    source: '#chunk_8f1',
    score: '92%',
    marker: '1',
    excerpt: 'Redis 主要提供 RDB（快照持久化）和 AOF（追加文件持久化）。如果 Redis 意外宕机，RDB 会丢失最后一次快照之后的修改。',
  },
  {
    id: 'chunk-2',
    title: '04-Redis持久化.md',
    source: '#chunk_8f3',
    score: '87%',
    marker: '2',
    excerpt: 'AOF 的优点是数据安全性更高，可以配置为每秒同步。缺点是 AOF 文件通常比同等数据量的 RDB 文件大。',
  },
]

export const knowledgeBases = [
  { id: 'backend', label: '后端开发面试指南', icon: Book, active: true },
  { id: 'network', label: '计算机网络基础', icon: Book, active: false },
  { id: 'rag', label: '大模型 RAG 学习', icon: Book, active: false },
]

export const documents: KnowledgeDocument[] = [
  { id: 'redis', name: '04-Redis持久化机制.md', meta: '24 KB · 12 mins ago', status: '已索引 42 chunks', statusTone: 'success' },
  { id: 'mysql', name: 'MySQL_性能优化实战.pdf', meta: '2.1 MB · 1 hour ago', status: '切分中', statusTone: 'info' },
  { id: 'spring', name: 'SpringBoot 高频面试题.txt', meta: '86 KB · yesterday', status: '已索引 96 chunks', statusTone: 'success' },
]

export const flashCard: FlashCard = {
  tag: 'Redis 持久化',
  question: 'Redis 的持久化机制有哪些？它们分别有什么优缺点？',
  answer: [
    'RDB：在指定时间间隔将内存快照写入磁盘。优点是文件紧凑、恢复快；缺点是宕机时可能丢失最后一次快照后的数据。',
    'AOF：以日志方式记录每次写命令。优点是数据安全性高；缺点是文件体积更大，恢复速度慢于 RDB。',
  ],
}

export const modeSettings = {
  chat: [
    { label: '联网搜索', icon: Globe },
    { label: '深度: 标准', icon: BrainCircuit },
  ],
  rag: [
    { label: '已选知识库: 后端开发面试指南', icon: Library },
    { label: 'Top K: 3', icon: Database },
  ],
  agent: [
    { label: '教育专家', icon: UserCog },
    { label: '面试官', icon: MessageCircleQuestion },
    { label: '出题教练', icon: Workflow },
  ],
} satisfies Record<WorkMode, Array<{ label: string; icon: typeof Library }>>