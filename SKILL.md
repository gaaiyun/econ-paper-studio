---
name: econ-paper-studio
description: End-to-end empirical economics research workflow — from research question clarification through identification strategy selection, Stata/R/Python code generation, robustness checks, to paper drafting and R&R response. Use this skill when the user is doing causal inference research (DiD, RDD, IV, SCM, PSM, DML), writing an empirical paper for SSCI/CSSCI journals, or responding to reviewer comments. The skill orchestrates upstream tools (StatsPAI for execution, Imbad0202/academic-research-skills for paper writing, sshtomar social-science skills for methodology, dylantmoore/stata-skill for Stata) into a five-stage workflow with optional Chinese-language output and Chinese journal templates.
---

# Econ Paper Studio

End-to-end empirical economics workflow. Five stages: question → design → execute → verify → write. Chinese-friendly. Stata-first.

> **WORKFLOW.md** is the single source of truth for the five-stage pipeline. This file is the Cursor/Claude Code skill entry that describes activation conditions and routing rules.

## When to Use This Skill

Yes:
- Causal inference: DiD, RDD, IV, SCM, PSM, DML, Causal Forest
- Empirical paper writing: from data to draft to R&R response
- Identification strategy selection given research question + data structure
- Robustness checks automation (parallel trends, placebo, multiple testing correction, heterogeneity)
- Chinese journal submission (CSSCI, CSI Tier 1)
- Stata-heavy workflows where most upstream tools are Python/R
- Referee response drafting (point-by-point)

No:
- Pure ML / non-causal prediction (use scikit-learn directly)
- Theory-only papers without empirics
- Bibliometric reviews (use OpenAlex MCP directly)
- One-off regression in Jupyter (overkill)

## Default Mode: Quick or Full?

**Quick mode** — User has a clear brief and wants to skip to one specific stage:
- "I have data and want to know if DiD is appropriate" → jump to stage 2 (design)
- "I have a draft, run robustness checks" → jump to stage 4 (verify)

**Full mode** — User has fuzzy intent or high-stakes deliverable:
- "I want to write a paper about X" → start at stage 1 (question)
- Mentions "submit to" / "客户" / "投稿" / "blind review"

Default is **quick mode**. Switch to full when the brief has fewer than 3 of {research question, identification strategy, data, target journal, expected contribution}.

## The Five Stages

### Stage 1: question (research question clarification)

**Tool**: `RESEARCH_QUESTION.md` template (5 core questions + 5 advanced)

**Skip if**: User already has a clear "X has a causal effect on Y in context Z" brief plus identification strategy and target journal.

**Use if**: User says "I want to study minimum wage effects" with no further detail.

Read [`RESEARCH_QUESTION.md`](./RESEARCH_QUESTION.md). Ask the 5 core questions: research question, contribution, journal, data, identification strategy seed. Stop generating until the brief is structured.

### Stage 2: design (identification strategy selection)

**Tool**: `scripts/identify_strategy.py` decision tree

**Skip if**: Strategy locked + literature benchmark known.

**Use if**: User asks "what method?" or has data but no method yet.

Run:
```bash
python scripts/identify_strategy.py --brief research_brief.yaml
```

Outputs `strategy_recommendation.md` with primary method, alternatives, ≥3 literature benchmarks, robustness checklist, and StatsPAI function call preview.

### Stage 3: execute (code scaffolding)

**Tool**: `scripts/scaffold.py` (generates Stata / R code skeletons)

```bash
python scripts/scaffold.py --strategy DiD --session my-paper --lang stata
```

Outputs `outputs/<session>/` with standard subdirectories and Stata/R analysis files:
- `do/00_master.do` or `R/00_main.R` — ordered execution entry
- `01_clean` / `02_descriptive` / `03_main` — core empirical workflow
- `04_robustness` / `05_heterogeneity` / `99_export` — checks and paper outputs
- `data/`, `tables/`, `figures/`, `robustness/` — replication package structure

### Stage 4: verify (robustness + audit)

**Tool**: `scripts/robustness_checks.py`

```bash
python scripts/robustness_checks.py --strategy DiD --analysis outputs/my-paper --output verify_report.md
```

Checks:
- **Critical**: parallel trends (DiD), McCrary density (RDD), weak IV F-stat (IV), cluster SE used, multiple testing correction
- **High**: placebo, heterogeneity, alternative bandwidth/cluster levels, HonestDiD sensitivity, selection (Heckman/Lee bounds)
- **Audit**: AI-style filler phrases, obvious citation placeholders, missing references section risk

This verifier is offline-first. It does not prove numerical correctness or source support; use it as a blocking static gate before live Stata/R/Python runs and external citation verification.

### Stage 5: write (paper writing + R&R)

**Tool**: `scripts/session.py` session manager

```bash
python scripts/session.py init my-paper --rq "X causes Y" --strategy DiD --target-journal CSSCI
python scripts/session.py add my-paper --version v1 --paper draft_v1.docx --note "first draft"
python scripts/session.py add-review my-paper --version r1 --letter comments.docx --decision major
python scripts/session.py promote my-paper --version v2
```

Maintains `manifest.json` + `CHANGELOG.md` per session. Use Stage 4 `verify --paper <draft>` to scan AI-style filler and citation placeholders before recording an iteration score.

## Things That Must Survive Compilation

When advising on the workflow, never lose:

- **Identification strategy first, then data**. A clever method on bad data ≥ a bad method on good data ≥ no method.
- **Cluster SE always**. Default cluster level: panel ID for individuals, treatment unit for staggered policies, region for shocks.
- **Multiple testing correction** when running >1 hypothesis. Bonferroni or Holm-Šídák, not just `p<0.05`.
- **Pretrend check is necessary, not sufficient** (Roth 2022 AERI). Always pair with HonestDiD or local randomization.
- **Don't OVERSELL**. "Robust" / "Strong" / "Conclusive" are red flags unless backed by 4+ specifications.
- **Reproducibility lock**. Every result table needs a do-file path + seed + data version.

## Upstream Dependencies

This skill is an **orchestrator**. It calls into:

| Upstream | Used by | What we use |
|---|---|---|
| `StatsPAI` (pip) | Stage 3 + 4 | All causal inference methods |
| `obra/superpowers` (skill) | All stages | brainstorming + verification-before-completion + dispatching-parallel-agents |
| `Imbad0202/academic-research-skills` (skill) | Stage 5 | academic-paper writer + reviewer |
| `sshtomar/claude-code-skills-social-science` (skill) | Stage 2 + 4 | DID skill + regression-diagnostics |
| `dylantmoore/stata-skill` (skill) | Stage 3 | Stata reference (37 core + 20 packages) |
| `K-Dense-AI/claude-scientific-skills` (skill) | Stage 3 + 4 | statistical-analysis (test selection, APA reporting) |

If those skills are not installed, this skill still works in "standalone mode" but with reduced quality. Prompt the user to install them via `INSTALL_CN.md` instructions.

## Files

| File | Role |
|---|---|
| `README.md` | Project intro |
| `PROJECT_PLAN.md` | Full task breakdown |
| `WORKFLOW.md` | Five-stage workflow detail |
| `RESEARCH_QUESTION.md` | Stage 1 template |
| `INSTALL_CN.md` | Chinese install guide |
| `scripts/identify_strategy.py` | Stage 2 strategy selector |
| `scripts/scaffold.py` | Stage 3 Stata/R scaffold generator |
| `scripts/robustness_checks.py` | Stage 4 offline static verifier |
| `scripts/session.py` | Stage 5 paper session manager |
| `scripts/cli.py` | Unified `econ-studio` entry |
| `references/` | Methods + anti-AI phrase references |
| `examples/` | Smoke-test research brief and planned case studies |
| `tests/` | 107 offline pytest tests |

## Notes

- **Python > 3.10** required (StatsPAI dependency)
- **Optional**: Stata installation (for stata-mcp) — most scripts work without it via fallback
- **Optional**: Volcengine ARK_API_KEY for vision-based table verification
- **Optional**: Semantic Scholar API key for citation validation (free tier OK)

This skill is at version **0.1.0**. The offline CLI path is runnable; external citation verification and real Stata/R execution remain explicit user-side/live-tool steps.
