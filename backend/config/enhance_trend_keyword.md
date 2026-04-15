# Skill: 美妆护肤趋势关键词扩充器 (Trend Keyword Expander for Beauty & Skincare)

## 1. Skill 基本信息

| 属性 | 内容 |
|------|------|
| 名称 | `expand_beauty_trend_keywords` |
| 用途 | 将原始趋势关键词（可能跨领域）扩充为聚焦美妆/护肤领域的搜索词列表，用于社交媒体爬虫精准抓取 |
| 输入 | 单个原始关键词 + 元数据（topic_cluster, trend_type, 可选的原始query_variants） |
| 输出 | 一组扩充后的搜索词（字符串数组），每个词均可直接用于 MediaCrawler 的关键词搜索 |

## 2. LLM 调用方式

使用 OpenAI 兼容接口（智谱 API），model 为 `glm-5.1`，需设置 `thinking: {"type": "disabled"}`。

### System Prompt

```
你是一个专门为美妆护肤领域社交媒体爬虫服务的关键词扩充专家。你的任务是根据用户提供的原始趋势关键词及其元数据，生成 3~6 个聚焦于美妆护肤领域的搜索词变体。

生成规则：

领域限定：
- 所有生成的搜索词必须明确指向护肤品、化妆品、个人护理相关内容。
- 如果原始关键词在其他领域也有高热度（例如"发酵"可用于食品、生物技术），必须通过添加领域限定词（如"护肤""化妆品""面膜""精华"）来消除歧义。
- 示例：原始词"发酵赋能" → 应产出"发酵赋能 护肤""发酵成分 化妆品""发酵原料 精华"等。

保留核心概念：
- 不改变原始关键词的核心语义，仅做上下文限定和同义扩展。
- 同义扩展可使用常见美妆术语（如"外泌体"可扩展为"外泌体 抗衰""EXOSOME 护肤"）。

适配平台搜索习惯：
- 生成的搜索词应适合在小红书、抖音、B站、微博等平台使用。
- 可使用自然语言短语（如"什么护肤品含外泌体"），但优先使用简短关键词组合（如"外泌体 面霜"），因为平台搜索更倾向于关键词匹配。

利用元数据指导扩展：
- 如果 trend_type = ingredient，可增加"成分""原料""含X的护肤品"等后缀。
- 如果 trend_type = claim（功效宣称），可增加"真的有效吗""测评""好用吗"等用户常见搜索后缀。
- 如果 topic_cluster 包含 risk，可增加"风险""副作用""避雷"等词。

避免过度扩展：
- 不要生成过于宽泛的词（如仅"护肤"），也不要生成与美妆完全无关的词。
- 不要重复已有的 existing_variants，但可基于它们优化或补充。

输出格式：
返回一个 JSON 对象，包含一个 expanded_keywords 数组，每个元素是一个字符串。
```

### User Prompt 模板

```
原始关键词: {original_keyword}
主题簇: {topic_cluster}
趋势类型: {trend_type}
已有变体: {existing_variants}

请生成扩充后的美妆护肤领域搜索词，严格按以下JSON格式返回：
{{"expanded_keywords": ["搜索词1", "搜索词2", "搜索词3"]}}
```

## 3. 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `original_keyword` | string | 是 | 原始关键词，如 '发酵赋能' |
| `topic_cluster` | string | 是 | 主题簇，如 'ingredient_technology' |
| `trend_type` | string | 是 | 趋势类型：ingredient / claim / scenario / category / risk_compliance |
| `existing_variants` | string[] | 否 | CSV中已有的 query_variants（管道分隔的字符串列表） |

## 4. 输出示例

### 示例 1：成分技术类

输入：
- original_keyword: "发酵赋能"
- topic_cluster: "ingredient_technology"
- trend_type: "ingredient"
- existing_variants: ["发酵赋能", "发酵成分", "发酵原料"]

输出：
```json
{
  "expanded_keywords": [
    "发酵赋能 护肤",
    "发酵成分 化妆品",
    "发酵原料 精华 面霜",
    "发酵护肤品 推荐",
    "微生物发酵 护肤"
  ]
}
```

### 示例 2：功效宣称类

输入：
- original_keyword: "快速美白"
- topic_cluster: "claim_risk_watch"
- trend_type: "claim"
- existing_variants: ["快速美白", "7天美白", "28天焕白"]

输出：
```json
{
  "expanded_keywords": [
    "快速美白 护肤品",
    "快速美白 真的吗",
    "快速美白 风险",
    "快速美白 副作用",
    "快速美白 避雷"
  ]
}
```

## 5. 系统集成流程

在 SchedulerAgent 调用 CrawlerAgent 之前，插入 KeywordExpanderAgent：

1. 从趋势关键词库读取一条关键词记录（含 keyword, topic_cluster, trend_type, query_variants）
2. 调用 KeywordExpanderAgent，通过 LLM 扩充关键词
3. 获取返回的 `expanded_keywords` 数组
4. 将原有 `query_variants` 与新生成的 `expanded_keywords` 合并去重
5. 将合并后的搜索词列表作为 `expanded_keywords` 传递给 CrawlerAgent / MediaCrawler 子进程
6. MediaCrawler 的 `--keywords` 参数支持逗号分隔的多关键词搜索
