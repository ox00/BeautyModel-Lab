# 工程映射表：从 TradingAgents 到 Beauty QA 顾问

## 1. 模块映射（核心）

| TradingAgents 模块 | 参考文件 | BeautyModel-Lab 对应模块建议 | 说明 |
|---|---|---|---|
| 图编排主入口 | `TradingAgents/tradingagents/graph/trading_graph.py` | `src/graph/beauty_graph.py` | 统一编排执行流程 |
| 图结构构建 | `TradingAgents/tradingagents/graph/setup.py` | `src/graph/setup.py` | 节点与条件边配置 |
| 条件逻辑 | `TradingAgents/tradingagents/graph/conditional_logic.py` | `src/graph/conditional_logic.py` | 决定走哪个分支 |
| 分析员角色 | `TradingAgents/tradingagents/agents/analysts/*` | `src/agents/analysts/*` | 科学分析/趋势分析/口碑分析 |
| 研究/辩论角色 | `TradingAgents/tradingagents/agents/researchers/*` | `src/agents/researchers/*` | 正反观点对撞 |
| 风险管理 | `TradingAgents/tradingagents/agents/managers/risk_manager.py` | `src/agents/managers/compliance_manager.py` | 合规与风险审查 |
| LLM 工厂 | `TradingAgents/tradingagents/llm_clients/factory.py` | `src/llm_clients/factory.py` | 多模型切换 |
| 数据源路由 | `TradingAgents/tradingagents/dataflows/interface.py` | `src/dataflows/interface.py` | 多数据源抽象与回退 |
| 默认配置 | `TradingAgents/tradingagents/default_config.py` | `config/default_config.py` | 中央配置项 |

## 2. 业务角色映射

| 交易角色 | 美业顾问角色 |
|---|---|
| Fundamentals Analyst | 成分/功效科学分析员 |
| Social/News Analyst | 趋势与口碑分析员 |
| Research Manager | 顾问结论协调器 |
| Trader | QA 建议生成器 |
| Risk Manager | 合规审查员 |

## 3. Beauty 会话流程建议（MVP）
1. 用户输入：肤质/诉求/预算/偏好 + 可选趋势关键词。  
2. 分析节点：
   - 科学分析：成分适配与风险
   - 趋势分析：热点词与时效变化
   - 口碑分析：用户反馈与负面风险词
3. 对撞节点：正反观点简短辩论（避免单一路径偏差）。  
4. 顾问节点：输出候选推荐 + 解释理由 + 替代方案。  
5. 合规节点：敏感表述拦截/替换。  
6. 输出节点：结构化答复（建议、理由、注意事项、免责声明）。

## 4. 最小目录建议（可作为下一步工程初始化）
```text
BeautyModel-Lab/
  src/
    graph/
    agents/
      analysts/
      researchers/
      managers/
    dataflows/
    llm_clients/
    services/
  config/
  eval/
  docs/
```

## 5. 三阶段落地计划（建议）
- Phase A（1-2周）：
  - 建立 graph + 3个基础分析节点 + 1个合规节点
  - 打通单轮 QA 闭环
- Phase B（3-4周）：
  - 增加“对撞节点”和回放评测
  - 引入多源数据路由
- Phase C（5-6周）：
  - 接入蒸馏飞轮（生成-校验-蒸馏-回流）
  - 完成基线对比和消融实验

## 6. 与现有文档关系
- 数据维度与采样：`docs/08-技术方案-数据维度与采样设计.md`
- 蒸馏飞轮：`docs/09-技术方案-蒸馏与多轮对撞飞轮.md`
- 实验里程碑：`docs/10-实验设计与里程碑.md`
