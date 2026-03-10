# Beauty QA Advisor Proposal（正式结构版｜中文母稿）

## Title
**Beauty QA Advisor: 面向科学护肤与趋势审美协同优化的多智能体对话顾问系统**

## Abstract
本项目聚焦“科学护肤正确性”与“趋势审美时效性”之间的双目标冲突，提出一个基于多智能体编排的 QA 对话顾问系统。系统通过多源数据采集与趋势发现机制，结合高可信静态科学知识库，实现对用户问题的结构化推荐与解释输出；并以“生成-校验-蒸馏-回流”四步飞轮支持持续迭代。在方法上，我们将趋势定义从抽象概念转化为可计算指标（热度增速、跨平台一致性、持续性、新品关联度），并引入“科学/安全硬约束 + 趋势软优化”冲突解决策略。实验层面将设置科学-only、趋势-only、通用LLM三类 baseline，并通过消融实验验证趋势引擎、合规守门与飞轮机制的贡献。项目在有限企业数据供给下采用分级数据策略（P0/P1/P2）和合规边界约束，目标是构建可复现、可评估、可演示的毕业实践方案。

---

## 1. Motivation and Problem Context
### 1.1 场景背景
美业消费者决策呈现“专业理性 + 社媒潮流”双驱动特征。当前主流工具普遍偏向单目标：
- 科学导向系统：准确但更新慢；
- 趋势导向系统：更新快但专业可靠性不足。

### 1.2 核心矛盾
我们关注的核心矛盾是：
> 在动态趋势快速变化的环境下，如何维持科学可靠且可解释的个性化建议？

### 1.3 问题定义
在有限企业数据供给和合规约束下，构建一个既具科学可靠性、又具趋势响应能力的 QA 对话顾问系统。

---

## 2. Related Work and Gap
### 2.1 技术方案线（Scenario Solution Line）
- **Scientific-only QA / KG-RAG**：专业正确性高，但时效性不足。
- **Trend-only Recommender**：趋势响应快，但存在成分冲突与误导风险。
- **General LLM Assistant**：覆盖广，但容易幻觉，缺乏行业安全边界。

### 2.2 用户价值线（User Value Line）
现有消费者工具在“跟上趋势节奏 + 解决科学护肤问题”上存在体验裂缝：
- 建议可解释性弱；
- 风险边界不清晰；
- 对趋势更新反应不稳定。

### 2.3 研究缺口（Gap）
缺少一类可复现方案，能够**同时优化科学正确性与趋势时效性**，并在有限数据条件下持续迭代。

### 2.4 我们的改进（Our Improve）
- 双通道协同框架：Science Channel + Trend Channel；
- 趋势可计算定义与触发更新机制；
- 蒸馏飞轮与回放回归机制；
- 合规守门内生化（非事后补丁）。

---

## 3. Research Questions and Hypotheses
### RQ1
如何在多数据源条件下实现准实时更新，同时维持质量一致性与可追溯性？

### RQ2
如何定义 Trend 并将其转化为可执行推荐能力？

### RQ3
当 Trend 与科学知识冲突时，系统如何进行可解释决策？

### Hypotheses
- **H1**：引入趋势引擎后，Trend Freshness 显著提升。
- **H2**：引入合规守门后，Safety 指标显著提升。
- **H3**：引入飞轮回流后，回归集性能更稳定，遗忘率更低。

---

## 4. Method and System Design
### 4.1 Input / Output
**Input**：用户自然语言问题、肤质/诉求、预算、偏好、可选趋势偏好。  
**Output**：结构化建议（推荐项、科学依据、趋势依据、风险提示、免责声明）。

### 4.2 Data Flow
多源采集 -> 标准化 -> 趋势识别 -> 检索/推理 -> 合规过滤 -> 对话输出。

### 4.3 Core Components
1. **Data Ingestion Agents**：IP 热度、新品、社媒内容、口碑数据采集与清洗。  
2. **Trend Engine**：趋势识别、更新触发、趋势影响建模。  
3. **Science Knowledge Layer**：成分-功效-风险-法规知识。  
4. **Dialogue Orchestrator**：多角色协同与会话状态管理。  
5. **Safety/Compliance Gate**：风险规则审查 + LLM 二次检查。  
6. **Distillation Flywheel**：生成-校验-蒸馏-回流迭代。

---

## 5. Core Challenges and Technical Route
### 5.1 Challenge A: Multi-source Near-real-time Update
**问题**：如何保证 freshness 与 consistency 同时成立？  
**路线**：multi-agent ingestion + schema 标准化 + quality gate + source fallback。

### 5.2 Challenge B: Trend Discovery and Dynamic Update
**问题**：Trend 如何被定义、触发、更新并可用于推荐？  
**路线**：定义 `TrendScore` 并建立触发规则：

\[
TrendScore = \alpha \cdot growth_{7d} + \beta \cdot cross\_platform + \gamma \cdot persistence + \delta \cdot new\_product\_relevance
\]

当 `TrendScore > threshold` 触发增量更新（数据与模型双更新）。

### 5.3 Challenge C: Conflict Resolution (Trend vs Science)
**问题**：趋势建议与科学约束冲突时如何决策？  
**路线**：科学与安全作为硬约束，趋势作为软优化；输出冲突解释和保守替代建议。

---

## 6. Distillation and Iterative Learning
### 6.1 Four-step Flywheel
1. Teacher 生成候选样本  
2. 规则/知识一致性校验  
3. Student 蒸馏训练  
4. 误差回流（hard-case 池）

### 6.2 Anti-forgetting
- 固定回放集（每轮必测）；
- 历史高频问题回归门槛；
- 复发率监控。

---

## 7. Data Strategy and Compliance
### 7.1 MVP 数据维度
商品、成分、趋势、口碑、合规规则、弱画像。

### 7.2 数据供给策略
- P0：可训练包；
- P1：受限访问；
- P2：盲测包；
- 分层抽样 + 趋势补样，支持有限预算可持续迭代。

### 7.3 合规边界
去标识化、最小必要原则、用途限制、敏感表述拦截。

---

## 8. Evaluation Protocol
### 8.1 Baselines
- Baseline-A：Scientific-only
- Baseline-B：Trend-only
- Baseline-C：General LLM

### 8.2 Metrics
Correctness / Completeness / Safety / Trend Freshness / Latency / Explainability / Hallucination Rate

### 8.3 Ablation
- w/o Trend Engine
- w/o Compliance Gate
- w/o Distillation Flywheel
- w/o Replay

### 8.4 Feasibility Pilot (建议写入正式稿)
先做 30–50 条小样本预实验，验证双目标冲突真实存在，并初步验证改进方向可行。

---

## 9. Timeline and Milestones
- **M1（Week 1-2）**：问题定义冻结 + baseline 初版。
- **M2（Week 3-4）**：多源采集与趋势引擎打通。
- **M3（Week 5-6）**：飞轮迭代 + 消融实验。
- **M4（Week 7-8）**：结果汇总 + 正式报告与答辩材料。

---

## 10. Expected Contributions
1. 双目标协同 QA 顾问框架。  
2. 面向美业的 Trend 可计算定义与触发更新机制。  
3. 生成-校验-蒸馏-回流的多轮迭代机制。  
4. 可复现的课程实践评估协议（baseline + 消融 + 回归）。

---

## 11. Risks and Mitigation
- 数据噪声高 -> 质量门槛 + 人工抽检。
- 生成幻觉 -> 规则校验 + 一致性检查。
- 遗忘问题 -> 回放与回归门槛。
- 范围失控 -> MVP 范围冻结与阶段交付。

---

## 12. References（占位）
> 此处按导师格式补齐正式文献（不少于 8–12 条，含 benchmark/LLM bias/trend analysis/multi-agent orchestration/distillation）。
