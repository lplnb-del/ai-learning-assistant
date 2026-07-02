import {
  Book,
  BookMarked,
  BookOpenCheck,
  BrainCircuit,
  BrainCog,
  Cloud,
  Database,
  Globe,
  Layers,
  Library,
  MessageCircleQuestion,
  Network,
  ScrollText,
  UserCog,
  Workflow,
} from '@lucide/vue'
import type {
  AgentStep,
  FlashCard,
  KnowledgeDocument,
  MainView,
  MessageBlock,
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

export const viewTitles: Record<MainView, string> = {
  workspace: 'AI 推理台',
  knowledge: '知识库管理',
  cards: 'QA 记忆卡片',
  history: '问答历史',
}

export const chatMessages: MessageBlock[] = [
  {
    role: 'user',
    content: ['能不能帮我解释一下什么是 RAG？尽量通俗一点，最好结合生活中的例子。'],
  },
  {
    role: 'assistant',
    status: '已思考 2.4 秒，查阅了 3 个网页',
    title: '生活中的例子：开卷考试',
    content: [
      'RAG（检索增强生成）是一种让 AI 回答前先翻资料的技术。普通 Chat 像闭卷考试，只能凭已有记忆作答。',
      'RAG 更像开卷考试：你给它一批可信资料，它先检索相关段落，再把检索结果和问题一起交给大模型组织答案。',
      '简单公式：RAG = 外部知识检索 + 大模型归纳总结。它很适合处理课程资料、论文、项目文档和企业内部知识。',
    ],
  },
]

export const ragMessages: MessageBlock[] = [
  {
    role: 'user',
    content: ['基于资料，Redis 的持久化机制有哪些？它们分别有什么优缺点？'],
  },
  {
    role: 'assistant',
    status: '已检索本地库，命中 4 个片段，耗时 0.8s',
    title: 'Redis 持久化机制',
    content: [
      'Redis 主要提供 RDB、AOF 和 Redis 4.0 之后的混合持久化。RDB 是快照，文件紧凑且恢复快，但意外宕机时可能丢失最后一次快照之后的数据。[1]',
      'AOF 会记录写命令，数据安全性更高，可配置为每秒同步，但文件通常更大，恢复速度慢于 RDB。[2]',
      '在面试回答里，可以按“机制 -> 优点 -> 缺点 -> 适用场景”的顺序展开，再补充混合持久化作为加分项。',
    ],
  },
]

export const agentSteps: AgentStep[] = [
  {
    id: 'plan',
    title: '任务拆解与规划',
    detail: '生成 3 个子任务：检索本地 RAG 文档、联网补充 LangChain 最佳实践、注入教育专家角色输出路线。',
    status: 'completed',
    icon: Network,
    tone: 'purple',
  },
  {
    id: 'rag',
    title: '调用知识库检索',
    detail: '命中 2 个文档片段，提取核心术语：向量数据库、Chunking 策略、召回率优化。',
    status: 'completed',
    icon: Database,
    tone: 'blue',
  },
  {
    id: 'web',
    title: '调用联网搜索',
    detail: '读取 4 个技术博客，抓取 LangChain LCEL 与 Agent 编排相关实践。',
    status: 'completed',
    icon: Globe,
    tone: 'blue',
  },
  {
    id: 'subagent',
    title: '教育专家生成学习路线',
    detail: '正在把资料、检索结果和学习目标整理为 4 周路线。',
    status: 'running',
    icon: UserCog,
    tone: 'red',
  },
]

export const agentAnswer = [
  '结合你的本地 RAG 知识体系以及最新行业实践，我为你整理了一套《大模型应用开发 4 周进阶路线》。',
  'W1：夯实基础，掌握 DeepSeek/OpenAI 兼容接口、流式输出、Prompt 结构化表达。',
  'W2：深入 RAG，理解文本切分、向量数据库、Top-K、召回率和来源引用展示。',
  'W3：接入 LangChain/LangGraph，把工具调用、状态图和 Agent 计划拆成可验证步骤。',
  'W4：工程化交付，补齐 FastAPI 接口、前端高保真体验、测试、README 和演示脚本。',
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

export const decks = [
  { id: 'backend', label: '后端面试必刷', count: 42, icon: Layers, active: true },
  { id: 'network', label: '计网八股文', count: 15, icon: Layers, active: false },
  { id: 'rag', label: '大模型 RAG 基础', count: 8, icon: Layers, active: false },
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
    { label: '深度研究模式', icon: Workflow },
    { label: '教育专家', icon: UserCog },
    { label: '云端沙箱', icon: Cloud },
  ],
} satisfies Record<WorkMode, Array<{ label: string; icon: typeof Library }>>
