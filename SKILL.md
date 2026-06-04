---
name: econ-paper-studio
description: End-to-end empirical economics research workflow — from research question clarification through identification strategy selection, data audit, Stata/R/Python code scaffolding, robustness checks, paper quality audit, and R&R tracking. Use this skill when the user is doing causal inference research (DiD, RDD, IV, SCM, PSM, DML), writing an empirical paper for SSCI/CSSCI journals, or responding to reviewer comments. The skill orchestrates econometric, data-validation, writing, plotting, and verification disciplines into a local workflow with optional Chinese-language output.
---

# Econ Paper Studio

End-to-end empirical economics workflow. Stages: skills → question → design → data contract → execute → evidence ledger → claim audit → reviewer gauntlet → write. Chinese-friendly. Stata-first.

> **WORKFLOW.md** is the single source of truth for the five-stage pipeline. This file is the Cursor/Claude Code skill entry that describes activation conditions and routing rules.

## Required Companion Skills

When the platform has these skills available, load them before doing substantive work:

1. `superpowers:using-superpowers`
2. `superpowers:executing-plans`
3. `superpowers:systematic-debugging`
4. `superpowers:verification-before-completion`
5. `data:statistical-analysis`
6. `data:validate-data`
7. `data:create-viz`
8. `content-research-writer`
9. `documents:documents`

Detailed purpose, fallback behavior, and upstream installation guidance are documented in `docs/SKILL_LOADOUT.md` and `docs/UPSTREAM_SKILLS.md`.
The same loadout is also available as machine-readable metadata in `skill_loadout.yaml`.

Do not treat missing companion skills as a reason to stop. Fall back to the local CLI gates: `doctor`, `skills plan`, `identify`, `design-memo`, `data-audit`, `scaffold`, `ledger`, `verify`, `claim-audit`, `reviewer-gauntlet`, `paper audit`, and `session`.

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

## The Core Stages

### Stage 0: skills (upstream routing and safety)

**Tool**: `scripts/skills.py`

```bash
python scripts/skills.py plan --task full-paper
python scripts/skills.py audit --dir _references/upstream-skills/some-skill
```

Use `plan` before substantial work so the agent knows which upstream skills to load for literature, design, execution, writing, claim audit, review, and submission. Use `audit` before loading a third-party skill directory; it checks for missing `SKILL.md`, network calls, environment/secret access, SSH key patterns, and browser-data access.

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

Then render the identification contract:

```bash
python scripts/evidence_pipeline.py design-memo --brief research_brief.yaml --output design_memo.md
```

### Stage 3: data-audit + execute

**Tool**: `scripts/data_audit.py` first, then `scripts/scaffold.py`.

```bash
python scripts/data_audit.py --csv data/analysis_panel.csv \
  --key unit_id --key year \
  --outcome outcome \
  --treatment treatment \
  --cluster unit_id \
  --fail-on-critical

python scripts/scaffold.py --strategy DiD --session my-paper --lang stata
```

`data_audit.py` checks duplicate keys, missingness, treatment variation, numeric outcome, and cluster count before estimation. `scaffold.py` outputs `outputs/<session>/` with standard subdirectories and Stata/R analysis files:
- `do/00_master.do` or `R/00_main.R` — ordered execution entry
- `01_clean` / `02_descriptive` / `03_main` — core empirical workflow
- `04_robustness` / `05_heterogeneity` / `99_export` — checks and paper outputs
- `data/`, `tables/`, `figures/`, `robustness/` — replication package structure

The data-audit report now includes a data contract: analysis grain, join explosion risk, denominator boundary, missingness boundary, cluster level, and claim boundary.

### Stage 3.5: evidence ledger

**Tool**: `scripts/evidence_pipeline.py ledger`

```bash
python scripts/evidence_pipeline.py ledger init --ledger evidence_ledger.json
python scripts/evidence_pipeline.py ledger add --ledger evidence_ledger.json \
  --artifact-id table1 \
  --title "Baseline DiD estimates" \
  --artifact-path tables/table1.tex \
  --code-path do/03_main.do \
  --data-source data/analysis_panel.csv \
  --sample "city-year panel" \
  --model "two-way fixed effects DiD" \
  --estimand ATT \
  --cluster city_id \
  --claim "Minimum wage changes affect youth employment"
python scripts/evidence_pipeline.py ledger audit --ledger evidence_ledger.json
```

Every table and figure that supports a paper claim should have a ledger row.

### Stage 4: verify (robustness + audit)

**Tool**: `scripts/robustness_checks.py`

```bash
python scripts/robustness_checks.py --strategy DiD --analysis outputs/my-paper --output verify_report.md
```

Checks:
- **Critical**: parallel trends (DiD), McCrary density (RDD), weak IV F-stat (IV), cluster SE used, multiple testing correction
- **High**: placebo, heterogeneity, alternative bandwidth/cluster levels, HonestDiD sensitivity, selection (Heckman/Lee bounds)
- **Audit**: AI-style filler phrases, obvious citation placeholders, missing references section risk

This verifier is a static gate. It does not prove numerical correctness or source support; use it before live Stata/R/Python runs and external citation verification so the agent does not skip required evidence.

### Stage 5: paper/write (outline, audit, session)

**Tool**: `scripts/paper_pipeline.py` for outline/audit and `scripts/session.py` for version history.

```bash
python scripts/paper_pipeline.py outline --brief research_brief.yaml --output paper_outline.md
python scripts/paper_pipeline.py audit --paper draft.md --output paper_audit.md --fail-under 8
python scripts/session.py init my-paper --rq "X causes Y" --strategy DiD --target-journal CSSCI
python scripts/session.py add my-paper --version v1 --paper draft_v1.docx --note "first draft"
python scripts/session.py add-review my-paper --version r1 --letter comments.docx --decision major
python scripts/session.py promote my-paper --version v2
```

`paper_pipeline.py` checks core sections, explicit contribution, obvious citation placeholders, causal overclaim risk, filler phrases, and figure/table caption quality. It does not verify that a citation exists or supports a claim. `session.py` maintains `manifest.json` + `CHANGELOG.md` per session.

Before treating a draft as ready, run:

```bash
python scripts/evidence_pipeline.py claim-audit --paper draft.md --ledger evidence_ledger.json
python scripts/evidence_pipeline.py reviewer-gauntlet --paper draft.md --ledger evidence_ledger.json
```

`claim-audit` maps explicit `Claim:` statements back to evidence-ledger entries. `reviewer-gauntlet` applies five views: Method Reviewer, Data Auditor, Citation Auditor, Writing/Humanizer, and Replication Editor.

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
| `data:validate-data` style checks | Stage 3 | duplicate keys, missingness, join explosion, cluster count |
| `content-research-writer` / humanizer style checks | Stage 5 | contribution sentence, concrete prose, no placeholder citations |
| academic plotting guidance | Stage 5 | figure/table captions, uncertainty display, reviewer readability |
| `sshtomar/claude-code-skills-social-science` (skill) | Stage 2 + 4 | DID skill + regression-diagnostics |
| `dylantmoore/stata-skill` (skill) | Stage 3 | Stata reference (37 core + 20 packages) |

If those skills are not installed, this skill still works in "standalone mode" but with reduced quality. Prompt the user to install them via `INSTALL_CN.md` instructions.

## Files

| File | Role |
|---|---|
| `README.md` | Project intro |
| `AGENTS.md` | Generic agent instructions for Codex, Cursor, OpenCode, and similar agents |
| `skill_loadout.yaml` | Machine-readable companion skill list |
| `research_skill_registry.yaml` | Machine-readable upstream skill routing by research phase |
| `agent_manifest.yaml` | Platform entrypoints and safe command mapping |
| `PROJECT_PLAN.md` | Full task breakdown |
| `WORKFLOW.md` | Five-stage workflow detail |
| `docs/AGENT_RUNBOOK.md` | Step-by-step agent handoff and execution protocol |
| `docs/AGENT_INTEGRATIONS.md` | Claude Code, OpenCode, Codex, Cursor, and Coze setup |
| `docs/SKILL_LOADOUT.md` | Companion skills to load with this project |
| `docs/UPSTREAM_SKILLS.md` | Upstream skills bundle and installation policy |
| `docs/CLI_REFERENCE.md` | Command reference |
| `docs/QUALITY_GATES.md` | Pre-delivery gates |
| `docs/PROJECT_STRUCTURE.md` | Directory layout and commit boundaries |
| `examples/` | Public toy cases for agent smoke runs and workflow demos |
| `RESEARCH_QUESTION.md` | Stage 1 template |
| `INSTALL_CN.md` | Chinese install guide |
| `scripts/identify_strategy.py` | Stage 2 strategy selector |
| `scripts/data_audit.py` | Stage 3 data validation gate |
| `scripts/scaffold.py` | Stage 3 Stata/R scaffold generator |
| `scripts/robustness_checks.py` | Stage 4 static verifier for method evidence and writing risks |
| `scripts/paper_pipeline.py` | Stage 5 paper outline and writing-quality audit |
| `scripts/skills.py` | Upstream skill routing and local skill safety audit |
| `scripts/evidence_pipeline.py` | Design memo, evidence ledger, claim audit, and reviewer gauntlet |
| `scripts/session.py` | Stage 5 paper session manager |
| `scripts/cli.py` | Unified `econ-studio` entry |
| `references/` | Methods + anti-AI phrase references |
| `examples/` | Example research brief and planned case studies |

## Notes

- **Python > 3.10** required (StatsPAI dependency)
- **Optional**: Stata installation (for stata-mcp) — most scripts work without it via fallback
- **Optional**: Volcengine ARK_API_KEY for vision-based table verification
- **Optional**: Semantic Scholar API key for citation validation (free tier OK)

This skill is at version **0.3.0**. The CLI gates are runnable; external citation verification and real Stata/R/Python execution remain explicit live-tool steps.
