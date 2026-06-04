# 快速开始

这条路径用于用仓库里的 toy fixture 跑通完整流程。真实研究仍要替换成自己的数据、代码和文稿。

## 1. 安装

```powershell
cd "<path-to-econ-paper-studio>"
python -m pip install -e .
```

如果 `econ-studio` 不可用，先用 `python scripts\cli.py` 替代。

## 2. 自检

```powershell
econ-studio doctor --strict
```

预期：所有 required file 和 required import 通过。

## 3. 识别策略

```powershell
econ-studio identify `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\identify_strategy.md
```

预期：DiD 排在第一，并列出平行趋势、错时 DiD、安慰剂和多重检验等必查项。

## 4. 数据审计

```powershell
econ-studio data-audit `
  --csv examples\case-min-wage-did\panel_sample.csv `
  --required city_id `
  --required year `
  --required minimum_wage_increase `
  --required youth_employment_rate `
  --key city_id `
  --key year `
  --outcome youth_employment_rate `
  --treatment minimum_wage_increase `
  --cluster city_id `
  --min-clusters 3 `
  --output outputs\min-wage-demo\data_audit.md `
  --fail-on-critical
```

预期：score 为 10.0。真实研究不要把 `--min-clusters 3` 当标准；这里是为了让 toy fixture 通过。

## 5. 生成 Stata 骨架

```powershell
econ-studio scaffold `
  --strategy DiD `
  --session min-wage-demo `
  --lang stata
```

预期：`outputs\min-wage-demo\do\` 下生成 7 个 do-files。

## 6. 稳健性与写作静态核验

```powershell
econ-studio verify `
  --strategy DiD `
  --analysis outputs\min-wage-demo `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\verify_report.md `
  --fail-under 6
```

预期：生成 `verify_report.md`。这一步不跑真实回归，只检查代码和文本里的证据钩子。

## 7. 论文大纲与草稿质检

```powershell
econ-studio paper outline `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\paper_outline.md

econ-studio paper audit `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\paper_audit.md `
  --fail-under 8
```

预期：生成大纲和草稿质检报告。报告通过只说明这个 fixture 没有明显结构问题，不说明引用已经被核验。
