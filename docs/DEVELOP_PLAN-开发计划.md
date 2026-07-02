# DEVELOP PLAN：全能学习助理开发计划

## 1. 当前状态

- 项目正式路线已重订为 **Vue 前端 + FastAPI 后端**。
- 前端目标是一比一还原 `prototype/index.html`，不再用 Streamlit 作为正式 UI 主线。
- 后端目标是提供 FastAPI 接口，承载 DeepSeek、RAG、Agent、知识库、存储和流式输出。
- 已清空旧 Streamlit UI 代码。
- 已完成 Milestone 0-4：Vue 前端基线、高保真静态工作台、FastAPI 后端基线、Chat 前后端垂直闭环。
- Milestone 5 已完成基础闭环：SQLite 元数据表、知识库创建/列表/删除确认、Markdown/TXT/PDF/URL 导入、清洗切分、chunk 预览、索引准备入口和前端 API 接入。
- Milestone 6 已完成第一条本地检索切片：RAG 页面可选择知识库、调整 Top K、使用固定演示问题提问并展示来源片段；后端已有可替换的本地 hashing embedding provider、JSON 持久化向量索引适配层和 cosine similarity 检索；无检索结果时会给出兜底提示；后续继续把适配层替换为 Chroma 并接入模型生成。
- Milestone 7 已升级为“问答库 + 卡片”基础闭环：后端提供 `qa_libraries`、`qa_cards` SQLite 存储、问答库创建/列表/删除、卡片创建/列表/删除、掌握程度更新和按问答库/知识库/标签/掌握程度筛选；前端 QA 卡片页接入真实 API，支持按问答库管理卡片、手动创建、点击翻牌、掌握程度标记和删除；RAG 回答可选择参考问答库，并保存到指定问答库或在保存时直接新建问答库。

## 2. 技术栈

### 2.1 Frontend

- Vue 3
- Vite
- TypeScript
- Composition API + `<script setup lang="ts">`
- Tailwind CSS
- Vue Router
- Pinia
- @lucide/vue
- pnpm

前端原则：

- 组件小而聚焦，使用 PascalCase。
- 根组件和 route view 只做组合。
- 状态来源单一，派生状态用 `computed`。
- 组件通信默认 props down / events up。
- 复杂逻辑进入 composables；跨页面状态进入 Pinia。
- 不使用 `v-html` 渲染不可信内容。
- 前端不保存、不读取模型 API Key。

### 2.2 Backend

- Python 3.12
- FastAPI
- uv
- Pydantic schemas
- DeepSeek OpenAI-compatible API
- LangChain / LangGraph
- SQLite
- Chroma
- pytest

后端原则：

- API Key 只存在后端环境变量或本地 `.env`。
- Chat/RAG/Agent 流式输出使用 SSE。
- 业务能力在服务层，不写进路由函数。
- LangChain / LangGraph 渐进接入，不阻塞 MVP。

## 3. 架构决策

采用前后端分离：

```text
Vue Frontend
  -> REST / SSE
FastAPI Backend
  -> LLM Gateway / RAG / Agent / Storage
DeepSeek + SQLite + Chroma + LangChain/LangGraph
```

理由：

- Vue 更适合一比一还原高保真原型。
- FastAPI 更适合承载 AI 服务、密钥、文件处理、RAG 和 Agent。
- 前端不直接接触模型 Key，安全边界清晰。
- 该架构比 Streamlit 更接近正式 AI 产品工程。

## 4. 产品边界

- `Chat`：普通云端大模型会话，可有联网搜索开关、思考深度、模型选择和会话历史；不暴露 Skills、MCP、SubAgent 或知识库选择。
- `RAG`：围绕知识库问答、检索参数、来源片段和问答卡片；不暴露通用 Skills、MCP、SubAgent。
- `Agent`：开放学习角色 SubAgent、学习 Skills 和多步骤任务编排；取消 cowork、云端/本地工作场景入口，聚焦教育专家、面试官、出题教练、总结教练等可选角色模式。

## 5. Definition of Done

简历版完成标准：

- Vue 前端高保真还原原型主界面。
- FastAPI 后端可本地启动。
- Chat 支持真实模型调用和 SSE 流式输出。
- 支持知识库创建、资料导入、切分预览和向量索引。
- 支持 Markdown/TXT/PDF，URL 导入作为增强项。
- 支持基于知识库问答并展示来源片段。
- 支持问答卡片保存、翻牌和掌握程度标记。
- Agent 支持学习角色 SubAgent、学习 Skills、任务拆解、步骤跟踪和结果汇总。
- 有 README、架构图、演示截图、典型演示脚本和可复现运行方式。

## 6. 默认决策

- 第一批知识库资料：项目自身文档，包括 PRD、系统架构、开发计划、UI 设计系统和简历项目描述。
- PDF 导入节奏：Markdown/TXT 先跑通，PDF 放入简历版闭环。
- URL 导入节奏：第一版接受“抓取正文文本 + 失败原因提示”的简化方案。
- 问答卡片策略：先做“问答库 + 卡片”双层结构、掌握程度标记和保存入口，不做复杂间隔重复算法。
- Chat 联网搜索：第一版先做 UI 开关和接口桩。
- 思考深度：第一版映射到 prompt 策略和 max token，不绑定模型私有能力。
- Agent 角色模式：第一版优先实现教育专家和面试官，并复用 RAG 知识库和已有资料。
- 第一批 Skills：总结、解释、出题、生成问答卡片。
- 第一批 SubAgent：教育专家和面试官优先。

## 7. Milestone 0：文档重基线

目标：清空旧 Streamlit 主线进度，明确 Vue + FastAPI 正式路线。

任务：

- [x] 重写 README 技术栈与当前状态。
- [x] 重写 AGENTS 协作规则与项目结构。
- [x] 重写 PRD 实现决策。
- [x] 重写系统架构文档。
- [x] 重写开发计划。
- [x] 同步 UI 设计系统工程化要求。

验收：

- 新会话读取 `AGENTS.md`、`README.md`、`docs/PRD-全能学习助理.md`、`docs/DESIGN-系统架构.md`、`docs/DEVELOP_PLAN-开发计划.md` 后，不会继续把 Streamlit 当正式 UI 主线。
- 文档明确 Vue 是正式前端，FastAPI 是正式后端。
- 旧 Streamlit UI 代码已清空；保留的 DeepSeek Gateway 被描述为后端经验参考，而非新路线已完成进度。

## 8. Milestone 1：Vue 前端工程初始化

目标：创建正式前端工程基线。

任务：

- [x] 创建 `frontend/`。
- [x] 使用 Vite 初始化 Vue 3 + TypeScript。
- [x] 接入 Tailwind CSS。
- [x] 接入 Vue Router。
- [x] 接入 Pinia。
- [x] 接入 @lucide/vue。
- [x] 创建基础目录：`components/`、`views/`、`stores/`、`composables/`、`styles/`。
- [x] 定义设计 token：颜色、字体、阴影、圆角、动效。
- [x] 创建前端 `.env.example`，仅包含 `VITE_API_BASE_URL`。
- [x] 配置 lint / typecheck / build 脚本。

验收：

- `pnpm install` 成功。
- `pnpm dev` 可启动。
- `pnpm build` 通过。
- 页面显示空工作台壳。

## 9. Milestone 2：Vue 高保真静态工作台

目标：一比一还原原型主界面，不接后端。

任务：

- [x] 拆解 `prototype/index.html` 的布局、样式和交互。
- [x] 实现 `AppShell`。
- [x] 实现 `SidebarNav`。
- [x] 实现 `ModeTabs`。
- [x] 实现 `ModeTopBar`。
- [x] 实现 `ChatWorkspace`。
- [x] 实现 `RagWorkspace`。
- [x] 实现 `AgentWorkspace`。
- [x] 实现 `InspectorPanel`。
- [x] 实现 `KnowledgeView`。
- [x] 实现 `CardsView`。
- [x] 实现 light/dark `data-theme` 切换。
- [x] 使用假数据展示知识库、来源片段、卡片和 Agent log。

验收：

- 不接后端也能看出完整产品形态。
- 视觉上接近 `prototype/index.html`。
- Chat 不展示知识库、Skills、MCP、SubAgent。
- RAG 不展示通用 Skills、MCP、SubAgent。
- Agent 展示学习角色 SubAgent、学习 Skills、任务步骤和执行日志，不展示 cowork、云端/本地场景。

## 10. Milestone 3：FastAPI 后端工程基线

目标：建立后端 API 壳和前后端契约。

任务：

- [x] 创建 `src/ai_study_agent/api/main.py`。
- [x] 创建 routers：chat、knowledge、rag、cards、agents。
- [x] 创建 Pydantic schemas。
- [x] 配置 CORS。
- [x] 暴露 `/api/health`。
- [x] 保留并整理 DeepSeek Gateway。
- [x] 定义统一错误响应。
- [x] 更新 README 启动方式。

验收：

- `uv run uvicorn ai_study_agent.api.main:app --reload` 可启动。
- `/api/health` 返回正常。
- OpenAPI 文档可访问。
- 后端测试通过。

## 11. Milestone 4：Chat 前后端垂直闭环

目标：Vue 调 FastAPI，FastAPI 调 DeepSeek，并流式返回。

任务：

- [x] 后端实现 Chat 非流式接口。
- [x] 后端实现 Chat SSE 流式接口。
- [x] 前端实现 API client。
- [x] 前端实现 `useChatStream`。
- [x] Chat 页面接入后端 SSE 流式输出。
- [x] 支持模型、温度、思考深度、上下文保留。
- [x] 缺少 Key、网络失败、模型报错时友好提示。

验收：

- Vue 页面输入问题后通过 FastAPI Chat SSE 接口获得模型回复。
- 流式输出可见。
- 前端不接触 API Key。
- Chat 无知识库、Skills、MCP、SubAgent 入口。
- 已完成模型无关自动化验证；真实 DeepSeek 请求属于外部服务调用，需要用户确认后再执行联调验收。

## 12. Milestone 5：Knowledge 导入、切分与元数据

目标：完成知识库管理和资料处理链路，为 RAG 做数据准备。

任务：

- [x] SQLite 初始化和基础迁移策略。
- [x] 知识库创建、列表、选择、删除确认。
- [x] Markdown/TXT 导入。
- [x] 文档文本抽取、清洗和基础元数据记录。
- [x] chunk size、chunk overlap、标题/段落切分策略。
- [x] chunk 预览和重建索引入口。
- [x] 保存 source document、chunk 元数据和导入状态。
- [x] PDF 文本抽取。
- [x] URL 正文抽取和失败原因保存。

验收：

- 能在前端创建知识库并导入 Markdown/TXT/PDF。
- 能在前端看到切分后的 chunks。
- 能在前端触发索引准备，并看到文档数和 chunk 数反馈。
- 导入失败时能看到原因，且不影响 Chat。
- SQLite 中能查到知识库、文档和 chunk 元数据。
- PDF 导入可在前端选择文件，由后端本地抽取文本并切分。

## 13. Milestone 6：RAG 垂直闭环

目标：让知识库真正可问答，并能解释答案来源。

任务：

- [x] 接入本地 Embedding Provider。
- [x] 创建本地向量索引适配层和持久化目录。
- [x] 重建索引时写入 embedding。
- [x] 实现本地关键词检索切片。
- [x] 实现本地 similarity search。
- [x] 实现 RAG prompt 组装。
- [x] RAG 页面接入真实问答。
- [x] 展示来源片段、文档名、chunk 序号、检索分数。
- [x] 增加无检索结果兜底。
- [x] 实现 RAG 顶部设置栏。
- [x] 准备至少 3 个固定演示问题。

验收：

- 能选择知识库提问。
- 回答基于资料生成，并展示来源片段。
- 调整 top_k、阈值、回答风格后 UI 状态清晰。
- RAG 不展示通用 Skills/MCP/SubAgent 入口。

## 14. Milestone 7：QA Library 问答库与卡片

目标：形成学习产品差异化能力，把问答沉淀为可管理、可复习、可参与 RAG 的问答资产层。

任务：

- [x] 设计并实现 `qa_libraries`、`qa_cards` 存储。
- [x] 支持问答库创建、列表、删除。
- [x] 支持把 RAG 问答保存到指定问答库。
- [x] 支持保存时直接新建问答库。
- [x] 支持手动创建问答卡片。
- [x] 支持从 RAG 结果生成问答卡片。
- [x] 支持卡片翻牌。
- [x] 支持掌握程度标记。
- [x] 支持按问答库、知识库、标签、掌握程度筛选。
- [x] 支持 RAG 选择参与参考的问答库。
- [x] 支持直接从单个 chunk 生成候选问答卡片。
- [x] 支持直接从整篇知识库文档批量生成候选问答卡片。
- [ ] 增加更完整的复习队列策略和下一次复习时间。
- [ ] 支持多知识库联合检索，而不是当前的单知识库 + 多问答库。

## 15. Milestone 8：Agent Capability Layer

目标：把 Skills、MCP Tools、SubAgents 统一收束在 Agent 专用能力层。

任务：

- [ ] Capability 基础接口。
- [ ] Capability Registry。
- [ ] Skill Registry。
- [ ] 基础 Skills：总结、解释、出题、生成问答卡片。
- [ ] MCP Tool Adapter 接口桩。
- [ ] SubAgent 基础接口。
- [ ] Education Expert SubAgent。
- [ ] Interviewer SubAgent。
- [ ] Quiz Coach SubAgent。
- [ ] Summary Coach SubAgent。

## 16. Milestone 9：Agent 模式编排

目标：实现多步骤任务编排，而不是简单 SubAgent 列表。

任务：

- [ ] Agent Planner。
- [ ] LangGraph 状态图。
- [ ] 任务步骤状态：pending、running、done、failed。
- [ ] Agent 可调用 Capability Layer。
- [ ] Agent 可组合 RAG、Skills、MCP、SubAgent。
- [ ] Agent 支持学习规划、模拟面试、出题练习、资料总结等学习任务。
- [ ] Agent 支持选择教育专家、面试官、出题教练、总结教练等角色模式。
- [ ] Agent 页面展示计划、执行过程、工具调用、观察结果和最终汇总。

## 17. Milestone 10：工程化与简历交付

目标：让项目可复现、可演示、可写进简历。

任务：

- [ ] 完善 README。
- [ ] 增加架构图和运行截图。
- [ ] 增加演示脚本。
- [ ] 增加基础测试：chunk 切分、配置读取、RAG prompt、卡片存储、模式边界、API schema。
- [ ] 增加示例资料和演示问题。
- [ ] 更新简历项目描述，确保与真实完成状态一致。
- [ ] 整理 commit 历史和版本标签。

## 18. 推荐提交顺序

1. `docs: reset architecture to vue fastapi`
2. `chore: scaffold vue frontend`
3. `feat: recreate prototype shell in vue`
4. `feat: add fastapi backend shell`
5. `feat: connect vue chat to fastapi stream`
6. `feat: add knowledge ingestion pipeline`
7. `feat: add rag question answering`
8. `feat: add qa cards workflow`
9. `feat: add agent capability layer`
10. `feat: add agent orchestration`
11. `docs: add demo guide and resume evidence`

每次提交前执行：

- Code review：检查 diff 是否符合三模式边界、密钥安全、Vue 组件边界和 UI 设计系统。
- Code simplify：删除临时文件、死代码和未使用 mock。
- 文档同步：功能状态变化后更新 README、开发计划或简历证据。
- 验证：前端运行 build/typecheck，后端运行模型无关测试。

## 19. 新会话启动清单

1. 读取 `AGENTS.md`。
2. 读取 `README.md`。
3. 读取 `docs/PRD-全能学习助理.md`。
4. 读取 `docs/DESIGN-系统架构.md`。
5. 读取 `docs/DEVELOP_PLAN-开发计划.md`。
6. 查看 `prototype/index.html`，确认 UI 视觉基准。
7. 执行 `git status --short`，确认当前工作区。
8. 从 Milestone 1：Vue 前端工程初始化开始实现。
