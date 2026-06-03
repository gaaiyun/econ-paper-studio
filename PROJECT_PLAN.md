# 项目计划与路线图

`econ-paper-studio` 是一个实证经济学论文工作流编排层。它不替代 Stata/R/Python，也不替代研究者判断；它把研究问题、识别策略、代码骨架、质量核验和论文版本管理放进一个本地可复现 session。

## 当前状态

| 模块 | 状态 | 说明 |
|---|---|---|
| CLI | 可用 | `scripts/cli.py` 统一入口，支持 `doctor/brainstorm/identify/scaffold/verify/session` |
| Doctor | 可用 | `scripts/doctor.py` 检查 Python 版本、关键文件、核心依赖和可选依赖 |
| Stage 1 question | 可用 | `RESEARCH_QUESTION.md` 提供研究问题五问 |
| Stage 2 design | 可用 | `scripts/identify_strategy.py` 支持 DiD/RDD/IV/SCM/Matching/DML 推荐 |
| Stage 3 execute | 可用 | `scripts/scaffold.py` 支持 Stata DiD/RDD 与 R DiD 骨架 |
| Stage 4 verify | 可用 | `scripts/robustness_checks.py` 离线扫描方法证据、AI 味、因果过度声称和引用风险 |
| Stage 5 write | 可用基础版 | `scripts/session.py` 管理 manifest、CHANGELOG、版本和审稿意见 |
| Examples | 最小可跑 | `examples/case-min-wage-did/research_brief.yaml` 可用于 smoke test |
| Tests | 可用 | 111 个离线 pytest，CI 友好 |

## 设计原则

1. **不重造轮子**：StatsPAI、Academic Research Skills、Stata skill、social-science skills 做得好的地方，本项目只做 adapter 和编排。
2. **离线优先**：没有 API key、没有 Stata/R、本地无网络时，CLI 仍能生成研究骨架并做静态质量检查。
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
├── SKILL.md
├── TESTING.md
├── pyproject.toml
├── scripts/
│   ├── cli.py
│   ├── doctor.py
│   ├── identify_strategy.py
│   ├── scaffold.py
│   ├── robustness_checks.py
│   └── session.py
├── references/
│   ├── anti_ai_phrases.md
│   └── methods/did.md
├── examples/
│   ├── README.md
│   └── case-min-wage-did/research_brief.yaml
└── tests/
    ├── test_cli.py
    ├── test_doctor.py
    ├── test_identify_strategy.py
    ├── test_scaffold.py
    ├── test_robustness_checks.py
    └── test_session.py
```

## 近期路线图

### P0：保持可用

- 任何新增能力都必须能离线测试。
- README 和 INSTALL_CN 的命令必须能复制运行。
- `python -m pytest tests/ -p no:cacheprovider` 必须保持全绿。
- 不把 `outputs/`、数据文件、API key、外部仓库加入版本库。

### P1：提升 Stage 4

- 为 `verify` 增加 `--strategy RDD/IV/SCM/PSM/DML` 的更多 fixture。
- 扩展文本中因果过度声称扫描：覆盖更多中文措辞和 claim-to-evidence 对齐规则。
- 增加表文一致性静态检查：扫描 `Table X` / `Figure X` 引用是否有对应文件或标签。

### P2：补完整 case

- `case-min-wage-did`：增加预期输出、示例 verify report 和 do-file 说明。
- `case-rdd-college`：补 RDD brief 和 scaffold smoke test。
- `case-iv-export`：补 IV brief，重点展示 first-stage / weak-IV 风险。

### P3：外部引用核验

- 可选接入 OpenAlex / Crossref / Semantic Scholar。
- 区分“引用存在”“引用主题相关”“引用支持该 claim”三个层级。
- 所有网络核验必须可关闭，测试使用 fixture，不依赖线上服务。

### P4：写作/R&R 辅助

- 在 `session.py` 基础上补 reviewer comment 结构化解析。
- 生成 point-by-point response 模板，但不伪造修改位置。
- 把 anti-AI phrase scan 与 session iteration score 关联。

## 成功标准

- 新用户 5 分钟内能跑完 README 的最小路径。
- 研究者能在输出里看到“下一步该补什么”，而不是只看到泛泛建议。
- 对 DiD/RDD/IV 等高风险方法，工具会主动指出关键识别和稳健性缺口。
- 文档不承诺当前代码做不到的事。
- 所有测试在本地和 CI 中离线通过。

## 已知边界

- `verify` 是静态检查，不跑真实回归。
- Stata/R 模板仍需要用户替换变量名和数据路径。
- Python + StatsPAI 执行模板尚未实现。
- 引用真实性需要后续外部 API 或人工核验。
- `PROJECT_PLAN.md` 是路线图，不是论文方法论教程；方法细节优先看 `WORKFLOW.md` 和 `references/`。
