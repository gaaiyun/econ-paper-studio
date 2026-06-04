# 中文安装与使用指南

面向 Windows 11 + PowerShell 用户。macOS / Linux 用户把路径和续行符换成对应 shell 即可。

## 1. 项目位置

当前仓库：

```powershell
cd "G:\github_project_0516\econ-paper-studio"
```

项目是一个本地 CLI / Agent Skill 编排层：研究问题 -> 识别策略 -> 数据审计 -> Stata/R 脚手架 -> 离线质量核验 -> 论文写作质检和 session 管理。

## 2. 安装

建议先把 pip 缓存和临时目录放到 G 盘，避免 C 盘空间被安装缓存占用：

```powershell
New-Item -ItemType Directory -Force G:\dev-cache\pip,G:\dev-cache\tmp | Out-Null
$env:PIP_CACHE_DIR = "G:\dev-cache\pip"
$env:TEMP = "G:\dev-cache\tmp"
$env:TMP = "G:\dev-cache\tmp"
```

建议使用可编辑安装，顺便装测试依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

验证 CLI：

```powershell
python scripts\cli.py --help
python scripts\cli.py doctor --json
econ-studio --help
```

如果只想跑脚本，不注册 entry point，也可以一直使用：

```powershell
python scripts\cli.py <command>
```

## 3. 最小可运行路径

```powershell
python scripts\cli.py init min-wage-demo `
  --rq "最低工资调整对青年就业率的因果效应" `
  --strategy unsure `
  --target-journal CSSCI `
  --data-source "城市-年份面板"

python scripts\cli.py identify `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\identify_strategy.md

python scripts\cli.py scaffold `
  --strategy DiD `
  --session min-wage-demo `
  --lang stata

python scripts\cli.py data-audit `
  --csv examples\case-min-wage-did\panel_sample.csv `
  --required city_id `
  --required year `
  --required minimum_wage_increase `
  --required youth_employment_rate `
  --key city_id `
  --key year `
  --outcome youth_employment_rate `
  --treatment minimum_wage_increase `
  --cluster city_id `
  --min-clusters 3 `
  --output outputs\min-wage-demo\data_audit.md `
  --fail-on-critical

python scripts\cli.py verify `
  --strategy DiD `
  --analysis outputs\min-wage-demo `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\verify_report.md `
  --fail-under 6

python scripts\cli.py paper outline `
  --brief examples\case-min-wage-did\research_brief.yaml `
  --output outputs\min-wage-demo\paper_outline.md

python scripts\cli.py paper audit `
  --paper examples\case-min-wage-did\draft_excerpt.md `
  --output outputs\min-wage-demo\paper_audit.md `
  --fail-under 8
```

预期结果：

- `outputs\min-wage-demo\manifest.json`：论文 session 元数据
- `outputs\min-wage-demo\identify_strategy.md`：识别策略推荐
- `outputs\min-wage-demo\data_audit.md`：示例 CSV 数据结构审计
- `outputs\min-wage-demo\do\*.do`：Stata 分析骨架
- `outputs\min-wage-demo\verify_report.md`：离线质量核验报告
- `outputs\min-wage-demo\paper_outline.md` / `paper_audit.md`：论文大纲和草稿质检报告

`outputs/` 已被 `.gitignore` 忽略，不会误提交。

## 4. 五阶段命令

| 阶段 | 命令 | 说明 |
|---|---|---|
| doctor | `python scripts\cli.py doctor --json` | 检查本地环境和关键文件 |
| question | `python scripts\cli.py brainstorm` | 打开研究问题模板 |
| design | `python scripts\cli.py identify --brief <brief.yaml>` | 推荐识别策略 |
| data-audit | `python scripts\cli.py data-audit --csv <panel.csv> --key id --key year` | 检查重复键、缺失、处理变量变化、结果变量类型和聚类数量 |
| execute | `python scripts\cli.py scaffold --strategy DiD --session <name> --lang stata` | 生成 Stata/R 骨架 |
| verify | `python scripts\cli.py verify --strategy DiD --analysis outputs\<name>` | 离线质量闸门 |
| paper | `python scripts\cli.py paper outline/audit` | 生成论文大纲或审计草稿结构、引用风险、空泛写作和图表标题 |
| write | `python scripts\cli.py init/list/show/add/add-review/promote` | 管理论文版本 |

短别名：

```powershell
python scripts\cli.py b          # brainstorm
python scripts\cli.py d --json   # doctor
python scripts\cli.py i --help   # identify
python scripts\cli.py sc --help  # scaffold
python scripts\cli.py da --help  # data-audit
python scripts\cli.py v --help   # verify
python scripts\cli.py p --help   # paper
```

## 5. 可选配置

复制 `.env.example`：

```powershell
Copy-Item .env.example .env
notepad .env
```

当前离线路径不需要任何 API key。以下配置只用于可选增强：

- `STATA_PATH`：安装 Stata 后，可记录本机 Stata 路径
- `SEMANTIC_SCHOLAR_API_KEY` / `OPENALEX_EMAIL`：后续外部引用核验
- `ARK_API_KEY` / `OPENAI_API_KEY`：后续视觉表格核验或 LLM 辅助

## 6. 可选：Stata / R

Stata-first 是本项目的默认使用习惯，但测试和脚手架生成不要求本机安装 Stata。

Stata 常用包：

```stata
ssc install reghdfe, replace
ssc install estout, replace
ssc install csdid, replace
ssc install rdrobust, replace
ssc install rddensity, replace
ssc install coefplot, replace
```

R 的现代 DiD/RDD 生态：

```r
install.packages(c("fixest", "did", "rdrobust", "Synth", "MatchIt"))
```

`HonestDiD` 可能需要按其上游说明单独安装。

## 7. 注册为 Agent Skill

如果要让 Claude Code / Cursor 识别本项目，可以把仓库目录链接到对应 skills 目录。

PowerShell 示例：

```powershell
cmd /c mklink /J "%USERPROFILE%\.claude\skills\econ-paper-studio" "G:\github_project_0516\econ-paper-studio"
cmd /c mklink /J "%USERPROFILE%\.cursor\skills\econ-paper-studio" "G:\github_project_0516\econ-paper-studio"
```

删除链接不会删除主项目：

```powershell
cmd /c rmdir "%USERPROFILE%\.claude\skills\econ-paper-studio"
cmd /c rmdir "%USERPROFILE%\.cursor\skills\econ-paper-studio"
```

## 8. 测试

```powershell
python -m pytest tests/ -p no:cacheprovider
python -m ruff check scripts tests
python -m py_compile scripts\cli.py scripts\doctor.py scripts\identify_strategy.py scripts\scaffold.py scripts\session.py scripts\robustness_checks.py scripts\data_audit.py scripts\paper_pipeline.py
```

当前测试全部离线运行，不需要 Stata、R、LLM API key 或网络。

## 9. 常见问题

### `econ-studio` 命令不存在

先运行：

```powershell
python -m pip install -e ".[dev]"
```

或者直接用：

```powershell
python scripts\cli.py --help
```

### 中文输出乱码

脚本尽量使用 Windows-safe 输出。若终端仍乱码，先执行：

```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
chcp 65001
```

### `data-audit` 有 critical failure

先处理重复键、缺失、处理变量不变化或结果变量不是数值这类问题。它们通常会导致分母错位、join explosion 或无法识别。

### `verify` 或 `paper audit` 得分不高

这不是报错，而是质量闸门在提示缺口。按 `Next Actions` 补齐平行趋势、安慰剂、多重检验校正、引用、贡献句、图表标题或写作问题，再重新运行。

### `git status` 看到 `outputs/`

`outputs/` 已被 `.gitignore` 忽略。如果之前手动添加过，先从 index 移除：

```powershell
git rm -r --cached outputs
```

不要删除真实研究输出，除非你确认不再需要。

## 10. 进一步阅读

- [README.md](./README.md) - 项目简介和快速试用
- [docs/QUICKSTART_CN.md](./docs/QUICKSTART_CN.md) - 更详细的最小可运行路径
- [docs/CLI_REFERENCE.md](./docs/CLI_REFERENCE.md) - 命令和参数说明
- [docs/AGENT_RUNBOOK.md](./docs/AGENT_RUNBOOK.md) - agent 接手项目的执行顺序
- [docs/SKILL_LOADOUT.md](./docs/SKILL_LOADOUT.md) - 配套 skills 加载清单
- [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md) - 项目目录和提交边界
- [docs/QUALITY_GATES.md](./docs/QUALITY_GATES.md) - 投稿/交付前质量闸门
- [WORKFLOW.md](./WORKFLOW.md) - 五阶段工作流
- [RESEARCH_QUESTION.md](./RESEARCH_QUESTION.md) - 研究问题模板
- [TESTING.md](./TESTING.md) - 测试说明
- [PROJECT_PLAN.md](./PROJECT_PLAN.md) - 当前状态和路线图
