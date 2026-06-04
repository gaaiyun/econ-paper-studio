---
name: econ-paper-studio
description: Use for empirical economics research agents that need econometric workflow, data audit, paper writing, citation boundaries, and delivery verification.
compatibility: opencode
metadata:
  project: econ-paper-studio
  entrypoint: AGENTS.md
---

# econ-paper-studio

Read these files first:

1. `AGENTS.md`
2. `SKILL.md`
3. `skill_loadout.yaml`
4. `research_skill_registry.yaml`
5. `docs/UPSTREAM_SKILLS.md`
6. `docs/AGENT_RUNBOOK.md`
7. `docs/QUALITY_GATES.md`

This project is agent-native. Use `econ-studio` CLI gates together with live Stata/R/Python execution, citation APIs, data connectors, and document-rendering tools when available.
Start with `econ-studio skills plan --task full-paper`, then use `skills audit` before loading third-party skill directories.
Install or load the upstream skills listed in `skill_loadout.yaml` when the platform supports it; otherwise read the relevant upstream `SKILL.md` files and record the missing pieces.

Do not fabricate results or citations. The evidence ledger and claim audit must connect paper claims to real table, code, data, model, and citation verification state. Static checks are gates; they are not a substitute for real model execution or source verification.
