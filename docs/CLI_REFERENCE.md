# CLI Reference

统一入口是：

```powershell
econ-studio <command> [options]
```

没有安装 entry point 时使用：

```powershell
python scripts\cli.py <command> [options]
```

## doctor

检查本地环境和关键文件。

```powershell
econ-studio doctor --strict
econ-studio doctor --json
```

`--strict` 会在 required check 失败时返回非零退出码，适合交付前检查。

## skills

给 agent 输出本轮任务应加载的上游 skills，或审计本地第三方 skill 目录。

```powershell
econ-studio skills plan --task full-paper
econ-studio skills plan --task review --json
econ-studio skills audit --dir _references\upstream-skills\some-skill
```

常用 task：`full-paper`、`literature`、`design`、`execute`、`audit`、`write`、`review`、`submit`。

`skills audit` 会检查 `SKILL.md` 是否存在，以及脚本中是否出现网络调用、环境变量/secret 读取、SSH key、浏览器数据等风险信号。它不会判断上游仓库一定安全；它只是让 agent 在加载前先把风险说清楚。

## brainstorm

打印研究问题模板。

```powershell
econ-studio brainstorm
```

用于研究问题还没说清楚的时候。正式 brief 应整理成 YAML。

## identify

根据 research brief 推荐识别策略。

```powershell
econ-studio identify `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\identify_strategy.md
```

输出包含推荐策略、理由、关键文献基准和必须补的稳健性。

## design-memo

把 research brief 转成识别设计备忘录。

```powershell
econ-studio design-memo `
  --brief research_brief.yaml `
  --output outputs\my-paper\design_memo.md
```

输出包含 research question、estimand、样本单位、时间单位、处理变量、结果变量、识别假设、威胁和必须诊断。它不替代 `identify`，而是把识别设计写成 agent 和研究者都能复查的 contract。

## data-audit

审计 CSV 分析样本。

```powershell
econ-studio data-audit `
  --csv data\analysis_panel.csv `
  --required unit_id `
  --required year `
  --key unit_id `
  --key year `
  --outcome outcome_var `
  --treatment treatment_var `
  --cluster unit_id `
  --output outputs\my-paper\data_audit.md `
  --fail-on-critical
```

报告会包含 data contract：分析粒度、join explosion 风险、缺失边界、分母边界、聚类层级和 claim 边界。

常用参数：

| 参数 | 说明 |
|---|---|
| `--csv` | 要审计的 CSV |
| `--required` | 必须存在的列，可重复 |
| `--key` | 分析键，可重复，例如 `city_id` + `year` |
| `--outcome` | 结果变量 |
| `--treatment` | 处理变量或政策变量 |
| `--cluster` | 聚类变量 |
| `--min-clusters` | 聚类数量下限，默认 30 |
| `--fail-on-critical` | 有 critical failure 时返回 2 |

## scaffold

生成分析骨架。

```powershell
econ-studio scaffold --strategy DiD --session my-paper --lang stata
```

当前主要支持 Stata-first 路径。生成的是模板，不是真实结果。

## verify

静态核验分析脚本和论文草稿。

```powershell
econ-studio verify `
  --strategy DiD `
  --analysis outputs\my-paper `
  --paper paper\draft.md `
  --output outputs\my-paper\verify_report.md `
  --fail-under 6
```

它会检查方法证据、空泛填充语、引用占位符和因果过度声称。它不跑真实回归。

## ledger

管理证据账本。每个支持论文结论的表或图都应该有一条记录。

```powershell
econ-studio ledger init --ledger outputs\my-paper\evidence_ledger.json

econ-studio ledger add `
  --ledger outputs\my-paper\evidence_ledger.json `
  --artifact-id table1 `
  --title "Baseline DiD estimates" `
  --artifact-path tables\table1.tex `
  --code-path do\03_main.do `
  --data-source data\analysis_panel.csv `
  --sample "city-year panel" `
  --model "two-way fixed effects DiD" `
  --estimand ATT `
  --cluster city_id `
  --claim "Minimum wage changes affect youth employment" `
  --status needs_verification

econ-studio ledger audit --ledger outputs\my-paper\evidence_ledger.json
```

ledger 记录的是证据位置和执行口径，不会自己生成回归结果。

## claim-audit

把论文草稿里的显式 `Claim:` 结论映射回 evidence ledger。

```powershell
econ-studio claim-audit `
  --paper paper\draft.md `
  --ledger outputs\my-paper\evidence_ledger.json `
  --output outputs\my-paper\claim_audit.md
```

如果 claim 找不到表图、代码、数据和模型记录，就应补 ledger、补结果，或把正文说法降级。

## reviewer-gauntlet

从五个审稿视角检查草稿和证据账本。

```powershell
econ-studio reviewer-gauntlet `
  --paper paper\draft.md `
  --ledger outputs\my-paper\evidence_ledger.json `
  --output outputs\my-paper\reviewer_gauntlet.md
```

五个视角是 Method Reviewer、Data Auditor、Citation Auditor、Writing/Humanizer、Replication Editor。

## paper outline

从 brief 生成论文大纲。

```powershell
econ-studio paper outline `
  --brief research_brief.yaml `
  --output outputs\my-paper\paper_outline.md
```

大纲会保留待核验来源和待填写结果，不会编造文献或数值。

## paper audit

审计论文草稿。

```powershell
econ-studio paper audit `
  --paper paper\draft.md `
  --output outputs\my-paper\paper_audit.md `
  --fail-under 8
```

它会检查核心章节、贡献句、引用占位符、因果声称、填充语、vague attribution、promotional language、显式 claim 是否有证据标记，以及图表标题。

## session

管理论文 session 和版本。

```powershell
econ-studio init my-paper --rq "X 对 Y 的因果效应" --strategy DiD
econ-studio list
econ-studio show my-paper
econ-studio add my-paper --version v1 --paper paper\draft.md --note "first draft"
econ-studio add-review my-paper --version r1 --letter review.md --decision major
econ-studio promote my-paper --version v2
```

`session` 记录版本，不替你判断论文质量。每次记录前应先跑 `verify` 和 `paper audit`。
