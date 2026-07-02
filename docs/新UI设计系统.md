# UI：全能学习助理设计系统 (Neural Expressive 版)

## 1. 核心设计哲学 (Core Philosophy)

本系统采用“神经元表现力 (Neural Expressive)”设计范式，旨在通过 MD3 规范建立起 AI 与人之间的逻辑信任。

- **学术沉静 (Academic Calm)**：排版优先考虑长时间阅读的舒适性，去除干扰性的高频色块。
- **深度感知 (Elevation & Depth)**：通过层级阴影与背景透明度，构建虚拟的物理空间感，避免扁平导致的逻辑混淆。
- **灵动响应 (Fluid Responsiveness)**：界面响应 AI 推理状态 (Thinking/Retrieving/Generating) 需具备视觉反馈，而非死板的静态加载。

## 2. 颜色系统与动态语义 (Semantic Colors)

系统支持日夜间模式，通过 CSS 变量 `var(--color-*)` 进行全局控制。

### 2.1 基础色值表

| Token              | Light Mode         | Dark Mode                | 属性描述                   |
| ------------------ | ------------------ | ------------------------ | -------------------------- |
| `app-bg`           | `#F0F4F9`          | `#131314`                | 全局背景，用于减弱边缘对比 |
| `surface`          | `#FFFFFF`          | `#1E1F20`                | 主要卡片与工作区容器       |
| `surface-elevated` | `#F8FAFC`          | `#252627`                | 次级面板，用于区分层级     |
| `text-primary`     | `#1F1F1F`          | `#E3E3E3`                | 正文标题与核心交互         |
| `text-secondary`   | `#444746`          | `#C4C7C5`                | 元数据、标注、说明文字     |
| `accent-blue`      | `#0B57D0`          | `#C2E7FF`                | 核心连接、激活项、主要按钮 |
| `border-soft`      | `rgba(0,0,0,0.08)` | `rgba(255,255,255,0.12)` | 柔和分割线                 |

### 2.2 状态色 (Semantic Feedback)

- **Success (成功/已掌握)**: `#16A34A` (暗色背景下应降低明度至 `#55C27C`)
- **Warning (模糊/待复习)**: `#F59E0B`
- **Danger (严重/删除/失败)**: `#DC2626`
- **Info (溯源/提示)**: `#2563EB`

## 3. 排版体系 (Typography System)

排版遵循阅读节奏，采用非等宽间距控制 (Kerning) 以提升中文排版的舒适度。

| 级别               | 大小 | 字重 | 行高 (Line Height) | 语义                         |
| ------------------ | ---- | ---- | ------------------ | ---------------------------- |
| **Headline**       | 24px | 700  | 32px               | 页面大标题                   |
| **Section**        | 18px | 650  | 24px               | 卡片标题、功能区命名         |
| **Body (Default)** | 15px | 400  | 26px               | 核心 AI 回复、文档内容       |
| **Metadata**       | 13px | 400  | 20px               | 引用来源、时间戳、卡片标签   |
| **Code/Monospace** | 13px | 500  | 20px               | Agent 日志、Token 数、代码块 |

## 4. 组件交互规范 (Component Specifications)

### 4.1 Pill-Input (胶囊输入区)

- **默认状态**：宽胶囊形状，高度固定 52px，带有极细的柔和边框。
- **激活状态 (Focus)**：边框加深至 `accent-blue`，阴影增强，展示 `Focus Ring`。
- **输入状态**：自动根据内容拉伸高度，最高支持 150px，超出后内部滚动。
- **视觉隐喻**：悬浮于所有图层之上 (z-index: 50)，暗示这是“与模型对话的唯一入口”。

### 4.2 Magazine-style Output (AI 回复流)

- **布局逻辑**：彻底放弃传统对话气泡。AI 回复作为长文本流，与用户输入建立左对齐与右对齐的视觉差异。
- **引用机制**：行内引用 `[1]` 应具备点击反馈，触发右侧 Inspector 的溯源卡片滑入。
- **空状态设计**：使用极简线性图标，配合低对比度引导文字，避免空荡感。

### 4.3 Inspector Panel (检查器面板)

- **功能定位**：作为“思维的显微镜”。
- **层级显示**：
  - **Source View**：显示 chunk 内容、相似度得分 (Similarity Score)。
  - **Agent Log**：显示 JSON 树结构的 Tool Execution log。
- **交互规则**：支持手势收起/展开，点击溯源点时自动滚动至该片段。

## 5. 动效与物理规律 (Motion & Physics)

- **缓动函数**：所有位移采用 `cubic-bezier(0.2, 0, 0, 1)`。
- **时长基准**：
  - `micro-interaction` (图标变化、按钮 hover)：150ms。
  - `layout-transition` (切换模式、展开检查器)：250ms - 300ms。
  - `entrance` (页面加载)：400ms。
- **Physics**：所有悬浮组件的阴影应表现出从 `elevation 1` (默认) 到 `elevation 3` (聚焦) 的层次感，通过 `box-shadow` 的透明度变化实现。

## 6. 辅助功能与工程化要求 (Accessibility & Engineering)

- **Color Contrast**：所有正文文本对比度需通过 WCAG 2.1 AA 标准 (4.5:1)。
- **Color Blindness**：状态色 (成功/失败) 不得仅依赖颜色表达，需配合图标或文字标签。
- **Dark Mode 策略**：系统应默认优先读取系统偏好 (`prefers-color-scheme`)，并提供切换开关，主题切换需通过 `data-theme="dark"` 在根节点上实现，而非污染所有子组件。
- **Touch Targets**：所有可点击目标 (Button/Tab) 最小尺寸应为 44px x 44px。
- **Frontend Stack**：正式前端使用 Vue 3 + Vite + TypeScript + Tailwind CSS，一比一还原 `prototype/index.html`；Streamlit 不作为正式 UI 实现目标。
- **Vue Components**：使用 Composition API 与 `<script setup lang="ts">`，根组件/视图只做组合，复杂 UI 拆为聚焦组件，状态进入 Pinia 或 composables。
- **Asset Policy**：原型中的 Tailwind CDN、Lucide CDN 和 Google Fonts 只作为预览依赖；正式前端必须改成本地 npm 依赖或构建产物。

## 7. 版本记录

- **v1.0**：确立 Neural Expressive 视觉语言。
- **v1.1**：细化颜色 token 与动效曲线，增加无障碍标准。
- **v1.2**：明确正式前端技术栈为 Vue 3 + Vite + TypeScript + Tailwind CSS。
