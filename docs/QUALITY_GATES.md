# Quality Gates

这份清单用于投稿、交付或交给别人复现之前。每个 gate 都有命令或人工检查项。

## Gate 1. 本地环境

```powershell
econ-studio doctor --strict
```

要求：

- required files 存在；
- required imports 可用；
- CLI 能启动。

## Gate 2. 数据结构

```powershell
econ-studio data-audit --csv data\analysis_panel.csv --key unit_id --key year --outcome y --treatment d --cluster unit_id --fail-on-critical
```

不能带着 critical failure 继续跑模型。

人工还要检查：

- 数据来源；
- 合并日志；
- 删除样本原因；
- 变量口径；
- 是否存在重复 ID、重复年份或重复政策事件。

报告里的 data contract 也要看：分析粒度、join explosion 风险、分母边界和聚类层级必须和后续模型一致。

## Gate 3. 计量设计

```powershell
econ-studio identify --brief research_brief.yaml --output outputs\<session>\identify_strategy.md
econ-studio design-memo --brief research_brief.yaml --output outputs\<session>\design_memo.md
```

要求：

- 能解释为什么选这个策略；
- 能解释为什么不用其他策略；
- 剩余威胁写清楚；
- 稳健性不是事后凑出来的。

## Gate 3.5 上游 skills 和安全边界

```powershell
econ-studio skills plan --task full-paper
econ-studio skills audit --dir path\to\upstream-skill
```

要求：

- agent 知道本轮任务需要哪些上游 skills；
- 上游 skill 不复制进本仓库；
- 任何网络调用、环境变量读取、secret/SSH/browser data 风险都先写清楚；
- 缺失的 skill 标记为缺失，不假装已经加载。

## Gate 4. 代码骨架和复现

```powershell
econ-studio scaffold --strategy DiD --session <session> --lang stata
```

真实论文还要人工确认：

- 变量名已经替换；
- 数据路径可复现；
- seed、软件版本和包版本记录清楚；
- 表和图由脚本生成，不是手动改 Excel。

## Gate 5. 方法证据

```powershell
econ-studio verify --strategy DiD --analysis outputs\<session> --paper paper\draft.md --fail-under 6
```

常见红线：

- DiD 没有平行趋势或 event study；
- 错时 DiD 只用传统 TWFE；
- IV 没有 first-stage / weak-IV 诊断；
- RDD 没有操纵检验和 bandwidth 敏感性；
- 多结果/多分组没有多重检验处理；
- 聚类层级和政策处理层级不一致。

## Gate 5.5 证据账本和 claim

```powershell
econ-studio ledger audit --ledger outputs\<session>\evidence_ledger.json
econ-studio claim-audit --paper paper\draft.md --ledger outputs\<session>\evidence_ledger.json
econ-studio reviewer-gauntlet --paper paper\draft.md --ledger outputs\<session>\evidence_ledger.json
```

要求：

- 每个核心表图有 artifact path、code path、data source、sample、model、estimand 和 cluster；
- 每个显式 claim 能回到至少一个 ledger artifact；
- reviewer gauntlet 的方法、数据、引用、写作和复现问题已处理或明确列为待办；
- 没有把没有证据的机制、异质性或政策含义写成结论。

## Gate 6. 写作和图表

```powershell
econ-studio paper audit --paper paper\draft.md --fail-under 8
```

要求：

- 有明确的一句话贡献；
- 因果语言有识别假设和边界；
- 图表标题能说明样本、估计量、时间范围和不确定性；
- 不用“重要意义”“深刻洞见”“全面分析”这类空话替代证据；
- 不用 vague attribution 或 promotional language 代替具体文献和证据；
- 不保留作者年份占位符或 citation-needed。

## Gate 7. 引用

当前仓库只做静态 placeholder 检查。真实引用要另行核验：

- DOI 或期刊官网能打开；
- 文献标题、作者、年份匹配；
- 文献真的支持文中那句话；
- 没有把综述、方法文献、经验结果张冠李戴。

## Gate 8. 交付说明

交付给导师、合作者、客户或审稿人之前，最后写一段简短说明：

- 哪些模型和脚本已经实际运行；
- 哪些引用已经核验，哪些仍待核验；
- 哪些表图由脚本生成，输出路径在哪里；
- 哪些结论只能写成相关性、事件研究或描述性证据；
- 哪些限制需要在正文或附录中明说。
