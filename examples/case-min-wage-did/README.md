# case-min-wage-did

最小可跑的 DiD smoke case。它包含结构化 research brief、toy CSV 和论文 excerpt，用来验证 `identify -> data-audit -> scaffold -> verify -> paper audit` 这条离线链路。

`panel_sample.csv` 和 `draft_excerpt.md` 只是 fixture，不是真实研究数据或可引用论文内容。

## Run

```powershell
econ-studio identify `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\identify_strategy.md

econ-studio scaffold `
  --strategy DiD `
  --session min-wage-demo `
  --lang stata

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

econ-studio verify `
  --strategy DiD `
  --analysis outputs\min-wage-demo `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\verify_report.md `
  --fail-under 6

econ-studio paper outline `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\paper_outline.md

econ-studio paper audit `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\paper_audit.md `
  --fail-under 8
```

## Expected

- `identify` should rank DiD first.
- `data-audit` should pass the fixture with `--min-clusters 3`.
- `scaffold` should create 7 Stata do-files under `outputs/min-wage-demo/do/`.
- `verify` should pass the generated Stata scaffold and scan the draft excerpt.
- `paper audit` should pass the draft excerpt's structure and caption checks.

The generated do-files are still templates. Replace variable names, data paths, sources, and method details before using them for a real paper.
