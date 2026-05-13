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
- **文档解析**：MinerU（纯 CPU 模式，云服务器暂无 GPU，无加速）
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

# 先安装 MinerU（必须通过 uv 安装，不能直接 pip install）
pip install --upgrade pip
pip install uv
uv pip install -U "mineru[all]"

# 再安装其余依赖
pip install -r requirements.txt

deactivate
```

> 注意：MinerU 安装包较大，需要下载模型文件。云服务器暂无 GPU，MinerU 以纯 CPU 模式运行，无加速。

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

### 5. 配置环境变量

编辑 `backend/v1/.env`，根据实际情况修改 MySQL 连接、API Key 等配置。

### 6. 启动服务

```bash
# 使用 PM2 一键启动所有服务
pm2 start ecosystem.config.js
```

---

## 本地开发启动

### 1. 启动 Parser Service（端口 8001）

```bash
cd backend/v1/file_analysis
.\venv_RAG\Scripts\activate
python main.py
```

### 2. 启动 QA Service（端口 8002）

```bash
cd backend/v1/search_and_ask
.\venv_RAG2\Scripts\Activate.ps1
python main.py
```

### 3. 启动前端（端口 3000）

```bash
cd frontend
npm install   # 首次运行需要
npm run dev
```

---

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


---

## API 示例

### 自动提取实体关系

```bash
POST http://localhost:8002/api/v1/search/kg/extract/sync

{
  "doc_id": "doc_001",
  "kb_id": "kb_001",
  "content": "张三是AI工程师，在科技公司工作..."
}
```

### 多跳关联查询

```bash
POST http://localhost:8002/api/v1/search/kg/search/multihop

{
  "entity_name": "张三",
  "hops": 2
}
```

### 问答（启用知识图谱）

```bash
POST http://localhost:8002/api/v1/search/ask

{
  "query": "张三在哪家公司工作？",
  "knowledge_base_id": "kb_001",
  "use_kg": true,
  "kg_weight": 0.3
}
```

---

## PM2 启动（推荐）

> 需要全局安装 PM2：`npm install -g pm2`

项目根目录已提供 `ecosystem.config.js`，直接用以下命令管理所有服务。

### 启动所有服务

```bash
pm2 start ecosystem.config.js
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

访问地址：
- 管理员：http://localhost:3000/login
- 用户：http://localhost:3000/user/login

其他人访问地址
http://192.168.110.69:3000/login
http://192.168.110.69:3000/user/login
