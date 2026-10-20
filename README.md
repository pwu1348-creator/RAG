# PengPeng RAG System

基于 RAG（检索增强生成）技术的智能知识库问答系统，包含知识图谱增强模块。

---

## 项目架构

前后端分离，微服务设计，共 3 个服务：

| 服务 | 端口 | 路径 | 职责 |
|------|------|------|------|
| Parser Service | 8001 | `backend/v1/file_analysis/` | 文档解析、向量化存储、用户认证、知识库管理 |
| QA Service | 8002 | `backend/v1/search_and_ask/` | 混合检索、重排序、流式/非流式问答、知识图谱增强 |
| Frontend | 3000 | `frontend/` | Vue 3 前端界面 |

---

## 核心特性

### 检索层（Retrieval）
- **混合检索**：BM25 + 向量搜索 + RRF 融合
- **重排序**：BGE-reranker-v2-m3 精确相关性重排
- **父子块检索**：智能块划分与上下文拼接
- **知识图谱增强**：实体关系多跳推理检索

### 问答层（QA）
- **非流式问答**：立即返回完整答案
- **流式回答**：实时生成（SSE）
- **撰写模式**：专业文档写作协助
- **上下文记忆**：支持多轮对话

### 知识管理
- **自动实体关系抽取**：使用 LLM 智能识别
- **知识图谱存储**：NetworkX（轻量级本地图存储）
- **多跳推理**：支持 2-3 跳关联查询
- **图检索融合**：与向量检索自动融合

---

## 技术栈

### 后端
- **框架**：FastAPI + Uvicorn
- **LLM**：Qwen3-235B-A22B（Gitee AI 平台）
- **Embedding**：Qwen3-Embedding-8B（1024 维）
- **Reranker**：BGE-reranker-v2-m3
- **向量数据库**：ChromaDB（本地持久化）
- **关系数据库**：MySQL
- **文件存储**：MinIO
- **文档解析**：MinerU 云端 API（无需本地 GPU，通过官方 API 调用云端算力）
- **知识图谱**：NetworkX

### 前端
- **框架**：Vue 3 + Vite
- **状态管理**：Pinia
- **路由**：Vue Router
- **国际化**：vue-i18n
- **HTTP**：Axios

---

## 云服务器部署流程

### 前置条件

- Linux 服务器（推荐 Ubuntu 22.04+）
- Python 3.10+
- Node.js 18+
- MySQL 已启动，数据库 `rag_system` 已创建
- PM2 全局安装：`npm install -g pm2`

### 1. 克隆项目

```bash
git clone https://github.com/pwu1348-creator/RAG.git
cd RAG
```

### 2. 安装 Parser Service 依赖（端口 8001）

```bash
cd backend/v1/file_analysis
python -m venv venv_RAG
source venv_RAG/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

deactivate
```

> 注意：文档解析已改为调用 MinerU 云端 API，不再需要本地安装 MinerU 及下载模型文件。API Token 在 `backend/v1/.env` 中配置。

### 3. 安装 QA Service 依赖（端口 8002）

```bash
cd backend/v1/search_and_ask
python -m venv venv_RAG2
source venv_RAG2/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

deactivate
``` 

### 4. 安装前端依赖（端口 3000）

```bash
cd frontend
npm install
```




## 知识图谱配置

### 快速配置（开发环境）

默认使用 NetworkX 本地图存储，无需额外部署：

```bash
# backend/v1/search_and_ask/config.py 内置默认值：
# KG_BACKEND=networkx
# KG_MIN_CONFIDENCE=0.5
# KG_HOP_LIMIT=2

# 启动后自动生成知识图谱数据：./kg_data/graph.json
```





PengPeng RAG 项目框架总览
这是一个基于 RAG（检索增强生成）的智能知识库问答系统，前后端分离，微服务架构，共 3 个服务通过 PM2 统一管理。

整体架构

pengpengRAG/
├── backend/v1/
│   ├── .env                          # 共享环境变量配置
│   ├── file_analysis/  (端口 8001)    # Parser Service - 文档解析服务
│   └── search_and_ask/ (端口 8002)    # QA Service - 检索问答服务
├── frontend/           (端口 3000)    # Vue 3 前端
├── scripts/                           # PM2 启动脚本
└── ecosystem.config.js                # PM2 进程管理配置
后端服务 1：Parser Service（8001）
职责：文档解析、向量化存储、用户认证、知识库管理


file_analysis/
├── main.py                 # FastAPI 入口
├── config/settings.py      # 配置
├── core/document_parser.py # 文档解析核心（调用 MinerU 云端 API）
├── routes/
│   ├── parser_routes.py    # 文件上传/解析接口
│   ├── auth_routes.py      # 用户认证（登录/注册）
│   ├── admin_routes.py     # 管理员接口
│   ├── kb_routes.py        # 知识库 CRUD
│   └── settings_routes.py  # 系统设置
├── services/
│   ├── parser_service.py       # 解析业务逻辑
│   ├── chromadb_service.py     # ChromaDB 向量存储
│   ├── embedding_service.py    # Embedding 调用
│   ├── minio_service.py        # MinIO 文件存储
│   ├── mysql_service.py        # MySQL 操作
│   └── auth_service.py         # 认证逻辑
├── database/
│   ├── db_manager.py       # 数据库连接管理
│   └── schema.sql          # 建表语句
├── chroma_db/              # ChromaDB 本地持久化数据
└── uploads/                # 上传文件临时存储
后端服务 2：QA Service（8002）
职责：混合检索、重排序、流式/非流式问答、知识图谱增强


search_and_ask/
├── main.py              # FastAPI 入口
├── config.py            # 全部配置（LLM/Embedding/Reranker/KG 等）
├── core/
│   ├── retriever.py     # 混合检索（BM25 + 向量 + RRF 融合）
│   ├── kg_retriever.py  # 知识图谱检索
│   ├── qa.py            # 问答核心逻辑
│   └── answer_modes.py  # 回答模式（普通/撰写等）
├── routes/
│   ├── search_routes.py # 检索接口
│   ├── qa_routes.py     # 问答接口（流式/非流式）
│   ├── kg_routes.py     # 知识图谱接口（实体抽取/多跳查询）
│   ├── auth_routes.py   # 认证转发
│   └── system_routes.py # 系统状态
├── services/
│   ├── embedding_service.py           # Embedding
│   ├── chromadb_service.py            # 向量检索
│   ├── conversation_service.py        # 对话历史管理
│   ├── entity_relation_extractor.py   # LLM 实体关系抽取
│   └── knowledge_graph_service.py     # 知识图谱存储（NetworkX）
└── kg_data/             # 知识图谱持久化数据
前端（Vue 3 + Vite）

frontend/src/
├── App.vue / main.js
├── router/index.js      # 路由（管理员端 + 用户端）
├── api/                 # Axios 请求封装（admin/knowledge/parser/qa/user）
├── stores/              # Pinia 状态管理
├── pages/
│   ├── Login.vue / UserLogin.vue    # 双登录入口
│   ├── UserChat.vue                 # 用户问答界面
│   ├── QA.vue                       # 管理员问答
│   ├── Upload.vue                   # 文件上传
│   ├── Knowledge.vue                # 知识库管理
│   ├── UserManagement.vue           # 用户管理
│   ├── AdminDashboard.vue           # 管理后台
│   └── Settings.vue                 # 系统设置
└── components/          # 公共组件（Layout/Sidebar/Toast 等）
核心技术栈
层	技术
LLM	Qwen3-235B-A22B（Gitee AI 平台）
Embedding	Qwen3-Embedding-8B（1024 维）
Reranker	BGE-reranker-v2-m3
向量数据库	ChromaDB（本地持久化）
关系数据库	MySQL
文件存储	MinIO
文档解析	MinerU 云端 API
知识图谱	NetworkX（本地 JSON 持久化）
后端框架	FastAPI + Uvicorn
前端框架	Vue 3 + Vite + Pinia + Vue Router
进程管理	PM2
数据流简述
用户上传文档 → Parser Service 调用 MinerU API 解析 → 分块 → Embedding → 存入 ChromaDB + 元数据存 MySQL
用户提问 → QA Service 做混合检索（BM25 + 向量 + 可选知识图谱） → Reranker 重排 → LLM 生成回答（支持流式 SSE）
知识图谱：LLM 自动抽取实体关系 → NetworkX 存储 → 支持多跳推理查询，与向量检索结果融合


## PM2 启动（推荐）

> 需要全局安装 PM2：`npm install -g pm2`

项目根目录已提供 `ecosystem.config.js`，直接用以下命令管理所有服务。

### 启动所有服务

```bash
pm2 start /home/wsp/pengpengRAG/ecosystem.config.js

```

### 常用 PM2 命令

```bash
pm2 list                    # 查看所有进程状态
pm2 logs                    # 查看所有日志（实时）
pm2 logs parser-service     # 查看 Parser Service 日志
pm2 logs qa-service         # 查看 QA Service 日志
pm2 logs frontend           # 查看前端日志
pm2 restart all             # 重启所有服务
pm2 restart parser-service  # 单独重启 Parser Service
pm2 restart qa-service      # 单独重启 QA Service
pm2 restart frontend        # 单独重启前端
pm2 stop all                # 停止所有服务
pm2 delete all              # 删除所有进程
pm2 save                    # 保存当前进程列表（用于开机自启）
pm2 startup                 # 生成开机自启命令（按提示执行输出的命令）
```

管理员登录：https://rag.zhou1028.cn/login
用户登录：https://rag.zhou1028.cn/user/login
