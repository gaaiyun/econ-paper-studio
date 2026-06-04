# Writing Quality Protocol

Use this protocol before sharing a draft with an adviser, coauthor, client, or journal editor.

## Draft Checks

| Risk | What to check | Rule |
|---|---|---|
| Fake or unresolved references | Author-year placeholders, citation-needed notes, missing references section | Do not keep a citation unless it is traceable to a real source |
| Vague contribution | No one-sentence contribution | State what the paper adds before listing sections |
| Causal overclaim | Strong causal language without identification assumptions | Tie each causal sentence to design, robustness, or limitations |
| Filler prose | Inflated language and generic transitions | Replace filler with evidence, mechanisms, or concrete transitions |
| Weak captions | Captions such as "Results" or "Main regression" | State estimand, sample, period, uncertainty, and clustering when relevant |
| Reviewer readiness | Missing data, method, results, robustness, references sections | A reviewer should be able to locate every core claim quickly |

## Command

```powershell
econ-studio paper audit `
  --paper paper\draft.md `
  --output outputs\paper_audit.md `
  --fail-under 8
```

## Citation Boundary

This repository only performs offline placeholder checks. Verifying that a cited work exists, is the right work, and supports a specific claim still requires Crossref/OpenAlex/Semantic Scholar, a DOI page, a journal page, or manual reading.
