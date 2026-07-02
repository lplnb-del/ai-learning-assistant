# 全能学习助理

全能学习助理是一个面向学生学习与求职准备场景的 AI 知识工作台。项目目标不是只做一个聊天窗口，而是通过高保真前端、RAG 知识库、问答卡片和 Agent 编排，展示完整 AI 应用工程能力。

## 当前路线

项目已重新基线为 **Vue 前端 + FastAPI 后端** 的前后端分离架构。

- 前端主线：Vue 3 + Vite + TypeScript + Tailwind CSS，目标是一比一还原 `prototype/index.html`。
- 后端主线：FastAPI + Python 服务层，承载 DeepSeek、RAG、Agent、知识库、文件解析和流式接口。
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
- DeepSeek OpenAI-compatible API
- LangChain / LangGraph
- SQLite
- Chroma
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
  llm/                    LLM Gateway
  knowledge/              知识库管理
  ingestion/              文档导入与切分
  rag/                    检索增强问答
  cards/                  问答卡片
  agent_capabilities/     Skills、MCP、SubAgent 能力层
  agents/                 Agent 编排
  storage/                SQLite / Chroma 适配

docs/                     PRD、架构、开发计划、UI 设计系统
prototype/index.html      高保真 UI 原型参考
tests/                    后端模型无关测试
```

## 开发状态

当前已完成正式 Vue 前端工程基线、高保真静态工作台、FastAPI 后端工程基线、Chat 前后端垂直闭环、Knowledge 导入基础闭环，以及 RAG 本地检索切片：`frontend/` 使用 Vue 3 + Vite + TypeScript + Tailwind CSS，接入 Vue Router、Pinia 和 @lucide/vue，并还原 Chat、RAG、Agent、Inspector、知识库和 QA 卡片视图；后端已提供 FastAPI app、CORS、统一错误响应、OpenAPI、`/api/health`、Chat 非流式接口、Chat SSE 流式接口、SQLite 知识库元数据表、知识库创建/列表/删除、Markdown/TXT 文本导入切分接口、PDF 文本抽取导入接口、URL 正文导入接口、索引准备入口和 RAG 本地 chunk 检索问答接口；RAG 已具备可替换的本地 hashing embedding provider、JSON 持久化向量索引适配层、cosine similarity 检索、prompt 组装、无命中兜底和来源片段展示。前端知识库页面已接入真实 API，可创建知识库、导入 Markdown/TXT/PDF/URL、查看 chunks、触发索引准备，并通过二次确认删除知识库或文档；RAG 页面可选择知识库、调整 Top K、使用固定演示问题提问、展示来源片段，并在无命中时给出兜底提示。Chat 页面可通过后端调用 DeepSeek Gateway，支持模型、温度、思考深度、上下文保留和联网搜索开关，其中联网搜索当前为接口字段与 UI 开关，后续再接真实搜索能力。旧 Streamlit UI 代码已清空。

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
- `POST /api/rag/ask`：基于知识库 chunks 做本地检索问答，返回回答、来源片段和 prompt 预览。

## 配置原则

- 真实密钥只允许放在本地 `.env` 或系统环境变量中。
- 禁止提交密钥、令牌、密码或隐私数据。
- 前端不得直接持有模型 API Key，所有模型调用必须通过后端 API。
