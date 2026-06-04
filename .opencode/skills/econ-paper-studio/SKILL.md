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
4. `docs/UPSTREAM_SKILLS.md`
5. `docs/AGENT_RUNBOOK.md`
6. `docs/QUALITY_GATES.md`

This project is agent-native. Use `econ-studio` CLI gates together with live Stata/R/Python execution, citation APIs, data connectors, and document-rendering tools when available.
Install or load the upstream skills listed in `skill_loadout.yaml` when the platform supports it; otherwise read the relevant upstream `SKILL.md` files and record the missing pieces.

Do not fabricate results or citations. Static checks are gates; they are not a substitute for real model execution or source verification.
