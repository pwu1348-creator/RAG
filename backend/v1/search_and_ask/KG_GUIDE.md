## 知识图谱（Knowledge Graph）集成指南

### 概述

本项目已集成**高效的知识图谱系统**，支持：
- 📊 **自动实体关系提取** — 使用 LLM 从文档智能抽取实体和关系
- 🔗 **多跳推理检索** — 基于图结构的多层关联查询
- 🎯 **RAG 融合** — 知识图谱结果与向量/关键词检索融合
- 🏭 **生产级后端** — 支持 Neo4j 和轻量级 NetworkX 两种部署方案

---

## 快速开始

### 方案 1：轻量级部署（推荐用于开发）

使用 **NetworkX** 本地存储，无需额外服务部署。

#### 1.1 安装依赖

```bash
cd backend/v1/search_and_ask
pip install -r requirements.txt
```

#### 1.2 配置

在 `.env` 或环境变量中设置：

```env
# 知识图谱配置
KG_ENABLED=True
KG_BACKEND=networkx  # 使用 NetworkX 本地存储
KG_MIN_CONFIDENCE=0.5
KG_HOP_LIMIT=2
```

#### 1.3 启动服务

```bash
python main.py
```

服务启动后，知识图谱数据会存储在 `./kg_data/graph.json`

---

### 方案 2：生产级部署（Neo4j）

使用 **Neo4j** 作为专业图数据库，支持海量数据和复杂查询。

#### 2.1 安装 Neo4j

##### Windows 用户

使用 Docker 快速部署：

```bash
# 需要先安装 Docker Desktop

docker run -d ^
  --name neo4j ^
  -p 7687:7687 ^
  -p 7474:7474 ^
  -e NEO4J_AUTH=neo4j/pengpeng123 ^
  neo4j:latest
```

访问 Web UI：http://localhost:7474

##### Linux/Mac 用户

```bash
# 使用 Homebrew (Mac)
brew install neo4j

# 或 Docker
docker run -d \
  --name neo4j \
  -p 7687:7687 \
  -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/pengpeng123 \
  neo4j:latest
```

#### 2.2 配置

在 `.env` 中设置：

```env
# Neo4j 连接
KG_ENABLED=True
KG_BACKEND=neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pengpeng123
NEO4J_DATABASE=neo4j
KG_MIN_CONFIDENCE=0.5
KG_HOP_LIMIT=2
```

#### 2.3 验证连接

```bash
# 在 QA Service 启动时会自动连接，查看日志确认
pm2 logs qa-service
```

---

## API 使用

### 1. 实体关系提取

从文档提取实体和关系，自动存储到知识图谱。

#### 异步提取（推荐）

```bash
POST /api/v1/search/kg/extract

{
  "doc_id": "doc_001",
  "kb_id": "kb_001",
  "content": "张三是人工智能工程师，在科技公司工作。他专注于知识图谱研究。"
}
```

响应：
```json
{
  "status": "success",
  "message": "已提交提取任务，在后台执行",
  "doc_id": "doc_001"
}
```

#### 同步提取（等待结果）

```bash
POST /api/v1/search/kg/extract/sync

{
  "doc_id": "doc_001",
  "kb_id": "kb_001",
  "content": "...",
  "chunk_size": 2000
}
```

响应：
```json
{
  "status": "success",
  "entities": [
    {
      "id": "abc123",
      "name": "张三",
      "type": "Person",
      "doc_ids": ["doc_001"]
    }
  ],
  "relations": [
    {
      "id": "rel123",
      "source_id": "abc123",
      "target_id": "def456",
      "relation_type": "works_at",
      "confidence": 0.95
    }
  ],
  "entity_count": 5,
  "relation_count": 3
}
```

### 2. 实体搜索

```bash
POST /api/v1/search/kg/search/entity

{
  "name": "张三",
  "limit": 10
}
```

响应：
```json
{
  "status": "success",
  "entities": [
    {
      "id": "abc123",
      "name": "张三",
      "type": "Person",
      "doc_ids": ["doc_001", "doc_002"],
      "properties": {}
    }
  ],
  "total": 1
}
```

### 3. 多跳关联查询

```bash
POST /api/v1/search/kg/search/multihop

{
  "entity_name": "张三",
  "hops": 2,
  "limit": 50
}
```

响应：
```json
{
  "status": "success",
  "query_entity": "张三",
  "hops": 2,
  "entities": [
    {
      "id": "abc123",
      "name": "张三",
      "type": "Person"
    },
    {
      "id": "ghi789",
      "name": "科技公司",
      "type": "Organization"
    }
  ],
  "relations": [
    {
      "source": "abc123",
      "target": "ghi789",
      "relation_type": "works_at",
      "confidence": 0.95
    }
  ],
  "entity_count": 5,
  "relation_count": 4
}
```

### 4. 问答（自动使用 KG）

```bash
POST /api/v1/search/ask

{
  "query": "张三在哪家公司工作？",
  "knowledge_base_id": "kb_001",
  "use_kg": true,
  "kg_weight": 0.3
}
```

系统会自动：
1. 从查询中识别实体（"张三"）
2. 在知识图谱中查找相关信息
3. 进行多跳推理扩展相关实体
4. 融合 KG 结果与向量/关键词检索结果
5. 生成最终回答

参数说明：
- `use_kg`: 是否启用知识图谱（默认 true）
- `kg_weight`: KG 结果在融合中的权重（0-1，默认 0.3）
  - 0.3 表示重点依赖向量/关键词检索
  - 0.7 表示重点依赖知识图谱

### 5. 知识库数据删除

```bash
POST /api/v1/search/kg/delete/kb

{
  "kb_id": "kb_001"
}
```

响应：
```json
{
  "status": "success",
  "message": "已删除知识库 kb_001 的所有图数据",
  "kb_id": "kb_001"
}
```

### 6. 知识图谱状态

```bash
GET /api/v1/search/kg/status
```

响应：
```json
{
  "status": "success",
  "kg_enabled": true,
  "kg_backend": "networkx",
  "min_confidence": 0.5,
  "hop_limit": 2,
  "max_entities_per_doc": 50,
  "max_relations_per_doc": 100
}
```

---

## 工作流程

### 文档上传 → 知识图谱生成 → 智能问答

```
1. 用户上传文档
   ↓
2. Parser Service 解析文档 → 生成文本块
   ↓
3. QA Service 接收块，后台启动两个任务：
   
   任务 A: 向量化 + 存储到 ChromaDB（向量检索）
   
   任务 B: LLM 实体关系提取
      ├─ LLM 调用提示词
      ├─ 识别实体（Person, Organization, etc.）
      ├─ 识别关系（works_at, located_in, etc.）
      └─ 存储到知识图谱（Neo4j/NetworkX）
   
4. 用户提问
   ↓
5. QA Service 执行三层检索：
   
   Layer 1: 知识图谱检索
      ├─ 从查询提取实体
      ├─ KG 中搜索相关实体
      ├─ 多跳推理（2-3跳）扩展关联
      └─ 根据扩展实体检索相关文档块
   
   Layer 2: 向量检索
      ├─ Query 向量化
      └─ ChromaDB 语义相似度搜索
   
   Layer 3: 关键词检索
      ├─ BM25 倒排索引
      └─ 精确匹配查询词汇

6. RRF 融合 + BGE Reranker 重排序 → 候选集

7. KG 结果与混合检索结果融合
   ├─ KG 相似度：实体关联强度
   ├─ 混合相似度：向量+关键词融合
   └─ 加权融合：fused_score = (1-w)*hybrid + w*kg

8. 取回父块原文 + 上下文拼接

9. LLM 生成最终回答
```

---

## 性能优化

### 1. 实体提取优化

- **分块处理**：大文档自动分块（2000 字符）避免 LLM token 超限
- **去重机制**：自动去除重复实体和关系
- **置信度过滤**：仅保留高置信度结果（默认 >= 0.5）

### 2. 多跳搜索优化

- **深度限制**：默认 2 跳，可配置（避免图爆炸）
- **数量限制**：每步最多 20 个邻居
- **总数限制**：最多返回 50 个相关实体

### 3. 检索性能

| 后端 | 实体数 | 关系数 | 多跳查询 | 备注 |
|------|--------|--------|---------|------|
| NetworkX | 10K | 20K | <100ms | 完全内存，快速 |
| Neo4j | 100K+ | 1M+ | <500ms | 索引优化，生产级 |

### 4. 融合权重调优

```python
# 根据场景调整 kg_weight

# 事实类问题（WHO, WHAT, WHERE）
kg_weight = 0.6  # 依赖 KG 结构化信息

# 总结类问题
kg_weight = 0.3  # 依赖内容检索

# 推理类问题
kg_weight = 0.8  # 依赖多跳推理
```

---

## 故障排除

### Q1: "知识图谱服务未启用"

**原因**：KG 后端初始化失败

**解决**：
```bash
# 检查配置
echo $KG_ENABLED  # 应为 True

# 检查 Neo4j 连接（如使用 Neo4j）
docker ps | grep neo4j

# 查看日志
pm2 logs qa-service | grep "KnowledgeGraphService"
```

### Q2: 实体提取很慢

**原因**：LLM API 响应延迟

**解决**：
- 检查网络连接
- 减小 `chunk_size`（默认 2000，尝试 1000）
- 增加 LLM 并发（修改 asyncio 并发数）

### Q3: 知识图谱查询返回空结果

**原因**：
1. 知识库尚未提取实体关系
2. 查询实体不在图中
3. 实体名称不匹配

**解决**：
```bash
# 检查实体是否存在
POST /api/v1/search/kg/search/entity
{
  "name": "你要查找的实体",
  "limit": 100
}

# 如果为空，手动触发提取
POST /api/v1/search/kg/extract/sync
```

### Q4: Neo4j 连接超时

**原因**：Neo4j 服务未运行或地址错误

**解决**：
```bash
# 启动 Neo4j
docker start neo4j

# 验证连接
curl -i http://localhost:7474

# 检查配置
echo $NEO4J_URI  # 应为 bolt://localhost:7687
```

---

## 配置参考

### 完整配置参数

```env
# 知识图谱总开关
KG_ENABLED=True

# 后端选择：neo4j 或 networkx
KG_BACKEND=networkx

# Neo4j 配置（仅当 BACKEND=neo4j 时有效）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=pengpeng123
NEO4J_DATABASE=neo4j

# 提取参数
KG_MIN_CONFIDENCE=0.5  # 实体/关系置信度阈值
KG_HOP_LIMIT=2  # 多跳深度

# 容量参数
KG_MAX_ENTITIES_PER_DOC=50  # 每文档最多实体数
KG_MAX_RELATIONS_PER_DOC=100  # 每文档最多关系数

# 本地存储路径（仅 NetworkX）
GRAPH_PERSIST_DIR=./kg_data
```

### 推荐配置

#### 开发环境
```env
KG_BACKEND=networkx
KG_MIN_CONFIDENCE=0.5
KG_HOP_LIMIT=2
```

#### 生产环境
```env
KG_BACKEND=neo4j
KG_MIN_CONFIDENCE=0.6
KG_HOP_LIMIT=2  # 避免图爆炸
KG_MAX_ENTITIES_PER_DOC=100
KG_MAX_RELATIONS_PER_DOC=200
```

---

## 文件结构

```
backend/v1/search_and_ask/
├── services/
│   ├── knowledge_graph_service.py     # KG 核心服务（Neo4j/NetworkX）
│   └── entity_relation_extractor.py   # LLM 实体关系提取
├── core/
│   └── kg_retriever.py                # KG 检索和融合
├── routes/
│   └── kg_routes.py                   # KG 管理 API
├── kg_data/                           # NetworkX 本地存储（自动创建）
│   └── graph.json
└── config.py                          # KG 配置参数
```

---

## 最佳实践

### 1. 实体抽取质量

- 使用高质量、结构化的文档
- 避免极长的段落（> 3000 字符）
- 定期验证提取结果，调整置信度阈值

### 2. 查询优化

```python
# 对不同问题类型使用不同策略

# 结构化事实查询 → 高 KG 权重
use_kg = True
kg_weight = 0.7

# 内容摘要查询 → 低 KG 权重
use_kg = True
kg_weight = 0.2

# 完全禁用 KG → 快速降级
use_kg = False
```

### 3. 监控和维护

```bash
# 定期检查 KG 状态
curl http://localhost:8002/api/v1/search/kg/status

# 监控日志
pm2 logs qa-service | grep "KG\|Knowledge"

# 清理过期数据（知识库删除后）
POST /api/v1/search/kg/delete/kb
```

---

## 更多信息

- 📖 [Neo4j 官方文档](https://neo4j.com/docs/)
- 📖 [NetworkX 官方文档](https://networkx.org/)
- 🔍 [完整 API 文档](./API.md)
