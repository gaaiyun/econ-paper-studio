# Project Structure

这个仓库故意保持小而清楚。根目录放入口文件，细节文档放 `docs/`，方法和质量规则放 `references/`，代码在 `scripts/`。

## 顶层目录

| 路径 | 是否提交 | 用途 |
|---|---|---|
| `.cursor/rules/` | 是 | Cursor 项目规则 |
| `.github/workflows/` | 是 | GitHub Actions 自动化检查配置 |
| `.opencode/skills/` | 是 | OpenCode skill wrapper |
| `docs/` | 是 | 人看的详细文档和 agent runbook |
| `examples/` | 是 | 可跑的样例和 fixture |
| `integrations/` | 是 | Coze 等外部平台的工具 schema 或 runner 说明 |
| `references/` | 是 | 数据、写作、方法的协议和检查规则 |
| `scripts/` | 是 | CLI 子命令实现 |
| `outputs/` | 否 | 本地生成的 session、报告、do-files |
| 本地工具缓存目录 | 否 | 由开发工具临时生成，不要提交 |
| `*.egg-info/` | 否 | 本地 editable install 产物 |

## 根目录文件

| 文件 | 作用 |
|---|---|
| `README.md` | 项目简介和最小可运行路径 |
| `INSTALL_CN.md` | Windows / PowerShell 安装说明 |
| `WORKFLOW.md` | 五阶段研究流程 |
| `AGENTS.md` | 通用 agent 项目指令 |
| `SKILL.md` | Claude/Cursor/Codex skill 入口 |
| `skill_loadout.yaml` | 配套 skills 的机器可读清单 |
| `agent_manifest.yaml` | 平台入口和命令映射 |
| `RESEARCH_QUESTION.md` | 研究问题模板 |
| `PROJECT_PLAN.md` | 当前状态和路线图 |
| `pyproject.toml` | 包元数据、依赖和工具配置 |
| `.env.example` | 可选环境变量示例 |

## docs/

| 文件 | 作用 |
|---|---|
| `AGENT_RUNBOOK.md` | agent 接手真实研究任务时的顺序 |
| `AGENT_INTEGRATIONS.md` | Claude Code、OpenCode、Codex、Cursor、Coze 接入 |
| `SKILL_LOADOUT.md` | 本项目建议加载的 companion skills |
| `UPSTREAM_SKILLS.md` | 上游 skills 部署、加载和来源 |
| `QUALITY_GATES.md` | 投稿/交付前质量闸门 |

## scripts/

| 文件 | 命令 | 作用 |
|---|---|---|
| `cli.py` | `econ-studio <cmd>` | 统一入口 |
| `doctor.py` | `econ-studio doctor` | 本地环境和关键文件检查 |
| `identify_strategy.py` | `econ-studio identify` | 根据 brief 推荐识别策略 |
| `data_audit.py` | `econ-studio data-audit` | CSV 数据结构审计 |
| `scaffold.py` | `econ-studio scaffold` | 生成 Stata/R 分析骨架 |
| `robustness_checks.py` | `econ-studio verify` | 方法、写作和引用静态核验 |
| `paper_pipeline.py` | `econ-studio paper` | 论文大纲和草稿质检 |
| `session.py` | `econ-studio init/list/add/...` | 论文 session 和版本管理 |

## examples/

当前可跑案例是 `case-min-wage-did/`。

| 文件 | 作用 |
|---|---|
| `research_brief.yaml` | Stage 1/2 的输入 |
| `panel_sample.csv` | `data-audit` 的 toy fixture，不是真实研究数据 |
| `draft_excerpt.md` | `paper audit` 的草稿 fixture，不是可引用内容 |
| `README.md` | 该案例的命令和预期结果 |

## 不要提交什么

不要提交：

- `outputs/` 下生成的 session；
- 真实原始数据和中间数据；
- Stata `.dta`、`.smcl`、`.log` 产物；
- API key、`.env`、本地缓存；
- 外部 skills 的 clone。

如果需要长期保存某个真实研究输出，放到研究项目自己的仓库或归档目录，不要混进这个工具仓库。
