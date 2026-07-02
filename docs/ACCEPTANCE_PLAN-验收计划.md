# ACCEPTANCE PLAN：现有成果验收计划

## 1. 验收目标

本计划用于验收当前已完成的“AI Learning Assistant / 全能学习助理”阶段成果，重点确认：

- Vue 前端可启动、可构建，页面符合 Chat / RAG / Agent 三模式边界。
- FastAPI 后端可启动，健康检查和 OpenAPI 正常。
- Chat 支持后端代理模型调用和 SSE 流式输出。
- Knowledge 支持知识库创建、文档导入、切分预览、索引重建和删除。
- RAG 支持基于知识库的本地检索问答，并展示来源片段。
- 密钥、简历和本地数据不会进入公开仓库。

## 2. 验收前准备

### 2.1 环境检查

在项目根目录执行：

```bash
git status --short
python --version
uv --version
pnpm --version
```

通过标准：

- `git status --short` 不应出现非预期改动。
- Python 建议为 3.12。
- `uv` 和 `pnpm` 可以正常输出版本号。

### 2.2 配置检查

确认本地存在 `.env`，并至少配置：

```bash
DEEPSEEK_API_KEY=你的本地密钥
```

通过标准：

- `.env` 不出现在 `git status --short` 中。
- 前端没有任何模型 API Key 配置。
- 公开仓库只包含 `.env.example`，不包含真实密钥。

## 3. 自动化验证

### 3.1 后端测试

在项目根目录执行：

```bash
uv run pytest -q
uv run python -m compileall -q src tests
```

通过标准：

- pytest 全部通过。
- compileall 无报错。
- 当前基线预期至少通过 35 个后端测试。

### 3.2 前端验证

在项目根目录执行：

```bash
pnpm --dir frontend lint
pnpm --dir frontend typecheck
pnpm --dir frontend build
```

通过标准：

- ESLint 无错误。
- TypeScript 类型检查无错误。
- Vite production build 成功生成 `frontend/dist/`。

### 3.3 GitHub 公开内容检查

执行：

```bash
git ls-files .env docs/实习简历-李鹏亮.md
git check-ignore -v .env docs/实习简历-李鹏亮.md
git remote -v
```

通过标准：

- `git ls-files` 对 `.env` 和简历文件无输出。
- `git check-ignore` 显示 `.env` 和简历被 `.gitignore` 命中。
- `origin` 指向 `https://github.com/lplnb-del/ai-learning-assistant.git`。

## 4. 本地启动验收

### 4.1 启动后端

在项目根目录执行：

```bash
uv run uvicorn ai_study_agent.api.main:app --reload
```

访问：

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`

通过标准：

- 健康检查返回正常状态。
- OpenAPI 页面可打开，并能看到 Chat、Knowledge、RAG 等接口分组。

### 4.2 启动前端

新开终端执行：

```bash
cd frontend
pnpm dev
```

访问：

- `http://localhost:5173/`

通过标准：

- 页面正常打开。
- 左侧导航、模式切换、主工作区和 Inspector 可见。
- 无明显样式错位、遮挡、横向溢出或空白主界面。

## 5. 前端页面验收

### 5.1 Chat 模式

检查内容：

- Chat 页面展示模型、温度、思考深度、上下文保留、联网搜索开关等配置。
- 输入框可输入问题并发送。
- 页面不展示知识库选择、Skills、MCP、SubAgent 入口。

通过标准：

- Chat 只体现普通云端模型会话能力。
- 发送问题后可看到用户消息和助手回复。
- 后端缺少 Key 或模型请求失败时，页面给出友好错误提示。

### 5.2 RAG 模式

检查内容：

- RAG 页面可选择知识库。
- 可调整 Top K。
- 可使用固定演示问题。
- 可展示来源片段、文档名、chunk 序号和检索分数。
- 页面不展示通用 Skills、MCP、SubAgent 入口。

通过标准：

- RAG 只围绕知识库问答、检索参数和来源解释。
- 无知识库或无 chunk 时，有明确提示。
- 有命中来源时，回答区域和来源区域都可读。

### 5.3 Agent 模式

检查内容：

- Agent 页面展示教育专家、面试官、出题教练、总结教练等学习角色入口或状态。
- Agent 当前可作为规划中能力展示，不要求完整后端编排闭环。

通过标准：

- Agent 与 Chat / RAG 的能力边界清晰。
- 未完成能力不应伪装成已完成真实调用。
- 页面不展示 cowork、云端沙箱、本地工作场景等入口。

### 5.4 Knowledge 页面

检查内容：

- 可创建知识库。
- 可导入 Markdown/TXT 文本。
- 可导入 PDF 文件。
- 可导入 URL。
- 可查看文档列表和 chunks。
- 可触发索引重建。
- 删除知识库或文档前有二次确认。

通过标准：

- 成功导入后能看到文档和 chunk 预览。
- 导入失败时显示失败原因，不影响其它页面使用。
- 索引重建后返回文档数和 chunk 数。

## 6. 后端接口验收

可在 OpenAPI 页面或 curl 中验证。

### 6.1 Health

接口：

```text
GET /api/health
```

通过标准：

- 返回 200。
- 响应体包含正常状态。

### 6.2 Chat

接口：

```text
POST /api/chat
POST /api/chat/stream
```

通过标准：

- 非流式接口能返回完整回答。
- SSE 接口能分段返回内容。
- 未配置 Key 时返回可理解的错误，不泄露密钥。

### 6.3 Knowledge

接口：

```text
POST /api/knowledge/bases
GET /api/knowledge/bases
POST /api/knowledge/bases/{knowledge_base_id}/documents/import-text
POST /api/knowledge/bases/{knowledge_base_id}/documents/import-pdf
POST /api/knowledge/bases/{knowledge_base_id}/documents/import-url
GET /api/knowledge/bases/{knowledge_base_id}/documents
GET /api/knowledge/documents/{document_id}/chunks
POST /api/knowledge/bases/{knowledge_base_id}/index/rebuild
DELETE /api/knowledge/documents/{document_id}
DELETE /api/knowledge/bases/{knowledge_base_id}
```

通过标准：

- 知识库、文档、chunk 元数据能写入 SQLite。
- Markdown/TXT/PDF/URL 至少各完成一次成功或明确失败原因验证。
- 索引重建会写入本地 JSON 向量索引。

### 6.4 RAG

接口：

```text
POST /api/rag/ask
```

通过标准：

- 有知识库和 chunks 时返回回答。
- 返回 `sources`、`prompt_preview`、`retrieval_mode`。
- 重建索引后优先使用 `local_vector_index`。
- 无命中时给出兜底回答，不伪造来源。

## 7. 推荐手动验收脚本

### 7.1 知识库样本文本

创建知识库：`项目说明资料库`

导入 Markdown/TXT 内容：

```markdown
# AI Learning Assistant

AI Learning Assistant 是一个面向学生学习和求职准备场景的 AI 知识工作台。
项目采用 Vue3 + FastAPI 前后端分离架构，支持 Chat、RAG 和 Agent 三种模式。
RAG 模式会先检索知识库资料，再根据来源片段组织回答。
```

导入后操作：

1. 查看 chunks。
2. 点击重建索引。
3. 切换到 RAG 页面。
4. 选择该知识库。
5. 提问：`这个项目采用什么架构？`

通过标准：

- 回答应提到 Vue3 + FastAPI 前后端分离架构。
- 来源片段应来自刚导入的文档。
- 检索分数、文档名和 chunk 序号可见。

### 7.2 Chat 样本问题

提问：

```text
用三句话解释 RAG 和普通 Chat 的区别。
```

通过标准：

- 如果已配置 `DEEPSEEK_API_KEY`，应看到流式回复。
- 如果未配置 Key，应看到明确的配置提示。
- 前端控制台不应出现未捕获异常。

## 8. 安全与隐私验收

检查内容：

- `.env` 不被 Git 追踪。
- `docs/实习简历-李鹏亮.md` 不被 Git 追踪。
- 前端代码中没有真实 API Key。
- README 和文档不包含真实密钥、令牌或隐私凭证。
- 模型调用只经过后端。

通过标准：

- `git ls-files .env docs/实习简历-李鹏亮.md` 无输出。
- 搜索 `DEEPSEEK_API_KEY` 时，只应出现在 `.env.example`、配置读取或文档说明中，不应出现真实值。

## 9. 当前不验收或只做展示的内容

以下能力属于后续 Milestone，不作为本轮通过条件：

- Chroma 真正向量库接入。
- LangChain / LangGraph 编排落地。
- QA Cards 存储和复习闭环。
- Agent Capability Layer 后端真实执行。
- MCP Tool Adapter 和 SubAgent 实际调用。
- 生产环境部署。

## 10. 验收记录模板

| 模块 | 结果 | 备注 |
| --- | --- | --- |
| 后端测试 | 通过 / 未通过 |  |
| 前端 lint/typecheck/build | 通过 / 未通过 |  |
| 后端启动 | 通过 / 未通过 |  |
| 前端启动 | 通过 / 未通过 |  |
| Chat 流式输出 | 通过 / 未通过 |  |
| Knowledge 导入与切分 | 通过 / 未通过 |  |
| 索引重建 | 通过 / 未通过 |  |
| RAG 问答与来源展示 | 通过 / 未通过 |  |
| 三模式边界 | 通过 / 未通过 |  |
| 密钥与简历不追踪 | 通过 / 未通过 |  |

## 11. 验收结论

满足以下条件即可认为当前阶段验收通过：

- 自动化验证全部通过。
- 前端和后端都能本地启动。
- Chat、Knowledge、RAG 三条主链路至少各完成一次手动验证。
- 三模式边界没有明显混淆。
- 公开仓库不包含 `.env`、真实密钥和个人简历。
