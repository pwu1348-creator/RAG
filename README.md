# PengPeng RAG System

基于 RAG（检索增强生成）技术的智能知识库问答系统，个人练习项目。

---

## 启动方式

### 前置条件

- MySQL 已启动，数据库 `rag_system` 已创建
- Python 虚拟环境已安装依赖

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

访问地址：
- 管理员：http://localhost:3000/login
- 用户：http://localhost:3000/user/login

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
