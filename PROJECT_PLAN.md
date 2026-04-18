# 项目规划与任务拆解

> 配合 [`../design agent/RESEARCH_REPORT.md`](../design%20agent/RESEARCH_REPORT.md) 食用。

---

## 设计原则

1. **不重造轮子** — 已有 5 个项目做得比我们好（StatsPAI / academic-research-skills / superpowers / sshtomar / dylantmoore），我们做 **adapter + 编排层**
2. **本地优先** — 中文用户、Stata 用户、中国期刊场景
3. **可裁剪** — 五阶段不强制走完，每阶段有"何时跳过"
4. **可测试** — 每个核心脚本都要有 dry-run 模式 + pytest 单测
5. **可复现** — session 管理 + manifest + CHANGELOG，每一版可追溯

---

## 五阶段工作流详细设计

### 阶段 1：question（研究问题澄清）

**对标**：design-image-studio 的 BRAINSTORM.md + Imbad0202 academic-research-skills 的 deep-research socratic 模式

**何时跳过**：研究问题已经很明确（有 brief + 期刊定位 + 识别策略思路），直接进 design

**何时使用**：用户只说"我想研究最低工资对就业的影响"

**核心五问**：

1. **研究问题**：你的核心问题是什么？最好能用一句"X 对 Y 的因果效应"说清。如果说不清，就是没想清楚。
2. **目标贡献**：在已有文献里你要补什么？是新场景（中国 vs 欧美）/新方法（CS-DiD vs 传统 TWFE）/新机制（中介效应）/新政策含义？
3. **目标期刊定位**：CSSCI/CSI 一区？AER/QJE？还是工作论文先放 SSRN？这决定 sample / 方法严谨度 / 写作风格。
4. **数据可得性**：你有什么数据？面板还是横截面？颗粒度（个人/企业/城市/省）？时间跨度？
5. **识别策略雏形**：你目前想用什么方法？DiD/RDD/IV/SCM/Matching？为什么这个方法适合？

**输出**：`research_brief.yaml` —— 结构化 brief，下游所有阶段都读它

**产物文件**：`RESEARCH_QUESTION.md`（模板）+ `templates/research_brief.yaml`（schema）

---

### 阶段 2：design（识别策略选择）

**对标**：sshtomar 社会科学 skills 的 DID skill + StatsPAI 的方法选择器

**何时跳过**：识别策略已确定且文献基准清楚

**何时使用**：用户问"我这个数据应该用什么方法？" 或 "我想用 DiD 但不知道是不是合适"

**核心能力**：决策树脚本 `identify_strategy.py`

```
输入：research_brief.yaml + 数据描述
        ↓
┌─────────────────────────────────────────┐
│ 1. 治疗变量类型？                        │
│    - 二值且不可逆 → 标准 DiD          │
│    - 连续/多值/可逆 → 高级 DiD/SCM    │
│    - 选择性接受 → IV/Matching         │
│                                         │
│ 2. 是否有 cutoff？                      │
│    - 是 → RDD                         │
│    - 否 → 跳过                        │
│                                         │
│ 3. 时间结构？                           │
│    - 单时点 → DD                      │
│    - 多时点 + 同期治疗 → 标准 TWFE    │
│    - 多时点 + 错时治疗 → CS-DiD/SA    │
│                                         │
│ 4. 控制组怎么找？                       │
│    - 自然对照 → DiD                   │
│    - 需要构造 → SCM                   │
│    - 需要匹配 → PSM/Mahalanobis       │
└─────────────────────────────────────────┘
        ↓
输出：strategy_recommendation.md
  - 推荐方法 + 备选方案
  - 文献基准（哪些经典论文用了类似方法）
  - 需要做的稳健性检验清单
  - StatsPAI 函数调用预演（如 `sp.callaway_santanna(...)`）
```

**产物文件**：
- `scripts/identify_strategy.py` — 决策树主脚本
- `references/strategy_decision_tree.md` — 完整决策树文档
- `references/methods/` — 每个方法（DID/RDD/IV/SCM/PSM/DML）单独文档，含
  - 核心假设
  - 文献基准（≥3 篇经典论文）
  - StatsPAI 函数对照表
  - 常见 pitfall

---

### 阶段 3：execute（生成代码骨架）

**对标**：dylantmoore stata-skill + StatsPAI

**核心能力**：根据策略生成 Stata/R/Python 三语 do-file 骨架

```
输入：strategy_recommendation.md + 数据列名
        ↓
┌─────────────────────────────────────────┐
│ scaffold_dofile.py 生成：                │
│                                         │
│  1. 数据导入 + 描述性统计                │
│  2. 平衡性检验                          │
│  3. 主回归（带 cluster SE）             │
│  4. 平行趋势/安慰剂/RD bandwidth 等     │
│  5. 异质性分析                          │
│  6. 机制分析（中介/分组）                │
│  7. 表 1（描述性统计）                  │
│  8. 表 2（主结果，含 multiple specs）    │
│  9. 图 1（事件研究/回归不连续图）       │
│  10. 表 3-N（稳健性检验）               │
│                                         │
│ 三种语言可选：                           │
│  - Stata（默认，国内最广）              │
│  - R（fixest / did 生态）               │
│  - Python（StatsPAI 一站式）            │
└─────────────────────────────────────────┘
        ↓
输出：analysis/
       ├── 01_setup.do (or .R / .py)
       ├── 02_descriptive.do
       ├── 03_main.do
       ├── 04_robustness.do
       ├── 05_heterogeneity.do
       └── 06_tables_figures.do
```

**产物文件**：
- `scripts/scaffold_dofile.py` — 主生成器
- `templates/stata/` — Stata 模板（基于 reghdfe / csdid / rdrobust 等）
- `templates/r/` — R 模板
- `templates/python_statspai/` — Python + StatsPAI 模板

---

### 阶段 4：verify（稳健性检验）

**对标**：sshtomar regression-diagnostics + Imbad0202 integrity verification + claesbackman 因果过度声称检测

**核心能力**：自动跑稳健性 + 检测过度声称

```
robustness_checks.py：
├── 必做检查（critical）
│   ├── 平行趋势检验（DiD）
│   ├── McCrary 密度检验（RDD）
│   ├── 弱工具变量检验（IV）
│   ├── Cluster SE 是否使用
│   ├── 是否存在多重比较未校正（Bonferroni / Holm）
│   └── 主样本删减后系数是否稳定
├── 推荐检查（high）
│   ├── 安慰剂检验（虚假治疗组）
│   ├── 异质性效应（不同子样本）
│   ├── 不同 bandwidth/cluster level/控制变量集
│   ├── HonestDiD 敏感性分析
│   └── 选择性偏误（Heckman / Lee bounds）
└── 自动产出 verify_report.md
    ├── 过度声称检测：检查文本中"causes/effect/leads to"使用是否过度
    ├── 表/图与文本一致性检查
    ├── 引用 vs 原文一致性（Semantic Scholar API）
    └── 对照 strategy_recommendation.md 检查清单是否走完
```

**产物文件**：
- `scripts/robustness_checks.py` — 主检查器
- `references/robustness_protocols/` — 每个检查的协议文档
- `templates/verify_report.md` — 报告模板

---

### 阶段 5：publish（论文写作 + R&R）

**对标**：Imbad0202 academic-paper（10 modes）+ flonat /proofread + 降 AI 味 skills

**核心能力**：
1. 论文章节模板（含 IMRaD / 文献综述 / 政策报告等中国期刊常见结构）
2. session 管理（每版论文 + verify 报告 + reviewer response 链起来）
3. R&R response 起草（点对点回应）
4. 引用验证（Semantic Scholar API）
5. 降 AI 味（去掉 "It is worth noting that" / "Furthermore" 等典型 AI 套路）

```
paper_session.py：
├── init <paper-name> --venue <CSSCI/SSCI/working>
├── add --version v1 --paper paper_v1.docx --note "first draft"
├── verify --paper paper_v1.docx  # 跑引用验证 + AI 味检测
├── add-review --version r1 --reviewers "审稿人1.docx" "审稿人2.docx"
├── draft-response --version r1   # 自动生成 response 草稿
├── add --version v2 --paper paper_v2.docx --note "addressed R1/R2"
└── promote --version v2          # 标记终稿
```

**产物文件**：
- `scripts/paper_session.py` — session 管理器
- `templates/paper/` — 论文章节模板
  - `01_introduction.md`
  - `02_literature.md`
  - `03_data.md`
  - `04_methodology.md`
  - `05_results.md`
  - `06_discussion.md`
  - `07_conclusion.md`
- `templates/response_to_reviewers.md` — R&R response 模板
- `references/anti_ai_phrases.md` — 中英文 AI 味词组黑名单

---

## 项目目录结构（最终）

```
G:\计量经济学实证和论文agent\
├── README.md                           ✅ 已创建
├── PROJECT_PLAN.md                     ✅ 你正在看
├── SKILL.md                            ⏳ 待创建（Cursor/Claude Code skill 入口）
├── WORKFLOW.md                         ⏳ 待创建（五阶段总章程）
├── RESEARCH_QUESTION.md                ⏳ 待创建（阶段 1 模板）
├── INSTALL_CN.md                       ⏳ 待创建
├── CHANGELOG.md                        ⏳ 待创建
├── LICENSE                             ⏳ 待创建（MIT）
├── pyproject.toml                      ⏳ 待创建
├── requirements.txt                    ⏳ 待创建
├── .env.example                        ⏳ 待创建
├── .gitignore                          ⏳ 待创建
│
├── scripts/                            ⏳ 待创建
│   ├── __init__.py
│   ├── identify_strategy.py            # 阶段 2
│   ├── scaffold_dofile.py              # 阶段 3
│   ├── robustness_checks.py            # 阶段 4
│   ├── paper_session.py                # 阶段 5
│   └── cli.py                          # 统一 econ-studio 入口
│
├── references/                         ⏳ 待创建
│   ├── strategy_decision_tree.md
│   ├── methods/
│   │   ├── did.md
│   │   ├── rdd.md
│   │   ├── iv.md
│   │   ├── scm.md
│   │   ├── psm.md
│   │   └── dml.md
│   ├── robustness_protocols/
│   │   ├── parallel_trends.md
│   │   ├── placebo.md
│   │   ├── multiple_testing.md
│   │   └── ...
│   └── anti_ai_phrases.md
│
├── templates/                          ⏳ 待创建
│   ├── research_brief.yaml
│   ├── stata/
│   ├── r/
│   ├── python_statspai/
│   ├── paper/
│   ├── verify_report.md
│   └── response_to_reviewers.md
│
├── examples/                           ⏳ 待创建
│   ├── README.md
│   ├── case-min-wage-did/              # 最低工资 DiD 案例
│   ├── case-rdd-college/               # 高考分数线 RDD 案例
│   └── case-iv-export/                 # 中国出口 IV 案例
│
├── tests/                              ⏳ 待创建
│   ├── test_identify_strategy.py
│   ├── test_scaffold_dofile.py
│   └── test_paper_session.py
│
└── _references/                        ⏳ 待 git clone（不入版本库）
    ├── StatsPAI/                       # 上游计量包
    ├── academic-research-skills/       # 上游论文 pipeline
    ├── superpowers/                    # 上游工程纪律
    ├── stata-skill/                    # 上游 Stata 参考
    └── claude-code-skills-social-science/  # 上游社科 skills
```

---

## 任务优先级与时间预算

### Sprint 1（本会话内）— 项目骨架

- [x] 全网调研报告
- [x] README.md
- [x] PROJECT_PLAN.md（你正在看）
- [ ] SKILL.md（Cursor/Claude Code 入口）
- [ ] WORKFLOW.md
- [ ] RESEARCH_QUESTION.md（阶段 1 模板）
- [ ] requirements.txt + pyproject.toml
- [ ] .env.example + .gitignore
- [ ] git clone 3 个最重要参考项目到 `_references/`
- [ ] 创建 templates/ 和 references/ 子目录骨架

### Sprint 2（下一会话）— 核心脚本

- [ ] scripts/identify_strategy.py（决策树 + dry-run）
- [ ] scripts/scaffold_dofile.py（生成 Stata 模板）
- [ ] scripts/cli.py（统一入口）
- [ ] tests/ 基础测试

### Sprint 3 — 高级能力

- [ ] scripts/robustness_checks.py
- [ ] scripts/paper_session.py
- [ ] examples/ 至少 1 个完整案例

### Sprint 4 — 集成 + 发布

- [ ] junction 注册到 Cursor / Claude Code
- [ ] 集成 FRED / Semantic Scholar MCP
- [ ] 中文期刊投稿模板
- [ ] git push 到 GitHub

---

## 关键决策记录

### D1：用 junction 链接还是复制 _references/？

**选择**：git clone 到 `_references/`，**不入版本库**（写到 .gitignore）。

**理由**：
- junction 太脆弱（路径变了就坏了）
- 上游版本会迭代，我们要锁定看过的版本
- 不入版本库避免协议问题（CC BY-NC vs MIT）

### D2：用 StatsPAI 还是自己写计量代码？

**选择**：直接 `pip install statspai`，作为依赖。

**理由**：
- 390+ 函数已经覆盖，重写浪费
- agent-native API 设计（`list_functions / describe_function / function_schema`）正是我们想要的
- JOSS 发表，质量有保证

### D3：Stata 优先还是 Python 优先？

**选择**：**三语并行**，但 Stata 是 default。

**理由**：
- 国内学术圈仍以 Stata 为主
- R 是国际计量主流（fixest/did/rdrobust 生态）
- Python + StatsPAI 是新生态，给愿意尝鲜的用户

### D4：要不要做商业化？

**选择**：**不做**。MIT 开源，对标 CoPaper.AI 的商业方案做开源替代。

**理由**：
- CoPaper.AI 已经占据"20 分钟出论文"商业生态位
- 我们的差异化是中文 + Stata + 数据脱敏 + 本地，不抢生态
- 开源更符合学术圈协作精神

---

## 度量成功的标准

完成 v0.1.0 时，应该能做到：

1. ✅ 一个研究生用 30 分钟跑通"最低工资 DiD"全流程（question → design → execute → verify → publish）
2. ✅ 生成的 Stata do-file 直接可跑，无需手改
3. ✅ verify 报告能识别至少 5 类常见 pitfall（缺平行趋势 / 缺 cluster SE / 多重比较未校正等）
4. ✅ paper session 能管理至少 3 版迭代 + R&R response
5. ✅ 不依赖任何商业 API 也能用（用本地 LLM 也行）
