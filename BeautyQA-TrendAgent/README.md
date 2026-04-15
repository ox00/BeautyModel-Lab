# Multi-Agent for Trend — 趋势采集 Multi-Agent 系统

基于 MediaCrawler 的智能趋势内容采集与分析系统，支持小红书、抖音、B站、微博等多平台自动化爬取，结合 LLM 进行关键词扩充与数据清洗。

## 模块边界

- `BeautyQA-TrendAgent/` 放项目自有的趋势采集编排、任务调度、关键词扩展、清洗与 API 代码
- `BeautyQA-vendor/MediaCrawler/` 放外部 crawler 引擎源码
- 当前模块通过子进程方式调用 `MediaCrawler`，并依赖其原始 PostgreSQL 表结构
- 依赖边界与修改建议见 `../docs/13-trendagent-dataflow-and-dependency-boundary.md`

---

## 目录

- [项目架构](#项目架构)
- [工作流程](#工作流程)
- [环境配置](#环境配置)
- [快速启动](#快速启动)
- [运行方式](#运行方式)
- [API 接口](#api-接口)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

---

## 项目架构

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  CSV 关键词  │───▶│ 关键词扩充    │───▶│ 多平台爬取    │───▶│ AI 数据清洗   │
│  数据源      │    │ (LLM Agent)  │    │ (MediaCrawler)│    │ (LLM Agent)  │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                               │                     │
                                          ┌────▼─────┐        ┌────▼─────┐
                                          │PostgreSQL │        │ 清洗数据  │
                                          │  + Redis  │        │ 入库     │
                                          └──────────┘        └──────────┘
```

**核心组件：**

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| Web API | FastAPI + Uvicorn | RESTful 接口，端口 8000 |
| 爬虫引擎 | MediaCrawler (子进程) | 支持 xhs/dy/bili/wb/ks/tieba/zhihu |
| 任务调度 | Celery + Redis | 定时/异步任务队列 |
| 数据库 | PostgreSQL 15 (Docker) | 端口 5433，库名 media_crawler |
| 缓存 | Redis 7 (Docker) | 端口 6379 |
| LLM | 智谱 GLM / OpenAI 兼容 | 关键词扩充 + 数据清洗 |

---

## 工作流程

流水线分为 3 个步骤，由 `run_pipeline.py` 编排：

### Step 1: 关键词扩充 (thinking:off)

读取 `backend/config/trend-keyword.csv` 中的关键词，通过 LLM Agent 扩充为更丰富的搜索词组合。

- 输入：原始关键词（如 "发酵赋能"）
- 输出：扩充关键词列表（如 "发酵赋能, 发酵赋能 护肤, 发酵赋能 精华"）

### Step 2: 多平台爬取

每个扩充关键词启动独立的 MediaCrawler 子进程：

```
python main.py --platform xhs --lt qrcode --type search \
  --keywords 发酵赋能 \
  --save_data_option postgres \
  --headless false \
  --get_comment true \
  --max_comments_count_singlenotes 10 \
  --max_concurrency_num 2
```

- 每个关键词独立子进程，互不阻塞
- 第一个关键词使用 qrcode 登录，后续关键词复用 cookie
- 子进程超时：qrcode 15 分钟，cookie 10 分钟
- 超时后自动终止整个进程树（含浏览器子进程）

### Step 3: AI 数据清洗 (thinking:on)

对爬取的原始数据进行 AI 驱动的清洗与结构化处理。

---

## 环境配置

### 1. 前置条件

- **Python 3.13+**（项目使用根目录 `.venv` 统一管理）
- **Docker Desktop**（运行 PostgreSQL 和 Redis）
- **Git**

### 2. .env 配置文件

配置文件位于 **`backend/.env`**，关键配置项：

```env
# PostgreSQL（Docker 映射端口 5433→5432）
DATABASE_URL=postgresql+asyncpg://postgres:123456@localhost:5433/media_crawler
POSTGRES_DB_HOST=localhost
POSTGRES_DB_PORT=5433
POSTGRES_DB_USER=postgres
POSTGRES_DB_PWD=123456
POSTGRES_DB_NAME=media_crawler

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# LLM（关键词扩充 + 数据清洗）
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-5.1

# MediaCrawler 路径（自动计算，一般无需修改）
MEDIACRAWLER_DIR=C:/Users/Admin/Desktop/BeautyModel-Lab/BeautyQA-vendor/MediaCrawler
```

> **注意：** MediaCrawler 子进程通过 `process_manager.py` 中的 `_get_env()` 自动注入 PostgreSQL 环境变量，无需在 MediaCrawler 目录下单独配置 `.env`。

### 3. 依赖安装

项目使用**统一的 `.venv`**（位于项目根目录），backend 和 MediaCrawler 共享同一套依赖：

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活
.\.venv\Scripts\Activate.ps1

# 安装全部依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

> **重要：** 根目录的 `requirements.txt` 是项目的唯一依赖清单，已合并 backend 和 MediaCrawler 的全部依赖。`backend/requirements.txt` 和 `../BeautyQA-vendor/MediaCrawler/requirements.txt` 仅供参考，无需单独安装。

---

## 快速启动

### 1. 启动基础设施

```powershell
cd backend
docker compose up -d
```

验证 PostgreSQL 和 Redis 是否运行：

```powershell
docker ps
# 应看到 trend_postgres (5433) 和 trend_redis (6379)
```

### 2. 初始化数据库

```powershell
cd ..\BeautyQA-vendor\MediaCrawler
..\..\.venv\Scripts\python.exe main.py --init_db postgres
```

### 3. 运行流水线

```powershell
cd backend

# 测试模式（前5个关键词，扫码登录）
..\..\.venv\Scripts\python.exe run_pipeline.py --mode test --platform xhs --login-type qrcode

# 正式模式（全部关键词，扫码登录）
..\..\.venv\Scripts\python.exe run_pipeline.py --mode prod --platform xhs --login-type qrcode

# Cookie 登录（复用已保存的登录状态，无需扫码）
..\..\.venv\Scripts\python.exe run_pipeline.py --mode test --platform xhs --login-type cookie

# 无头模式
..\..\.venv\Scripts\python.exe run_pipeline.py --mode test --platform xhs --login-type cookie --headless

# 定时调度（每天自动执行）
..\..\.venv\Scripts\python.exe run_pipeline.py --mode prod --platform xhs --login-type cookie --schedule daily
```

### 4. 启动 Web API 服务

```powershell
cd backend
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 启动 Celery Worker（可选，用于异步任务）

```powershell
cd backend
..\..\.venv\Scripts\celery.exe -A app.tasks.celery_app worker --loglevel=info -Q crawl,process,schedule

# 启动 Beat 调度器（定时任务）
..\..\.venv\Scripts\celery.exe -A app.tasks.celery_app beat --loglevel=info
```

---

## 运行方式

项目支持三种运行方式：

### 方式一：独立流水线脚本（推荐用于测试/一次性采集）

```
python run_pipeline.py --mode test --platform xhs --login-type qrcode
```

适用于快速验证和手动触发采集，直接在终端查看日志输出。

### 方式二：Web API + Celery（推荐用于生产环境）

1. 启动 API 服务 → 通过 REST API 提交任务
2. Celery Worker 异步执行爬取和清洗
3. 通过 API 查询任务状态和数据

### 方式三：MediaCrawler 独立运行

```powershell
cd ..\BeautyQA-vendor\MediaCrawler
..\..\.venv\Scripts\python.exe main.py --platform xhs --lt qrcode --type search --keywords 关键词
```

适用于单独测试某个平台的爬取功能，不经过 backend 流水线。

---

## API 接口

Web API 服务启动后，访问以下端点：

| 端点 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/v1/keywords` | 获取关键词列表 |
| `POST /api/v1/keywords/expand` | 触发关键词扩充 |
| `GET /api/v1/tasks` | 获取任务列表 |
| `POST /api/v1/tasks/crawl` | 提交爬取任务 |
| `GET /api/v1/data/notes` | 查询笔记数据 |
| `GET /api/v1/data/comments` | 查询评论数据 |
| `GET /api/v1/system/status` | 系统状态 |

API 文档：启动后访问 `http://localhost:8000/docs`

---

## 项目结构

```
BeautyQA-TrendAgent/
├── .venv/                              # 统一虚拟环境（唯一）
├── requirements.txt                    # 统一依赖清单（唯一）
├── trend-keyword.csv → backend/config/ # 关键词数据源
│
├── backend/                            # 后端主项目
│   ├── .env                            # 环境变量配置（唯一）
│   ├── run_pipeline.py                 # 流水线入口脚本
│   ├── pyproject.toml                  # 项目元数据
│   ├── docker-compose.yml              # PostgreSQL + Redis
│   ├── alembic/                        # 数据库迁移
│   ├── config/
│   │   ├── trend-keyword.csv           # 趋势关键词数据
│   │   └── enhance_trend_keyword.md    # LLM 扩充 Prompt
│   └── app/
│       ├── main.py                     # FastAPI 入口
│       ├── config/settings.py          # Pydantic Settings
│       ├── agents/                     # AI Agent 层
│       │   ├── base.py                 # Agent 基类
│       │   ├── keyword_expander_agent.py  # 关键词扩充 Agent
│       │   ├── cleaning_agent.py       # 数据清洗 Agent
│       │   ├── crawler_agent.py        # 爬取 Agent
│       │   ├── insight_agent.py        # 洞察 Agent
│       │   ├── scheduler_agent.py      # 调度 Agent
│       │   └── trend_agent.py          # 趋势 Agent
│       ├── api/v1/                     # REST API 路由
│       │   ├── accounts.py             # 账号管理
│       │   ├── keywords.py             # 关键词管理
│       │   ├── tasks.py                # 任务管理
│       │   ├── data.py                 # 数据查询
│       │   └── system.py               # 系统状态
│       ├── infrastructure/
│       │   ├── crawler/                # 爬虫基础设施
│       │   │   ├── adapter.py          # 爬虫适配层
│       │   │   ├── config_mapper.py    # CLI 命令构建
│       │   │   └── process_manager.py  # 子进程管理
│       │   ├── database/               # 数据库层
│       │   │   ├── connection.py       # 连接管理
│       │   │   └── models.py           # ORM 模型
│       │   └── repositories/           # 数据仓储
│       ├── domain/                     # 领域模型
│       └── tasks/                      # Celery 任务
│           ├── celery_app.py           # Celery 配置
│           ├── crawl_tasks.py          # 爬取任务
│           ├── clean_tasks.py          # 清洗任务
│           └── schedule_tasks.py       # 定时调度任务
│
└── ../BeautyQA-vendor/MediaCrawler/      # MediaCrawler 爬虫引擎
    ├── main.py                         # MediaCrawler 入口
    ├── config/                         # 平台配置
    │   ├── base_config.py              # 基础配置
    │   ├── db_config.py                # 数据库配置
    │   └── xhs_config.py              # 小红书配置
    ├── media_platform/                 # 各平台爬虫实现
    │   ├── xhs/                        # 小红书
    │   ├── douyin/                     # 抖音
    │   ├── bilibili/                   # B站
    │   ├── weibo/                      # 微博
    │   └── ...
    ├── store/                          # 数据存储适配
    └── tools/                          # 工具集
```

---

## 常见问题

### Q: Playwright 浏览器安装失败？

如果 `playwright install chromium` 因网络问题失败，可设置镜像：

```powershell
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright"
playwright install chromium
```

### Q: PostgreSQL 连接失败？

1. 确认 Docker 容器正在运行：`docker ps`
2. 确认端口 5433 未被本地 PostgreSQL 占用
3. 检查 `backend/.env` 中 `DATABASE_URL` 的端口和密码

### Q: 子进程超时或卡死？

流水线已实现以下防护措施：
- 每个关键词独立子进程，互不阻塞
- qrcode 登录超时 15 分钟，cookie 模式超时 10 分钟
- Windows 下使用 `taskkill /F /T` 终止整个进程树（含浏览器子进程）
- 限制每笔记最多 10 条评论 (`--max_comments_count_singlenotes 10`)
- 评论并发数 2 (`--max_concurrency_num 2`)

### Q: Cookie 登录失败 "没有权限访问"？

Cookie 登录依赖浏览器保存的登录状态。如果状态过期，需要重新扫码登录一次：

```powershell
python run_pipeline.py --mode test --platform xhs --login-type qrcode
```

扫码成功后，后续关键词可继续使用 cookie 模式。

### Q: 如何添加新的爬取关键词？

编辑 `backend/config/trend-keyword.csv`，按现有格式添加新行。CSV 字段说明：

| 字段 | 说明 | 示例 |
|------|------|------|
| keyword | 主关键词 | 发酵赋能 |
| topic_cluster | 主题聚类 | ingredient_technology |
| trend_type | 趋势类型 | ingredient |
| suggested_platforms | 目标平台（\|分隔） | xiaohongshu\|douyin |
| query_variants | 查询变体（\|分隔） | 发酵赋能\|发酵成分 |

---

## 许可证

本项目仅供学习和研究目的使用。MediaCrawler 部分遵循其原始 [NON-COMMERCIAL LEARNING LICENSE](../BeautyQA-vendor/MediaCrawler/LICENSE)。
