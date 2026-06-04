# Upstream Skills Bundle

`econ-paper-studio` 负责把实证论文工作流串起来；上游 skills 负责提供更细的研究、计量、Stata、写作、图表和工程纪律。调用本项目的 agent 应先运行 `econ-studio skills plan --task full-paper`，再部署或加载这些上游 skills，最后按 `AGENTS.md` 和 `docs/AGENT_RUNBOOK.md` 执行。

## 原则

1. 不把上游仓库复制进本仓库。
2. 上游 skills 安装在 agent 自己的 skill 目录，或放在 `_references/upstream-skills/` 这类不提交的参考目录。
3. 使用前先读对应 `SKILL.md`、README、license 和安全边界。
4. 加载前可用 `econ-studio skills audit --dir <skill-dir>` 查明显风险信号。
5. 每次真实论文任务都记录使用了哪些 skills、版本或 commit、哪些外部工具实际运行过。
6. 如果某个 skill 没装上，不要编造它的能力；按 `docs/QUALITY_GATES.md` 手动降级。

## 推荐部署顺序

| 顺序 | 上游 | 用在本项目哪里 | Agent 应该怎么用 |
|---:|---|---|---|
| 1 | Auto-Empirical Research Skills（原 Awesome Agent Skills for Empirical Research） | 上游导航 | 先查经验研究任务应调用哪些社会科学技能 |
| 2 | obra/superpowers | 流程纪律 | 先选技能、写计划、系统排错、完成前核验证据 |
| 3 | StatsPAI | 计量执行 | 查因果推断和应用计量函数，必要时与 Stata/R 输出对照 |
| 4 | Academic Research Skills | 论文 pipeline | research -> write -> review -> revise -> finalize |
| 5 | Stata skill | Stata 代码 | 写 do-file、处理 `reghdfe`、`esttab`、`csdid`、`rdrobust` 等细节 |
| 6 | Social-science methods skills | 社会科学方法 | 把 DiD/RDD/IV/SCM/PSM/DML 的假设和诊断转成检查项 |
| 7 | data skills | 数据和统计 | 查重复键、join explosion、缺失、聚类层级、显著性和多重检验边界 |
| 8 | writing / humanizer / plotting skills | 写作和图表 | 去空话、压住 AI 腔、查贡献句、引用边界、图表标题和图形规范 |
| 9 | OpenJudge / reviewer skills | 审稿视角 | 把方法、数据、引用、写作和复现问题转成 reviewer gauntlet |
| 10 | documents skill | 投稿稿 | 处理 docx、PDF、表格渲染和视觉 QA |

## 机器可读清单

根目录 `skill_loadout.yaml` 是给 agent 或 runner 读取的清单。部署时应按其中的：

- `project_entrypoints` 读取本项目入口；
- `load_order` 加载会话内必需 skills；
- `upstream_skill_sources` 安装或定位外部 skills；
- `external_reference_policy` 约束外部仓库不进版本库。

根目录 `research_skill_registry.yaml` 是任务路由清单。agent 可先运行：

```powershell
econ-studio skills plan --task full-paper
```

它会把 literature、design、data_audit、execute、write、claim_audit、review、submit 各阶段对应的上游 skills 和来源列出来。

## 平台安装方式

不同 agent 平台的 skill 目录不一样，所以这里不给某个固定绝对路径。通用做法是：

```powershell
git clone <upstream-skill-repo-url> <agent-skill-dir>\<skill-name>
```

如果平台提供 skill manager，就用平台原生命令安装。安装后让 agent 先读上游 `SKILL.md`，再回到本项目的 `AGENTS.md` 执行。

### Claude Code / OpenCode

把上游 skill 放进个人或项目 skill 目录。完成后提示 agent：

```text
Load econ-paper-studio, then load the upstream skills listed in skill_loadout.yaml. Read each relevant SKILL.md before using it.
```

### Codex / Cursor

把 `AGENTS.md`、`skill_loadout.yaml`、`docs/UPSTREAM_SKILLS.md` 放在项目上下文里。若平台支持本地 skills，加载对应 skill；若不支持，就让 agent 读取上游仓库文档并按本项目质量闸门执行。

### Coze

Coze 不应直接拿 shell 去安装任意仓库。正确方式是 runner 侧预装或挂载上游 skills，Coze workflow 只调用白名单 API。runner 返回报告时，应说明哪些上游 skills 被使用，哪些没有被加载。

## 上游来源

| 上游 | 来源 |
|---|---|
| Auto-Empirical Research Skills（原 Awesome Agent Skills for Empirical Research） | `https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills` |
| StatsPAI | `https://github.com/brycewang-stanford/StatsPAI` |
| Academic Research Skills | `https://github.com/Imbad0202/academic-research-skills` |
| obra/superpowers | `https://github.com/obra/superpowers` |
| Stata skill | `https://github.com/dylantmoore/stata-skill` |
| Social-science methods skills | `https://github.com/sshtomar/claude-code-skills-social-science` |
| K-Dense Scientific Agent Skills | `https://github.com/K-Dense-AI/scientific-agent-skills` |
| OpenJudge paper-review | `https://github.com/agentscope-ai/openjudge/blob/main/skills/paper-review/SKILL.md` |
| Awesome Econ AI Stuff | `https://github.com/meleantonio/awesome-econ-ai-stuff` |
| humanizer | `https://github.com/blader/humanizer` |
| AI Research SKILLs | `https://github.com/Orchestra-Research/AI-Research-SKILLs` |

这些链接是上游入口，不代表本仓库重新分发其内容。部署时请遵守各自 license。
