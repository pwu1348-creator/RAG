# PengPeng RAG System

基于 RAG（检索增强生成）技术的智能知识库问答系统，个人练习项目。

---

## 项目整体架构

```
用户浏览器 (前端 :3000)
    │
    ├─ /api/parser/*      → Parser Service  (:8001)  文档解析后端
    ├─ /api/knowledge-bases/* → Parser Service (:8001)  知识库管理
    ├─ /api/auth/*        → Parser Service  (:8001)  认证
    ├─ /api/admin/*       → Parser Service  (:8001)  管理员
    └─ /api/qa/*          → QA Service      (:8002)  检索问答后端
```

### 三个服务说明

| 服务 | 端口 | 目录 | 职责 |
|------|------|------|------|
| 前端 Vue3 | 3000 | `frontend/` | 管理员界面 + 用户问答界面 |
| Parser Service | 8001 | `backend/v1/file_analysis/` | 文档上传、PDF解析(MinerU)、向量化写入ChromaDB、知识库/用户管理 |
| QA Service | 8002 | `backend/v1/search_and_ask/` | 检索问答（BM25+向量+RRF+Reranker+LLM） |

---

## 完整数据流

```
1. 上传文档
   前端 Upload页 → Parser Service → MinerU解析PDF → 文本存MySQL
                                  → 向量化(Embedding) → ChromaDB

2. 重索引（父子分块）
   前端 Knowledge页 → QA Service /index/kb/{id}
   → ParentChildChunker 切分父块(600-1200 tokens) + 子块(200-350 tokens)
   → 父块 → MySQL document_chunks (chunk_type='parent')
   → 子块 → MySQL + ChromaDB (含 parent_chunk_id 元数据)

3. 检索问答
   前端 QA页 输入问题
   → QA Service /ask/stream (SSE流式)
   → HybridRetriever: BM25关键词检索 + 向量检索 → RRF融合
   → BGE Reranker 重排序子块
   → 根据 parent_chunk_id 回退父块完整上下文
   → 构建Prompt → AsyncOpenAI LLM → 流式返回答案 + RAG_META引用
   → 前端实时渲染回答 + 显示参考来源
```

---

## 前端界面说明

前端共用同一个 Vue3 应用（端口 3000），分为两套独立界面：

### 管理员界面（需启动 Parser Service 8001）

| 路由 | 页面 | 说明 |
|------|------|------|
| `/login` | 管理员登录 | 管理员账号密码登录 |
| `/` | 首页 | 系统概览，快速入口 |
| `/users` | 用户管理 | 增删改查用户 |
| `/parser` | 文件上传 | 上传PDF/文档，触发解析 |
| `/knowledge` | 知识库管理 | 创建知识库、关联文档、触发重索引 |
| `/qa` | 管理员问答 | 管理员可调用所有知识库的问答界面 |
| `/settings` | 系统设置 | 系统参数配置 |

### 用户界面（需同时启动 QA Service 8002）

| 路由 | 页面 | 说明 |
|------|------|------|
| `/user/login` | **用户登录** | 带泥巴人动画的登录页，**登录请求走 QA Service (8002)**，8002 未启动则无法登录 |
| `/user/chat` | **智能问答** | 用户专属问答界面，左侧可配置助手名称/知识库/参数，支持多会话历史 |

### 用户登录页特色

登录页左侧有三个 SVG 泥巴人角色，会根据操作状态变化：
- **无操作 2 秒**：泥巴人偷看输入框方向（眼球斜视）
- **输入账号时**：泥巴人翻白眼（眼球上翻）+ 抖动动画
- **输入密码时**：泥巴人双手捂眼（闭眼线 + 手臂抬起）

### 用户问答界面功能

- 左侧可折叠侧边栏：对话历史列表、新建对话、助手设置、个人信息、退出
- 助手设置：自定义助手名称、选择知识库、调整 top_k、开关重排序（持久化）
- 个人信息：修改用户名、邮箱、密码
- 主区域：SSE 流式对话，显示参考来源，支持多轮上下文
- 对话记录本地持久化，会话名称自动取第一条问题

---

## 启动方式

### 前置条件

- MySQL 已启动，数据库 `rag_system` 已创建
- ChromaDB 使用本地持久化（`./chroma_db`），无需单独启动
- Python 虚拟环境已安装依赖

### 1. 启动 Parser Service（端口 8001）

```bash
cd backend/v1/file_analysis
.\venv_RAG\Scripts\activate        # Windows PowerShell
# 或 source venv_RAG/bin/activate  # Linux/Mac
python main.py
```

提供：文档上传解析、知识库管理、用户认证等 API

### 2. 启动 QA Service（端口 8002）

```bash
cd backend/v1/search_and_ask
.\venv_RAG2\Scripts\Activate.ps1   # Windows PowerShell
# 或 source venv_RAG2/bin/activate # Linux/Mac
python main.py
```

提供：检索问答、重索引等 API

### 3. 启动前端（端口 3000）

```bash
cd frontend
npm install   # 首次运行需要
npm run dev
```

访问 http://localhost:3000

---

## QA Service API 说明

基础路径：`http://localhost:8002/api/v1/search`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/search` | 纯检索，不调用LLM，返回相关父块 |
| POST | `/ask` | 问答（非流式），返回完整回答 |
| POST | `/ask/stream` | 问答（SSE流式），前端实时接收 |
| POST | `/writechat` | 撰写模式（非流式） |
| POST | `/writechat/stream` | 撰写模式（SSE流式） |
| POST | `/index/kb/{kb_id}` | 重索整个知识库（父子分块） |
| POST | `/index/doc/{kb_id}/{doc_id}` | 重索单个文档 |
| GET  | `/health` | 健康检查 |

### 请求示例（流式问答）

```json
POST /api/v1/search/ask/stream
{
  "query": "这份文档的主要内容是什么？",
  "knowledge_base_id": "kb_xxx",
  "top_k": 5,
  "use_rerank": true,
  "chat_history": [
    {"role": "user", "content": "上一个问题"},
    {"role": "assistant", "content": "上一个回答"}
  ]
}
```

SSE 响应格式：
```
data: 这份文档
data: 主要讲述了...
data: 
data: <!--RAG_META {"citations":[...],"search_results":[...]} RAG_META-->
```

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite + Vue Router + Pinia |
| Parser 后端 | FastAPI + MinerU(PDF解析) + pymysql |
| QA 后端 | FastAPI + ChromaDB + BM25 + BGE Reranker + AsyncOpenAI |
| 向量模型 | Qwen3-Embedding-8B（Gitee AI） |
| LLM | Qwen3-235B-A22B（Gitee AI） |
| 数据库 | MySQL（元数据） + ChromaDB（向量） |

---

## 配置说明

QA Service 支持环境变量覆盖默认配置：

```bash
# LLM
LLM_BASE_URL=https://ai.gitee.com/v1
LLM_API_KEY=your_key
LLM_MODEL=Qwen3-235B-A22B

# Embedding
EMBEDDING_BASE_URL=https://ai.gitee.com/v1
EMBEDDING_API_KEY=your_key
EMBEDDING_MODEL=Qwen3-Embedding-8B

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=rag_system

# 服务
SEARCH_ASK_PORT=8002
SEARCH_ASK_DEBUG=false
```




# 1. 启动 MySQL

# 2. Parser Service
cd backend/v1/file_analysis
.\venv_RAG\Scripts\activate
python main.py

# 3. QA Service  
cd backend/v1/search_and_ask
.\venv_RAG2\Scripts\Activate.ps1 
python main.py

# 4. 前端
cd frontend
npm run dev

__访问方式：__

- 管理员：`http://localhost:3000/login`（只需 Parser Service 8001）
- 用户：`http://localhost:3000/user/login`（需要 Parser Service 8001 + QA Service 8002 同时启动）
