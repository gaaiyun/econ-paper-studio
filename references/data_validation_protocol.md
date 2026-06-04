# Data Validation Protocol

Use this protocol before running Stata/R/Python estimation code.

## Required Checks

| Risk | What to check | Why it matters |
|---|---|---|
| Empty sample | Row count after every filter | A model can run on the wrong subsample without obvious errors |
| Duplicate analysis key | Unit-time or observation key uniqueness | Duplicate keys create join explosion and double counting |
| Missingness | Outcome, treatment, controls, cluster columns | Missing values change denominators and identifying samples |
| Treatment variation | At least treated and untreated observations | A constant treatment cannot identify an effect |
| Outcome type | Numeric scale and documented units | String-coded outcomes can silently break estimation |
| Cluster count | Number of non-missing clusters | Few clusters require different inference |

## Command

```powershell
econ-studio data-audit `
  --csv data\analysis_panel.csv `
  --key city_id `
  --key year `
  --outcome youth_employment_rate `
  --treatment minimum_wage_increase `
  --cluster city_id `
  --fail-on-critical
```

## Interpretation

`data-audit` is a pre-estimation gate. Passing it means the analysis file has no obvious structural failure. It does not prove data provenance, measurement validity, or model correctness.
