# 全能学习助理

全能学习助理是一个面向学生学习与求职准备场景的 AI 知识工作台。项目目标不是只做一个聊天窗口，而是通过高保真前端、RAG 知识库、问答卡片和 Agent 编排，展示完整 AI 应用工程能力。

## 当前路线

项目已重新基线为 **Vue 前端 + FastAPI 后端** 的前后端分离架构。

- 前端主线：Vue 3 + Vite + TypeScript + Tailwind CSS，目标是一比一还原 `prototype/index.html`。
- 后端主线：FastAPI + Python 服务层，承载 DeepSeek、RAG、Agent、知识库、文件解析和流式接口。RAG 链路全面采用 LangChain 生态：TextSplitter 切分、Chroma 向量库、LangChain Embeddings、LangChain Chat Model。
- AI 编排：LangChain / LangGraph 放在后端渐进接入。
- Streamlit：旧 UI 代码已从新主线移除；历史提交仅作为验证记录。

## 核心模式

- `Chat`：普通云端大模型会话，可包含联网搜索开关、思考深度、模型选择和会话历史；不暴露 Skills、MCP、SubAgent 或知识库选择。
- `RAG`：围绕知识库问答、检索参数、来源片段和问答卡片；不暴露通用 Skills、MCP、SubAgent。
- `Agent`：开放学习角色 SubAgent、学习 Skills 和多步骤任务编排；取消 cowork、云端/本地工作场景入口，聚焦教育专家、面试官、出题教练、总结教练等可选角色模式。

## 技术栈

### Frontend

- Vue 3
- Vite
- TypeScript
- Composition API + `<script setup lang="ts">`
- Tailwind CSS
- Vue Router
- Pinia
- @lucide/vue
- pnpm

### Backend

- Python 3.12
- FastAPI
- uv
- DeepSeek OpenAI-compatible API (via langchain-openai)
- LangChain（langchain-text-splitters、langchain-openai）
- LangChain Community（Chroma 集成）
- LangGraph（Agent 编排）
- Chroma（向量存储）
- SQLite（元数据存储）
- pytest

## 目标结构

```text
frontend/
  src/
    app/
    assets/
    components/
    composables/
    stores/
    styles/
    views/

src/ai_study_agent/
  api/                    FastAPI app、routers、schemas
  core/                   配置、领域类型、服务接口
  llm/                    LLM Gateway（LangChain Chat Model）
  knowledge/              知识库管理
  ingestion/              文档导入与切分
  rag/                    检索增强问答（LangChain RetrievalQA + Chroma）
  cards/                  问答卡片
  agent_capabilities/     Skills、MCP、SubAgent 能力层
  agents/                 Agent 编排
  storage/                SQLite / Chroma 适配

docs/                     PRD、架构、开发计划、UI 设计系统
prototype/index.html      高保真 UI 原型参考
tests/                    后端模型无关测试
```

## 开发状态

当前已完成正式 Vue 前端工程基线、高保真静态工作台、FastAPI 后端工程基线、Chat 前后端垂直闭环、Knowledge 导入基础闭环、RAG 本地检索切片，以及 QA Library 问答库基础闭环：`frontend/` 使用 Vue 3 + Vite + TypeScript + Tailwind CSS，接入 Vue Router、Pinia 和 @lucide/vue，并还原 Chat、RAG、Agent、Inspector、知识库和 QA 卡片视图；后端已提供 FastAPI app、CORS、统一错误响应、OpenAPI、`/api/health`、Chat 非流式接口、Chat SSE 流式接口、SQLite 知识库元数据表、知识库创建/列表/删除、Markdown/TXT/PDF/URL 文档导入切分、索引准备入口、RAG 本地 chunk 检索问答接口，以及 `qa_libraries` / `qa_cards` 问答库存储接口；RAG 已完成 LangChain + Chroma 全面升级：使用 LangChain TextSplitter 做文档切分、LangChain Embeddings 做向量化、Chroma 做向量存储和检索、LangChain Chat Model 做 LLM 调用，保留问答库匹配和知识库-问答库混合检索能力。前端知识库页面已接入真实 API，可创建知识库、导入资料、查看 chunks、触发索引准备，并通过二次确认删除知识库或文档；RAG 页面可选择多个知识库联合检索、调整 Top K、勾选参考问答库、使用固定演示问题提问、展示来源片段，并可把回答保存到指定问答库或在保存时直接新建问答库；QA 卡片页已升级为“问答库 -> 卡片”结构，可创建问答库、按问答库管理卡片、按知识库/标签/掌握程度筛选、点击翻牌、标记掌握程度和删除卡片。Chat 页面可通过后端调用 DeepSeek Gateway，支持模型、温度、思考深度、上下文保留和联网搜索开关，其中联网搜索当前为接口字段与 UI 开关，后续再接真实搜索能力。Agent 方向已收敛为学习角色模式，聚焦教育专家、面试官、出题教练、总结教练等可选角色；已实现 Capability Layer 基础闭环，内置 4 个学习 Skills（总结提炼、概念解释、出题练习、生成问答卡片）和 4 个角色模式（教育专家、面试官、出题教练、总结教练），支持选择角色、知识库上下文辅助执行，前端 Agent 工作台已从静态 mock 升级为真实交互。旧 Streamlit UI 代码已清空。

## 本地启动

前端：

```bash
cd frontend
pnpm dev
```

后端：

```bash
uv run uvicorn ai_study_agent.api.main:app --reload
```

默认地址：

- 前端：`http://localhost:5173/`
- 后端健康检查：`http://127.0.0.1:8000/api/health`
- OpenAPI：`http://127.0.0.1:8000/docs`

前端默认请求 `http://localhost:8000`；如后端端口变化，可在 `frontend/.env` 设置 `VITE_API_BASE_URL`。

Knowledge 当前支持：

- `POST /api/knowledge/bases`：创建知识库。
- `GET /api/knowledge/bases`：列出知识库。
- `DELETE /api/knowledge/bases/{knowledge_base_id}`：删除知识库及其文档/chunks。
- `POST /api/knowledge/bases/{knowledge_base_id}/documents/import-text`：导入 Markdown/TXT 文本并返回 chunks。
- `POST /api/knowledge/bases/{knowledge_base_id}/documents/import-pdf`：导入 PDF，后端抽取文本并返回 chunks。
- `POST /api/knowledge/bases/{knowledge_base_id}/documents/import-url`：抓取公开 URL 正文并返回 chunks。
- `GET /api/knowledge/bases/{knowledge_base_id}/documents`：列出知识库文档。
- `POST /api/knowledge/bases/{knowledge_base_id}/index/rebuild`：写入本地持久化向量索引，返回文档数和 chunk 数。
- `GET /api/knowledge/documents/{document_id}/chunks`：查看文档 chunks。
- `DELETE /api/knowledge/documents/{document_id}`：删除文档及其 chunks。
- `POST /api/rag/ask`：基于一个或多个知识库 chunks 做本地检索问答，支持多知识库联合检索，返回回答、来源片段和 prompt 预览。
- `POST /api/cards/libraries`：创建问答库。
- `GET /api/cards/libraries`：列出问答库。
- `DELETE /api/cards/libraries/{library_id}`：删除问答库。
- `POST /api/cards`：创建 QA 记忆卡片，可关联问答库、知识库、来源 chunks 和标签。
- `GET /api/cards`：按问答库、知识库、掌握程度或标签筛选卡片。
- `PATCH /api/cards/{card_id}/mastery`：更新卡片掌握程度。
- `DELETE /api/cards/{card_id}`：删除卡片。
- `POST /api/cards/generate-from-chunks`：从指定 chunks 批量生成候选问答卡片。
- `POST /api/cards/generate-from-document`：从指定文档的所有 chunks 批量生成候选问答卡片。
- `GET /api/cards/{card_id}/sources`：追溯问答卡片关联的知识库来源切片。

## 配置原则

- 真实密钥只允许放在本地 `.env` 或系统环境变量中。
- 禁止提交密钥、令牌、密码或隐私数据。
- 前端不得直接持有模型 API Key，所有模型调用必须通过后端 API。
