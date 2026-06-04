# Agent Integrations

`econ-paper-studio` 不是只能跑本地静态检查的小工具。它是给 agent 编排研究任务用的：agent 可以调用本地 CLI，也可以调用 Stata/R/Python、引用核验 API、MCP、数据库、文档渲染工具和 Coze workflow。CLI 的作用是把质量闸门固定下来，让 agent 不跳步骤。

## 总入口

| 文件 | 给谁读 | 作用 |
|---|---|---|
| `AGENTS.md` | Codex、Cursor、OpenCode、其他通用 coding agents | 项目级指令 |
| `SKILL.md` | Claude Code、Claude-compatible skills | 主 skill 入口 |
| `skill_loadout.yaml` | agent / runner / orchestration script | 配套 skills 的机器可读清单 |
| `research_skill_registry.yaml` | agent / runner / orchestration script | 按研究阶段路由上游 skills |
| `agent_manifest.yaml` | 平台集成和工具封装 | 各平台入口和命令映射 |
| `docs/AGENT_RUNBOOK.md` | 长任务接手 | 从研究问题到交付验证的流程 |
| `docs/UPSTREAM_SKILLS.md` | 上游 skills | 部署、加载和使用外部技能包 |
| `docs/QUALITY_GATES.md` | 交付前 | 数据、计量、引用、写作、复现检查 |

## Claude Code

Claude Code 的 skill 入口是 `SKILL.md`。官方文档说明，skill 通过 `SKILL.md` 给 Claude 增加可按需加载的能力，并可放在个人或项目 `.claude/skills/<name>/SKILL.md` 下。

推荐两种方式：

```powershell
# 方式 1：项目内直接使用，先让 Claude Code 读根目录 SKILL.md / AGENTS.md
cd "<path-to-econ-paper-studio>"
claude

# 方式 2：注册成个人 skill，供任意论文项目调用
cmd /c mklink /J "%USERPROFILE%\.claude\skills\econ-paper-studio" "<path-to-econ-paper-studio>"
```

Claude Code 接手论文项目时，第一句可以这样说：

```text
Use the econ-paper-studio skill. Load skill_loadout.yaml, then audit this paper project using docs/AGENT_RUNBOOK.md and docs/QUALITY_GATES.md.
```

## OpenCode

OpenCode 支持 `SKILL.md` agent skills，并会从 `.opencode/skills/<name>/SKILL.md`、`.claude/skills/<name>/SKILL.md`、`.agents/skills/<name>/SKILL.md` 等位置发现技能。

本仓库已经放了：

```text
.opencode/skills/econ-paper-studio/SKILL.md
```

在 OpenCode 里使用时，先进入仓库或论文项目，再让 agent 加载：

```text
Load the econ-paper-studio skill and follow AGENTS.md. Install or load the upstream skills listed in skill_loadout.yaml before substantive econometrics or writing work.
```

如果论文项目不在本仓库，可以把本仓库作为全局 skill：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.config\opencode\skills" | Out-Null
cmd /c mklink /J "%USERPROFILE%\.config\opencode\skills\econ-paper-studio" "<path-to-econ-paper-studio>"
```

## Codex

Codex 是 OpenAI 的 coding agent，用来写、审、交付代码；当前可以通过 Codex app、CLI、IDE extension、web/cloud 等入口使用。对这个仓库，Codex 的主要入口是：

```text
AGENTS.md
skill_loadout.yaml
docs/AGENT_RUNBOOK.md
docs/QUALITY_GATES.md
```

推荐提示词：

```text
Read AGENTS.md, skill_loadout.yaml, and docs/UPSTREAM_SKILLS.md. Treat econ-paper-studio as an agent-native empirical research workflow. Use available tools for live citation checks, Stata/R/Python execution, and document QA. Do not stop at static checks.
```

如果在 Codex app 或 Codex CLI 中接手真实论文目录，先让它把本仓库路径作为参考目录：

```text
Use <path-to-econ-paper-studio> as the workflow skill/reference repo, then audit the current paper project.
```

## Cursor

Cursor 可以读取项目规则和 `AGENTS.md`。本仓库已经放了：

```text
AGENTS.md
.cursor/rules/econ-paper-studio.mdc
```

在 Cursor 中打开仓库后，Agent 模式里直接说：

```text
Use the econ-paper-studio project rule. Load AGENTS.md and skill_loadout.yaml before editing.
```

如果是在另一个论文仓库中使用，把下面两类文件复制或链接过去：

```text
AGENTS.md
.cursor/rules/econ-paper-studio.mdc
```

如果只复制 `AGENTS.md`，也能工作；`.cursor/rules` 只是让 Cursor 更容易自动触发。

## Coze

Coze 不能直接读取研究者本机路径，也不能直接执行 `econ-studio`。正确接入方式是把 `econ-studio` 包装成一个受控 runner 服务，然后让 Coze workflow/API 调这个 runner。

### 推荐架构

```text
Coze Bot / Workflow
  -> HTTP Tool / Plugin
  -> econ-paper-studio runner API
  -> allowed workspace on server
  -> econ-studio command
  -> report text + artifact URLs
```

仓库提供了 Coze tool schema：

```text
integrations/coze/econ-paper-studio-tool-schema.json
```

runner 服务只允许这些命令：

- `doctor`
- `skills_plan`
- `skills_audit`
- `identify`
- `design_memo`
- `data_audit`
- `verify`
- `ledger_init`
- `ledger_add`
- `ledger_audit`
- `claim_audit`
- `reviewer_gauntlet`
- `paper_outline`
- `paper_audit`

不要让 Coze 传任意 shell 命令。路径也必须映射到服务端允许的 workspace，不接受任意绝对路径。

### Coze workflow 要点

1. Workflow 先收集 `workspace_id`、`command`、`paper_path/csv_path/brief_path` 等参数。
2. HTTP 工具调用 runner API。
3. runner 返回 Markdown report 和 artifact URL。
4. Coze 把报告摘要给用户，并把完整报告链接出来。
5. 如果需要联网引用核验，runner 侧接 Crossref/OpenAlex/Semantic Scholar，不让 Coze 模型凭空补引用。
6. 如果调用 `ledger_add`，runner 必须把路径限制在允许 workspace 内，并返回更新后的 ledger 摘要。

Coze 官方 API 文档要求 workflow 已发布后才能执行；调用时传 `workflow_id`、`parameters`，并用 bearer token 做鉴权。这个限制意味着：本项目的 Coze 接入应设计成“发布后的 workflow 调用 runner”，不是让模型直接访问本地仓库。

## 平台共同规则

无论哪个 agent 平台，都必须守这几条：

1. 先读 `AGENTS.md`、`skill_loadout.yaml` 和 `docs/UPSTREAM_SKILLS.md`。
2. 有配套 skills 就加载，没有就按 `docs/QUALITY_GATES.md` 手动执行。
3. 能联网核验引用就联网核验，不能联网就标记为“待核验”，不要编。
4. 能跑 Stata/R/Python 就实际跑，不能跑就标记为“未执行”，不要把模板当结果。
5. 结束前跑 `doctor`、paper/data/verify gates，并写清未执行或待核验的项目。
6. 论文核心结论要跑 `claim-audit`，不能只靠模型觉得“说得通”。

## 官方参考

- Claude Code skills: https://code.claude.com/docs/en/skills
- OpenCode agent skills: https://dev.opencode.ai/docs/skills
- Codex overview: https://help.openai.com/en/articles/11369540-getting-started-with-codex
- Cursor rules: https://docs.cursor.com/context/rules
- Coze Studio workflow API: https://github.com/coze-dev/coze-studio/wiki/6.-API-Reference
