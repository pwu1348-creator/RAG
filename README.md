# PengPeng RAG System

基于 RAG（检索增强生成）技术的智能知识库问答系统，包含**知识图谱**增强模块，个人练习项目。

---

## 🚀 核心特性

### 检索层（Retrieval）
- ✅ **混合检索**：BM25 + 向量搜索 + RRF 融合
- ✅ **重排序**：BGE-reranker-base 精确相关性重排
- ✅ **父子块检索**：智能块划分与上下文拼接
- ✅ **知识图谱增强**：实体关系多跳推理检索 ⭐ **新增**

### 问答层（QA）
- ✅ **非流式问答**：立即返回完整答案
- ✅ **流式回答**：实时生成（SSE）
- ✅ **撰写模式**：专业文档写作协助
- ✅ **上下文记忆**：支持多轮对话

### 知识管理 ⭐ **新增**
- ✅ **自动实体关系抽取**：使用 LLM 智能识别
- ✅ **知识图谱存储**：Neo4j（生产级）/ NetworkX（轻量级）
- ✅ **多跳推理**：支持 2-3 跳关联查询
- ✅ **图检索融合**：与向量检索自动融合

---

## 启动方式

## 启动方式

### 前置条件

- MySQL 已启动，数据库 `rag_system` 已创建
- Python 虚拟环境已安装依赖
- **[可选] Neo4j 部署**（用于生产级知识图谱，详见下方）

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

## 知识图谱配置 ⭐ **新增**

### 快速配置（开发环境）

默认使用 **NetworkX** 本地图存储（无需额外部署）：

```bash
# 环境变量自动配置
# backend/v1/search_and_ask/config.py 已内置默认值：
# - KG_BACKEND=networkx
# - KG_MIN_CONFIDENCE=0.5
# - KG_HOP_LIMIT=2

# 启动后自动生成知识图谱数据：
# ./kg_data/graph.json
```

### 高级配置（生产环境 - Neo4j）

**使用 Docker 部署 Neo4j**：

```bash
# Windows PowerShell
docker run -d `
  --name neo4j `
  -p 7687:7687 `
  -p 7474:7474 `
  -e NEO4J_AUTH=neo4j/pengpeng123 `
  neo4j:latest

# Linux/Mac
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/pengpeng123 \
  neo4j:latest
```

**配置环境变量**：

```bash
set KG_BACKEND=neo4j
set NEO4J_URI=bolt://localhost:7687
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=pengpeng123
```

详见 → [知识图谱完整指南](./backend/v1/search_and_ask/KG_GUIDE.md)

---

## 知识图谱 API

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

### 问答自动使用 KG

```bash
POST http://localhost:8002/api/v1/search/ask

{
  "query": "张三在哪家公司工作？",
  "knowledge_base_id": "kb_001",
  "use_kg": true,      # 启用知识图谱
  "kg_weight": 0.3     # KG 权重（0-1）
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