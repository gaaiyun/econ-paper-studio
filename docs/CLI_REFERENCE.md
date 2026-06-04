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

`--strict` 会在 required check 失败时返回非零退出码，适合 CI 和交付前检查。

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

它会检查核心章节、贡献句、引用占位符、因果声称、填充语和图表标题。

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
