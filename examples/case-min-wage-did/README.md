# case-min-wage-did

最小可跑的 DiD smoke case。它不包含真实数据，只提供结构化 research brief，用来验证 `identify -> scaffold -> verify` 这条离线链路。

## Run

```powershell
econ-studio identify `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\identify_strategy.md

econ-studio scaffold `
  --strategy DiD `
  --session min-wage-demo `
  --lang stata

econ-studio verify `
  --strategy DiD `
  --analysis outputs\min-wage-demo `
  --output outputs\min-wage-demo\verify_report.md `
  --fail-under 10
```

## Expected

- `identify` should rank DiD first.
- `scaffold` should create 7 Stata do-files under `outputs/min-wage-demo/do/`.
- `verify` should pass the default static DiD gate at `10.0 / 10`.

The generated do-files are still templates. Replace variable names, data paths, and method details before using them for a real paper.
