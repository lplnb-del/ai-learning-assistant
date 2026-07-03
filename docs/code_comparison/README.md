# 代码实现对比：手写 vs LangChain

这个目录保存了在项目中最初手写、后来被 LangChain 方案替代的组件代码，主要用于回顾架构演进过程，并在面试时能够详细解释实现差异。

## 1. Text Splitter（文档切分）

- **手写代码**：[`manual_text_splitter.py`](./manual_text_splitter.py)
- **LangChain 替代**：`langchain_text_splitters.RecursiveCharacterTextSplitter` 和 `MarkdownHeaderTextSplitter`（已在 `src/ai_study_agent/ingestion/text_splitter.py` 中更新）

### 核心差异

| 维度 | 手写实现 `_window_chunk` | LangChain `RecursiveCharacterTextSplitter` |
|---|---|---|
| **切分策略** | 先按 `\n\n` 切分段落，再通过滑动窗口对超长段落按固定字符数强行截断。容易切碎句子。 | 递归寻找分隔符（如 `\n\n` -> `\n` -> ` ` -> `""`），优先在自然段或句子边界切分，语义保留更好。 |
| **标题提取** | 正则匹配 `^#{1,6}` 提取每段最近的一个标题。 | 借助 `MarkdownHeaderTextSplitter`，能够感知 Markdown 标题的层级树，并作为 `metadata` 附加到每一个 Chunk。 |
| **重叠区 (Overlap)** | 固定按字符回溯（`cursor - chunk_overlap`），重叠部分可能是不完整的词。 | 在递归切分时，跨边界保留指定的 overlap，同样尽量遵守分隔符规则。 |

---

## 2. Embedding（向量化）

> 💡 *注：项目中为了实现“无外部依赖也可运行”的降级能力，手写 Embedding 代码未被删除，目前作为回退方案保留在 `src/ai_study_agent/rag/embedding.py` 中。*

- **手写代码**：`HashingEmbeddingProvider`
- **LangChain 方案**：`LangChainEmbeddingProvider`（包装了 `langchain_openai.OpenAIEmbeddings`）

### 手写实现思路（面试考点）
利用 `hashlib.sha256` 充当伪 Embedding。将文本分词后：
1. 对每个词计算 SHA-256，取前 4 字节映射到固定的 N 维向量下标。
2. 用哈希值的某一位决定加 1 还是减 1。
3. 最终对向量进行 L2 归一化（除以模长）。
4. 检索时直接对两个归一化后的向量求点积，即得到余弦相似度。

---

## 3. Vector Index（向量检索）

> 💡 *注：与 Embedding 类似，手写向量库代码仍作为“降级策略”保留在 `src/ai_study_agent/storage/vector_index.py` 中。*

- **手写代码**：`LocalVectorIndex` (基于 JSON 文件持久化)
- **LangChain 方案**：`ChromaVectorStore` (包装了 `langchain_community.vectorstores.Chroma`)

### 手写实现思路（面试考点）
- **持久化**：将所有 Chunk 的文本与向量序列化为 JSON 写入磁盘。写入时使用 `.tmp` 临时文件再 `replace` 的原子写机制，防止写一半进程崩溃导致文件损坏。
- **检索计算**：遍历加载所有向量，逐一与 Query 向量计算余弦相似度，利用 Python 的 `sorted` 函数按分数倒序排列后切片取 `top_k`。
- **与 Chroma 的差异**：Chroma 底层使用 HNSW (Hierarchical Navigable Small World) 图索引算法，能做到近似最近邻 (ANN) 快速搜索，适合海量数据；手写 JSON 版本则是全量计算的精确搜索 (KNN)，仅适用于小规模知识库。
