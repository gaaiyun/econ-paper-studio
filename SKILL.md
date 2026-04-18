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

**Tool**: `scripts/scaffold_dofile.py` (generates Stata / R / Python)

```bash
python scripts/scaffold_dofile.py --strategy strategy_recommendation.md --lang stata
```

Outputs `analysis/` with 6 standard files:
- `01_setup` — data import + descriptive stats
- `02_descriptive` — balance + summary tables
- `03_main` — main regression with cluster SE
- `04_robustness` — parallel trends / placebo / bandwidth tests
- `05_heterogeneity` — subgroup splits + interaction terms
- `06_tables_figures` — publication-ready output

### Stage 4: verify (robustness + audit)

**Tool**: `scripts/robustness_checks.py`

```bash
python scripts/robustness_checks.py --analysis analysis/ --output verify_report.md
```

Checks:
- **Critical**: parallel trends (DiD), McCrary density (RDD), weak IV F-stat (IV), cluster SE used, multiple testing correction
- **High**: placebo, heterogeneity, alternative bandwidth/cluster levels, HonestDiD sensitivity, selection (Heckman/Lee bounds)
- **Audit**: overstatement detection (excess "causes/leads to"), text-table consistency, citation-source consistency (Semantic Scholar)

### Stage 5: write (paper writing + R&R)

**Tool**: `scripts/paper_session.py` session manager

```bash
python scripts/paper_session.py init my-paper --venue CSSCI
python scripts/paper_session.py add --version v1 --paper draft_v1.docx
python scripts/paper_session.py verify --paper draft_v1.docx
python scripts/paper_session.py add-review --version r1 --reviewers "comments.docx"
python scripts/paper_session.py draft-response --version r1
```

Maintains `manifest.json` + `CHANGELOG.md` per session. Drafts point-by-point reviewer response. Strips AI-style filler ("It is worth noting", "Furthermore" etc.) using anti-AI phrase blacklist.

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
| `WORKFLOW.md` | Five-stage workflow detail (TODO) |
| `RESEARCH_QUESTION.md` | Stage 1 template (TODO) |
| `INSTALL_CN.md` | Chinese install guide (TODO) |
| `scripts/identify_strategy.py` | Stage 2 (TODO) |
| `scripts/scaffold_dofile.py` | Stage 3 (TODO) |
| `scripts/robustness_checks.py` | Stage 4 (TODO) |
| `scripts/paper_session.py` | Stage 5 (TODO) |
| `scripts/cli.py` | Unified `econ-studio` entry (TODO) |
| `references/` | Methods + protocols + anti-AI phrases (TODO) |
| `templates/` | Stata / R / Python / paper templates (TODO) |
| `examples/` | End-to-end case studies (TODO) |
| `tests/` | pytest (TODO) |

## Notes

- **Python > 3.10** required (StatsPAI dependency)
- **Optional**: Stata installation (for stata-mcp) — most scripts work without it via fallback
- **Optional**: Volcengine ARK_API_KEY for vision-based table verification
- **Optional**: Semantic Scholar API key for citation validation (free tier OK)

This skill is at version **0.1.0-init** as of 2026-04-19. Most scripts are TODO. See `PROJECT_PLAN.md` for the build sequence.
