# 项目计划与路线图

`econ-paper-studio` 是一个实证经济学论文 agent 工作流编排层。它不替代 Stata/R/Python，也不替代研究者判断；它把研究问题、识别策略、代码骨架、质量核验和论文版本管理放进一个可被 agent 接手的 session。

## 当前状态

| 模块 | 状态 | 说明 |
|---|---|---|
| CLI | 可用 | `scripts/cli.py` 统一入口，支持 `doctor/brainstorm/identify/data-audit/scaffold/verify/paper/session` |
| Doctor | 可用 | `scripts/doctor.py` 检查 Python 版本、关键文件、核心依赖和可选依赖 |
| Stage 1 question | 可用 | `RESEARCH_QUESTION.md` 提供研究问题五问 |
| Stage 2 design | 可用 | `scripts/identify_strategy.py` 支持 DiD/RDD/IV/SCM/Matching/DML 推荐 |
| Stage 3 data-audit/execute | 可用 | `scripts/data_audit.py` 检查 CSV 样本结构；`scripts/scaffold.py` 支持 Stata DiD/RDD 与 R DiD 骨架 |
| Stage 4 verify | 可用 | `scripts/robustness_checks.py` 静态扫描方法证据、空泛写作、因果过度声称和引用风险 |
| Stage 5 paper/write | 可用 | `scripts/paper_pipeline.py` 支持 outline/audit；`scripts/session.py` 管理 manifest、CHANGELOG、版本和审稿意见 |
| Docs | 可用 | `docs/` 提供 quickstart、CLI reference、agent runbook、agent integrations、skill loadout、quality gates 和目录说明 |
| Examples | 最小可跑 | `examples/case-min-wage-did/` 提供 brief、CSV fixture 和草稿 excerpt |

## 设计原则

1. **不重造轮子**：StatsPAI、Academic Research Skills、Stata skill、social-science skills 做得好的地方，本项目只做 adapter 和编排。
2. **Agent 原生**：OpenCode、Claude Code、Codex、Cursor、Coze 等平台可以读取入口文件、加载配套 skills，并调用真实 Stata/R/Python、引用 API、MCP、数据库或文档工具。
3. **Stata-first**：默认输出国内实证研究者熟悉的 Stata do-file，同时保留 R 的现代 DiD 生态。
4. **可裁剪**：用户可以只跑 `identify` 或只跑 `verify`，不强迫完整五阶段。
5. **质量闸门可解释**：verifier 只报告它看到的证据，不夸大成“引用真实”或“结果正确”。

## 非目标

- 不做“一键自动生成完整论文”。
- 不在没有真实数据的情况下声称完成实证结果。
- 不把静态检查包装成外部引用核验。
- 不把 Stata/R/Python 的数值执行藏在黑盒里。
- 不把上游 skills 或第三方仓库复制进本仓库。

## 当前目录

```text
econ-paper-studio/
├── README.md
├── INSTALL_CN.md
├── WORKFLOW.md
├── RESEARCH_QUESTION.md
├── AGENTS.md
├── SKILL.md
├── skill_loadout.yaml
├── agent_manifest.yaml
├── pyproject.toml
├── .cursor/
│   └── rules/econ-paper-studio.mdc
├── .opencode/
│   └── skills/econ-paper-studio/SKILL.md
├── docs/
│   ├── README.md
│   ├── QUICKSTART_CN.md
│   ├── CLI_REFERENCE.md
│   ├── AGENT_RUNBOOK.md
│   ├── AGENT_INTEGRATIONS.md
│   ├── SKILL_LOADOUT.md
│   ├── PROJECT_STRUCTURE.md
│   ├── QUALITY_GATES.md
│   └── REAL_WORLD_TRIALS.md
├── integrations/
│   └── coze/econ-paper-studio-tool-schema.json
├── scripts/
│   ├── cli.py
│   ├── doctor.py
│   ├── identify_strategy.py
│   ├── data_audit.py
│   ├── scaffold.py
│   ├── robustness_checks.py
│   ├── paper_pipeline.py
│   └── session.py
├── references/
│   ├── anti_ai_phrases.md
│   ├── data_validation_protocol.md
│   ├── writing_quality_protocol.md
│   └── methods/did.md
├── examples/
│   ├── README.md
│   └── case-min-wage-did/
│       ├── research_brief.yaml
│       ├── panel_sample.csv
│       └── draft_excerpt.md
```

## 近期路线图

### P0：保持可用

- 任何新增能力都要能被样例或 fixture 清楚演示。
- README 和 INSTALL_CN 的命令必须能复制运行。
- 不把 `outputs/`、数据文件、API key、外部仓库加入版本库。
- agent 入口文件必须和真实 CLI 能力一致，不写当前做不到的承诺。

### P1：提升 Stage 4

- 为 `verify` 增加 `--strategy RDD/IV/SCM/PSM/DML` 的更多 fixture。
- 扩展文本中因果过度声称扫描：覆盖更多中文措辞和 claim-to-evidence 对齐规则。
- 增加表文一致性静态检查：扫描 `Table X` / `Figure X` 引用是否有对应文件或标签。
- 扩展 `data-audit`：支持 join plan、样本流失表和聚类小样本推断建议。

### P2：补完整 case

- `case-min-wage-did`：增加预期输出、示例 verify report 和 do-file 说明。
- `case-rdd-college`：补 RDD brief 和 scaffold 示例。
- `case-iv-export`：补 IV brief，重点展示 first-stage / weak-IV 风险。

### P3：外部引用核验

- 可选接入 OpenAlex / Crossref / Semantic Scholar。
- 区分“引用存在”“引用主题相关”“引用支持该 claim”三个层级。
- 所有网络核验必须可关闭，示例使用 fixture，不依赖线上服务。

### P4：写作/R&R 辅助

- 在 `paper_pipeline.py` 基础上补 reviewer comment 结构化解析。
- 生成 point-by-point response 模板，但不伪造修改位置。
- 把 anti-AI phrase scan 与 session iteration score 关联。

## 成功标准

- 新用户 5 分钟内能跑完 README 的最小路径。
- 研究者能在输出里看到“下一步该补什么”，而不是只看到泛泛建议。
- 对 DiD/RDD/IV 等高风险方法，工具会主动指出关键识别和稳健性缺口。
- 文档不承诺当前代码做不到的事。

## 已知边界

- `verify` 是静态检查，不跑真实回归。
- `data-audit` 只查结构性数据风险，不证明数据来源可靠。
- `paper audit` 只查文本风险，不证明引用真实或 claim 被文献支持。
- Stata/R 模板仍需要用户替换变量名和数据路径。
- Python + StatsPAI 执行模板尚未实现。
- 引用真实性需要后续外部 API 或人工核验。
- `PROJECT_PLAN.md` 是路线图，不是论文方法论教程；方法细节优先看 `WORKFLOW.md` 和 `references/`。
