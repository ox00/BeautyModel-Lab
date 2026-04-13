# 趋势监控输入说明（给工程同学）

这个目录放“趋势报告 -> 监控关键词 -> agents 采集任务”的中间输入文件。

当前核心文件：
- `README_cn.md` - 工程接入说明
- `ENGINEERING_TASK_SPLIT_cn.md` - 工程任务拆分建议
- `2026-04-13-report-registry.csv` - 报告登记表
- `2026-04-13-trend-keyword-seed.csv` - 趋势关键词种子表

目标很直接：
- 给监控 agents 一套可落地的趋势输入
- 让工程侧知道哪些词能直接抓，哪些词先不要过度扩展
- 保留来源、时间、平台建议，方便后续做持续监控

## 文件各自负责什么

### 1. `report-registry`
作用：
- 记录每份报告的基本信息
- 标明它是月报、年报还是专题报告
- 标明当前文本可提取性高不高

工程上怎么用：
- 先按 `extractability` 过滤数据来源
- `high / medium` 可以继续做关键词扩展
- `low` 先只保留标题级主题，不要强行抽细词

### 2. `trend-keyword-seed`
作用：
- 给数据监控 agents 一批已经整理过的趋势关键词种子
- 每个词都带来源、时间属性、主题分类、优先级、推荐平台和查询变体

工程上怎么用：
- 不要把它当最终热词列表
- 它是任务输入种子，用来继续扩 query、分平台采集、做趋势追踪

### 3. `ENGINEERING_TASK_SPLIT_cn.md`
作用：
- 把当前输入拆成具体工程模块和任务卡
- 帮工程同学快速判断第一阶段先做什么、不该先做什么

工程上怎么用：
- 先按文档里的模块拆开发任务
- 再按第一阶段范围做最小可运行版本

## 最小接入方式

建议按下面顺序接：

1. 读取 `report-registry.csv`
- 先过滤 `extractability in (high, medium)`
- 把 `low` 的报告只当“一级主题来源”

2. 读取 `trend-keyword-seed.csv`
- 用 `report_id` 关联回报告元数据
- 优先保留 `priority=high`
- 第一轮优先保留 `confidence=high`

3. 按 `suggested_platforms` 拆任务
- 一个关键词可以对应多个平台
- `suggested_platforms` 用 `|` 分隔，拆成多条平台任务

4. 按 `query_variants` 扩 query
- `query_variants` 也是 `|` 分隔
- 可以直接拆成查询词列表，不用先自己造词

5. 输出标准化采集结果
- 每条结果至少保留：`keyword_id`、`platform`、`query`、`capture_date`、`observed_signal`、`source_url/source_id`
- 如果后面要做趋势聚类，额外保留 `normalized_keyword`、`topic_cluster`

## 推荐任务拆分方式

### 先按时间属性分任务
- `monthly`
  - 用于月度趋势追踪
- `annual`
  - 用于稳定主题监控
- `special_topic`
  - 用于专题监控

### 再按主题类型分任务
- `ingredient`
  - 成分 / 原料趋势
- `claim`
  - 宣称和功效话题
- `category`
  - 品类和类目趋势
- `scenario`
  - routine、场景、消费趋势
- `risk_compliance`
  - 高风险或争议信号

### 最后按平台拆采集任务
- `douyin`
  - 更适合追平台月报、类目、品类、热点表达
- `xiaohongshu`
  - 更适合追成分讨论、使用场景、用户口碑
- `taobao`
  - 更适合做商品和宣称验证
- `industry_news`
  - 更适合做原料、法规、行业趋势补充

## 字段约定

重点字段：
- `keyword`
  - 原始关键词
- `normalized_keyword`
  - 归一化后的主题名，后续方便聚类
- `topic_cluster`
  - 建议聚到哪个主题簇
- `trend_type`
  - 关键词属于哪类趋势任务
- `priority`
  - 建议先抓哪些词
- `confidence`
  - 当前这个词是不是来自明确可读证据，还是偏标题/人工整理
- `suggested_platforms`
  - 推荐抓取平台，`|` 分隔
- `query_variants`
  - 推荐直接拿去做采集扩展的变体，`|` 分隔
- `crawl_goal`
  - 这个词主要用于发现趋势、验证市场，还是监控风险
- `risk_flag`
  - 是否属于高风险监控词

字段值建议这样处理：
- `priority`
  - `high` 先抓
  - `medium` 第二轮抓
  - `low` 作为补充
- `confidence`
  - `high` 可以直接进自动任务
  - `medium` 建议先轻量人工抽检
- `risk_flag`
  - `high` 的词建议单独走风控/宣称监控链路

## 建议的 agents 输出格式

建议每条采集结果至少有这些列：
- `run_date`
- `keyword_id`
- `keyword`
- `normalized_keyword`
- `platform`
- `query`
- `source_type`
- `source_title`
- `source_url`
- `observed_signal`
- `engagement_or_heat`
- `capture_note`

如果工程上暂时不想做全量结构，最少也要保留：
- `keyword_id`
- `platform`
- `query`
- `source_url`
- `capture_date`

## 第一轮执行建议

- 先抓 `priority=high`
- 先抓 `confidence=high`
- 先从 `ingredient`、`claim`、`risk_compliance` 三类开始
- 对 `extractability=low` 的报告，不要自动补太多细词
- 先保留“一级主题词 + 平台类目词”，后面再增量扩展

当前最值得优先交给 agents 的方向：
- 原料创新趋势
  - 外泌体、发酵赋能、长寿护肤、神经美容、防晒原料创新
- 平台类目趋势
  - 护肤、彩妆、个护、面部护肤、防晒、洗发护发
- 风险监控趋势
  - 快速美白、热门趋势 vs 科学安全

## 不建议这样用

- 不要把这份表直接当“最终热词榜”
- 不要对 `extractability=low` 的报告自动生很多二级词
- 不要把 `query_variants` 当标准词表，它是采集扩展输入，不是归一化标签

## 当前限制

- 这版词库是“可用的第一版种子”，不是穷尽版
- 后续如果需要更细的月度热词，要么做 OCR，要么人工补录
