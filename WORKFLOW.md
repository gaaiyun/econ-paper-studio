# 五阶段工作流（econ-paper-studio）

把一篇计量实证论文从想法到投出去拆成五个阶段。每个阶段都有"何时跳过"的明确条件，**不是教条**。

```
question → design → execute → verify → write
```

其中 `data-audit` 是 execute 前的硬闸门：先检查分析样本结构，再让 Stata/R/Python 跑模型。

---

## 总体设计哲学

我做这套流程的核心想法是：**别让 agent 跳过思考直接跑代码**。

很多人用 AI 做计量研究时的常见失败：

1. 把数据扔给 AI，"帮我跑个 DiD" → 拿到一个不知道该不该信的系数
2. 出了显著系数就直接写 results → 写完才发现被审稿人指出 staggered TWFE 负权重问题
3. 跳过文献综述，"我先做实证再补文献" → 后期发现别人 5 年前已经做过同样的事
4. R&R 时找不到当时怎么做的、为什么这么做 → 重新跑、重新想，浪费几周

这五个阶段对应这五种失败模式：

| 阶段 | 防的失败 |
|---|---|
| 1. question | 没想清楚就开干 → "找显著性" |
| 2. design | 选错识别策略 → 内生性问题没解决 |
| 3. execute | 写完代码无法复现 → 自己半年后看不懂 |
| 4. verify | 漏了关键稳健性 → 被审稿人 desk reject |
| 5. write | 写作风格不一致 → editor 直接打回 |

---

## 阶段 1：question — 研究问题澄清

**何时跳过**：你已经有一篇成熟的论文要复现/延续，研究问题已定。

**何时使用**：
- 开题、JMP、毕业论文起步
- 拿到一份新数据但不知道做什么
- 有粗略想法但说不清"我到底想回答什么"

**用什么**：[`RESEARCH_QUESTION.md`](./RESEARCH_QUESTION.md) 里的核心五问。

**核心五问**：

### Q1：研究问题是什么（**一句话**，X → Y 形式）

要求一句话写完。"X 对 Y 的因果效应是什么"。

**反模式**：
- "我想研究最低工资和就业的关系" → 不够，是 effect on level 还是 elasticity？长期还是短期？
- "我想研究 AI 对劳动市场的影响" → 太大，必须收窄到具体 X 和 Y

**正确示例**：
- "提高联邦最低工资对青少年（16-19 岁）就业率的影响"
- "中国 2014 年沪港通开通对内地上市公司股价信息含量（PIN 测度）的影响"

### Q2：贡献是什么（counterfactual world test）

如果你的论文不存在，世界会缺少什么知识？一个段落写完。

**测试**：
- 这个问题别人做过吗？做到什么程度？
- 你能贡献的是什么——新数据？新方法？新机制？反例？

如果回答不出来，回到文献综述（调用 `literature-review` skill）。

### Q3：数据条件

- 你已经有的：什么数据集、覆盖什么、变量是否齐
- 你需要的：缺什么、能不能拿到、获取成本
- 数据频率（年/季/月）和单位（个体/省/行业）

如果数据条件不支持你的识别策略（比如要做 DiD 但只有横截面），**第二阶段必须重新选策略**。

### Q4：识别挑战

你的研究问题面临什么内生性威胁？

- 反向因果？（Y 影响 X）
- 遗漏变量？（什么 Z 同时影响 X 和 Y）
- 测量误差？
- 样本选择？

把每个威胁写下来，第二阶段的识别策略就是为了消除这些。

### Q5：目标期刊 + Deadline

- Top 5 (AER/QJE/JPE/Restud/Econometrica) vs. Top field (AEJ/JoE/RES/JBES/JAE) vs. Field
- JMP 时间表 / R&R 截止时间 / 会议投稿截止

期刊定位决定**写作风格、稳健性深度、模型复杂度**——top 5 要求每个角度都堵死，field 期刊允许更聚焦。

**Stage 1 产出**：把上面 5 个问题整理成 `research_brief.yaml`。可以直接参考 `examples/case-min-wage-did/research_brief.yaml`，下一个阶段用 `--brief` 读取。

---

## 阶段 2：design — 识别策略选择

**何时跳过**：你已经清楚要用 DiD/IV/RDD 中的哪个，并且知道那个方法的现代版本（不是 2010 年的 TWFE）。

**何时使用**：
- 你只知道"我应该用因果推断"但不确定具体哪种
- 你听过 Sun-Abraham / Callaway-Sant'Anna / HonestDiD 但不确定该不该用
- 你想确认你选的策略是否真的解决了 Q4 的识别威胁

**用什么**：

```bash
python scripts/identify_strategy.py --brief outputs/<session>/research_brief.yaml
```

脚本会基于 brief 里的数据结构、识别策略雏形、自然实验和识别威胁走一个决策树，推荐 1-2 个候选策略，并指出每个的关键 trade-off。

### 决策树概要

```
有处理 (treatment)？
├─ Yes
│   ├─ 横截面对比（截面）
│   │   └─ Matching / DML
│   ├─ 处理变量在 unit 和 time 上都有变化
│   │   └─ DiD（→ did-analysis skill）
│   │       ├─ 二元 + 同时处理 → 经典 TWFE OK
│   │       └─ Staggered adoption → CS / Sun-Abraham / BJS
│   ├─ 单一处理单位 vs 多控制单位
│   │   └─ Synthetic Control（→ causal-inference SCM 章节）
│   └─ 处理由某个 running variable 的阈值决定
│       └─ RDD（→ causal-inference RDD 章节）
└─ No (只是观察)
    ├─ 有外生 instrument
    │   └─ IV（→ causal-inference IV 章节）
    └─ 只能 conditional on observables
        └─ DML / Matching（坦诚说选择 on observables 弱点）
```

### Stage 2 产出

`outputs/<session>/identify_strategy.md`：

```markdown
# Identification Strategy: <session>

## Chosen: <strategy name>

## Rationale
- 为什么选这个（基于 RQ.md 的 Q3+Q4）
- 排除的其他候选 + 排除原因

## Key Threats this Strategy Addresses
- <Q4 威胁 1> ← 通过 <机制> 解决
- <Q4 威胁 2> ← 通过 <机制> 解决

## Remaining Threats (Stage 4 必查)
- <剩余威胁 1>，对应稳健性 <test name>
```

---

## 阶段 3：execute — 跑数据 + 出结果

**何时跳过**：从来不跳过。

**用什么**：

```bash
python scripts/data_audit.py --csv data/analysis_panel.csv \
  --key city_id --key year \
  --outcome youth_employment_rate \
  --treatment minimum_wage_increase \
  --cluster city_id \
  --fail-on-critical

python scripts/scaffold.py --strategy DiD --session my-mw-study
```

会生成 Stata + R 双语言骨架：

```
outputs/my-mw-study/
├── do/
│   ├── 00_master.do          # 主调度，按顺序 do 后面的
│   ├── 01_clean.do           # 数据清洗
│   ├── 02_descriptive.do     # 描述统计 + 平衡表
│   ├── 03_main.do            # 主回归 (reghdfe)
│   └── 99_export.do          # 结果导出 (estout/esttab)
└── R/
    ├── 00_main.R             # 主调度
    ├── 01_did_csa.R          # CS 估计 + Sun-Abraham
    ├── 02_event_study.R      # 事件研究图
    ├── 03_honest_did.R       # HonestDiD 敏感性
    └── 99_plots.R            # 高质量出图
```

**核心设计**：
- **先审数据结构**：检查重复键、缺失、处理变量变化、结果变量类型和聚类数量
- **Stata 做你熟的**：reghdfe + estout（有传统的论文表样式）
- **R 做 Stata 不擅长的**：现代 DiD 估计器、HonestDiD、ggplot 出版级图
- **00_master 文件**：保证从原始数据到 final tables/figures 一行命令复现

代码细节由 agent 调用 `stata` 和 `did-analysis` skill 完成。这个 scaffold 只生成骨架文件 + 注释占位符。

### Stage 3 产出

`data_audit.md` + `outputs/<session>/tables/` + `outputs/<session>/figures/` + 每个脚本顶部的 docstring 说明它在做什么。

---

## 阶段 4：verify — 稳健性检验

**何时跳过**：内部讨论稿、prototype。

**何时使用**：要投稿、要给老板看、要给客户提交。

**用什么**：

```bash
python scripts/robustness_checks.py \
  --strategy DiD \
  --analysis outputs/<session> \
  --output outputs/<session>/verify_report.md
```

会基于策略扫描分析脚本和论文文本，生成一份**针对性的**静态核验报告。它是离线质量闸门，不替代真实 Stata/R/Python 运行或外部引用核验。

### DiD 案例的清单（典型）

```markdown
- [ ] Pre-trend test (event-study with k pre-periods)
- [ ] Goodman-Bacon decomposition (negative weight diagnosis)
- [ ] CS estimator (Callaway-Sant'Anna 2021)
- [ ] Sun-Abraham estimator (2021)
- [ ] BJS estimator (Borusyak-Jaravel-Spiess 2024)
- [ ] HonestDiD (Rambachan-Roth 2023): smoothness + magnitude restrictions
- [ ] Placebo test 1: false treatment date (3 years before)
- [ ] Placebo test 2: placebo outcome (something that shouldn't be affected)
- [ ] Subgroup heterogeneity (treatment effect by X = ...)
- [ ] Sample restriction robustness (drop top decile of size, drop early adopters)
- [ ] Outcome winsorization (1% / 99%)
- [ ] Standard error clustering (unit / unit-time / Conley)
- [ ] Multi-outcome correction (Bonferroni / Romano-Wolf, if K > 5)
```

每一项都有"如何做 + 该用哪个 skill"的注释。Agent 按清单逐项执行，把结果记录到 `outputs/<session>/robustness/` 下。

**反模式**：跳过 HonestDiD（因为麻烦）→ 审稿人指出 → 大改。

### Stage 4 产出

`robustness/CHECKLIST.md` + 每项的产物（多张表、多张图）。

---

## 阶段 5：write — 论文写作

**何时跳过**：只是内部分析报告，不是论文。

**用什么**：`scripts/paper_pipeline.py` 生成大纲和审计草稿，`scripts/session.py` 记录版本和审稿意见。

```bash
python scripts/paper_pipeline.py outline \
  --brief examples/case-min-wage-did/research_brief.yaml \
  --output outputs/my-mw-study/paper_outline.md

python scripts/paper_pipeline.py audit \
  --paper paper/draft.md \
  --output outputs/my-mw-study/paper_audit.md \
  --fail-under 8
```

**关键编排顺序**（这是 Cochrane 等的反复强调）：

1. **先写 results section**（你最确定的内容）
2. **再写 method section**（解释 results 怎么来的）
3. **再写 introduction**（hook + research question + value added + roadmap）
4. **再写 conclusion**（重述贡献 + 未来方向）
5. **最后写 abstract**（从 intro 提炼）

**为什么这个顺序**：因为 intro 的论证逻辑取决于 results 的强度。先写 intro 等于在还没有结果时编辑营销文案。

### Stage 5 产出

```
outputs/<session>/paper/
├── paper_outline.md
├── paper_audit.md
├── v1/
│   ├── main.tex
│   ├── tables.tex
│   └── figures.tex
├── v2/                       # 改完一轮
└── final/                    # 投稿版
```

### R&R 流程

```bash
python scripts/session.py add-review my-mw-study \
  --version r1 \
  --letter referee_letter.pdf \
  --decision major
```

当前版本先把审稿意见登记进 session manifest 和 `CHANGELOG.md`。点对点 response 生成属于后续路线图；不要在当前版本中假装已经自动生成了修改位置。

### 写作质检边界

`paper audit` 会检查核心章节、贡献句、引用占位符、空泛填充语、因果过度声称和图表标题。它不会证明引用真实，也不会证明文献支持具体 claim。真实引用必须继续通过 DOI、期刊官网、Crossref/OpenAlex/Semantic Scholar 或人工阅读核验。

---

## 跨阶段约束

### reproducibility-first

每个阶段的产物都必须是**可复现包**的一部分。session 目录就是天然的 replication package：

```bash
python scripts/session.py show my-mw-study
python scripts/robustness_checks.py --strategy DiD --analysis outputs/my-mw-study
```

当前版本把 session 目录作为 replication package 的雏形。正式打包功能仍是后续路线图；人工打包时应该包含：
- 所有原始/中间/最终数据（或数据获取脚本）
- 所有 do 文件 + R 脚本
- 一个 `00_master.do` / `00_master.R` 串起来
- README 说明运行环境（Stata 18, R 4.3, 包版本）
- 论文 PDF + tables/figures 的源文件

### journal-aware

不同期刊对 robustness 深度、code release、数据 transparency 要求不同。`references/journal-style-guide.md` 列了主要期刊的差异。

### no-magic-cleaning

数据清洗的每一步都要在 do/R 文件里显式写出来。**绝不允许 Excel 手改**——R&R 时无法解释为什么某些观测被删了。

---

## 跳过条件速查

| 场景 | 推荐流程 |
|---|---|
| 复现别人的论文 | 跳 1+2，直接 execute |
| 延续自己之前论文的 next step | 简化 1，重做 2 |
| JMP / 毕业论文从 0 开始 | 完整 5 阶段 |
| 已有结果，要开始写 | 跳 1-4，直接 write |
| R&R 改稿 | 跳 1-3，重点 4+5（referee_response） |
| 数据探索性分析 | 1+3 即可，不写论文跳 5 |

---

## 命令速查

```bash
# 初始化项目
python scripts/session.py init my-mw-study \
  --rq "Does the federal minimum wage increase reduce teen employment?" \
  --strategy DiD --target-journal "AEJ:Applied"

# Stage 2: 识别策略选择
python scripts/identify_strategy.py --brief examples/case-min-wage-did/research_brief.yaml \
  --output outputs/my-mw-study/identify_strategy.md

# Stage 3: 生成代码骨架
python scripts/data_audit.py --csv examples/case-min-wage-did/panel_sample.csv \
  --key city_id --key year --outcome youth_employment_rate \
  --treatment minimum_wage_increase --cluster city_id --min-clusters 3

python scripts/scaffold.py --strategy DiD --session my-mw-study

# Stage 4: 离线质量核验
python scripts/robustness_checks.py \
  --strategy DiD \
  --analysis outputs/my-mw-study \
  --output outputs/my-mw-study/verify_report.md

# Stage 5: 写作大纲和草稿审计
python scripts/paper_pipeline.py outline \
  --brief examples/case-min-wage-did/research_brief.yaml \
  --output outputs/my-mw-study/paper_outline.md

python scripts/paper_pipeline.py audit \
  --paper examples/case-min-wage-did/draft_excerpt.md \
  --output outputs/my-mw-study/paper_audit.md

# 看历史
python scripts/session.py show my-mw-study
```

或者用统一 CLI：

```bash
econ-studio init my-mw-study --rq "..." --strategy DiD
econ-studio identify --brief examples/case-min-wage-did/research_brief.yaml
econ-studio data-audit --csv examples/case-min-wage-did/panel_sample.csv --key city_id --key year
econ-studio scaffold --strategy DiD --session my-mw-study
econ-studio verify --strategy DiD --analysis outputs/my-mw-study
econ-studio paper audit --paper examples/case-min-wage-did/draft_excerpt.md
econ-studio add-review my-mw-study --version r1 --letter letter.pdf --decision major
```
