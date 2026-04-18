# 中文安装与使用指南

> 面向 Windows + PowerShell 用户。macOS / Linux 用户请把 PowerShell 命令换成 bash。

---

## 1. 项目位置

| 路径 | 说明 |
|---|---|
| `G:\计量经济学实证和论文agent\` | **主项目目录**（你正在看的这个） |
| `G:\design agent\RESEARCH_REPORT.md` | 全网调研报告（生态地图） |

---

## 2. 环境准备

需要 Python 3.10+。

### 安装核心依赖

```powershell
cd "G:\计量经济学实证和论文agent"
pip install -r requirements.txt
```

最关键的是 [`StatsPAI`](https://github.com/brycewang-stanford/StatsPAI) —— Stanford 团队做的 agent-native 计量经济学包，390+ 函数，统一 API。

### 验证安装

```powershell
python -c "import statspai as sp; print(sp.__version__); print(len(sp.list_functions()))"
```

应该输出版本号和函数数量（~390）。

### 可选：装 Stata

如果你做计量研究，强烈推荐装 Stata 17+。然后可以装 [`stata-mcp`](https://github.com/SepineTam/stata-mcp) 让 Claude 直接调 Stata 命令。

```powershell
# 装 stata-mcp（可选）
pip install stata-mcp
```

把 Stata 路径填到 `.env`：

```env
STATA_PATH=C:\Program Files\Stata18\StataSE-64.exe
```

### 可选：装 R + 现代 DiD 包

如果你想用 R 做 staggered DiD：

```r
install.packages(c("fixest", "did", "didimputation", "HonestDiD",
                   "rdrobust", "Synth", "MatchIt"))
```

---

## 3. 配置 .env

```powershell
Copy-Item .env.example .env
notepad .env
```

最少要填的是 `ARK_API_KEY`（火山方舟）或者 `OPENAI_API_KEY`，让 verify 阶段能调视觉模型检查表/图。

---

## 4. 装上游 skills（推荐，但不强制）

我们的项目是 **编排层**，调上游已有的 skills。最好先把它们装好：

### 方式一：junction 链接（推荐）

```powershell
# 把 _references/ 里的几个 skills 链到 Cursor 和 Claude Code 的 skills 目录
cmd /c mklink /J "C:\Users\$env:USERNAME\.cursor\skills\econ-paper-studio" "G:\计量经济学实证和论文agent"
cmd /c mklink /J "C:\Users\$env:USERNAME\.claude\skills\econ-paper-studio" "G:\计量经济学实证和论文agent"
```

### 方式二：手动 git clone 到 IDE skills 目录

```powershell
cd "C:\Users\$env:USERNAME\.claude\skills"

git clone --depth 1 https://github.com/Imbad0202/academic-research-skills.git
git clone --depth 1 https://github.com/sshtomar/claude-code-skills-social-science.git
git clone --depth 1 https://github.com/dylantmoore/stata-skill.git
```

---

## 5. 跑五阶段（v0.1.0-init 阶段，scripts 还在开发中）

🚧 当前 v0.1.0-init 状态，scripts 还没全部写好。规划中的命令是：

```powershell
cd "G:\计量经济学实证和论文agent"

# 阶段 1：研究问题澄清（无脚本，直接读模板）
notepad RESEARCH_QUESTION.md

# 阶段 2：识别策略选择（开发中）
python scripts\identify_strategy.py --rq outputs\my-paper\RQ.md

# 阶段 3：生成 Stata/R 代码骨架（开发中）
python scripts\scaffold.py --strategy DiD --session my-paper

# 阶段 4：稳健性清单（开发中）
python scripts\robustness_checklist.py --session my-paper

# 阶段 5：R&R response（开发中）
python scripts\referee_response.py --session my-paper --letter referee.pdf
```

或者用统一 CLI（开发中）：

```powershell
econ-studio init my-paper --rq "..." --strategy DiD
econ-studio identify --rq RQ.md
econ-studio scaffold --strategy DiD --session my-paper
econ-studio verify --strategy DiD --session my-paper
econ-studio write --session my-paper
```

详细见 [`WORKFLOW.md`](./WORKFLOW.md)。

---

## 6. 在 Cursor / Claude Code 里触发

注册 skill 后，直接在对话里说：

```
用 econ-paper-studio 帮我做最低工资 DiD 的研究设计
```

```
用 econ-paper-studio 帮我审一下我的 R&R response，第二个审稿人那段
```

Cursor / Claude Code 会自动识别 SKILL.md 的 description 并触发本工作流。

---

## 7. 不需要本项目就能上手的最小路径

如果你想快速试用，**不装我们的项目也行**，直接用上游：

```powershell
# 只装 StatsPAI
pip install statspai

# Python 一行代码跑 CS-DiD
python -c "
import statspai as sp
import pandas as pd
df = pd.read_csv('your_data.csv')
result = sp.callaway_santanna(data=df, y='outcome', g='treat_year', t='year', id='unit_id')
print(result.summary())
result.to_latex('cs_did_table.tex')
"
```

这样你就能感受到 StatsPAI 的 agent-native 设计有多顺滑。我们的项目只是在它上面加了**研究问题 → 识别策略 → 代码骨架 → 稳健性 → 论文** 的完整工作流编排。

---

## 8. 故障排查

### `pip install statspai` 失败

可能是 Python 版本太低。检查：

```powershell
python --version  # 必须 >= 3.10
```

### Stata 命令找不到

确认 `.env` 里 `STATA_PATH` 填了正确路径，并且 `stata-mcp` 已装。

### Cursor 看不到 skill

确认 junction 已建：

```powershell
ls "C:\Users\$env:USERNAME\.cursor\skills\econ-paper-studio"
```

应该显示项目目录内容。如果没有，重做 junction 步骤。

### 删除 junction（不影响主项目）

```powershell
cmd /c rmdir "C:\Users\$env:USERNAME\.cursor\skills\econ-paper-studio"
cmd /c rmdir "C:\Users\$env:USERNAME\.claude\skills\econ-paper-studio"
```

---

## 9. 进一步学习

- [WORKFLOW.md](./WORKFLOW.md) — 五阶段工作流总章程
- [PROJECT_PLAN.md](./PROJECT_PLAN.md) — 完整任务拆解
- [RESEARCH_QUESTION.md](./RESEARCH_QUESTION.md) — 阶段 1 详细模板
- [`../design agent/RESEARCH_REPORT.md`](../design%20agent/RESEARCH_REPORT.md) — 全网调研报告

外部资源：

- [Awesome Agent Skills for Empirical Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research) — 实证研究 skills 元导航
- [StatsPAI 文档](https://github.com/brycewang-stanford/StatsPAI) — 计量执行包
- [Academic Research Skills](https://github.com/Imbad0202/academic-research-skills) — 论文写作 pipeline
- [obra/superpowers](https://github.com/obra/superpowers) — 工程方法论
- [Claude Code & Cowork for Academic Research](https://cornwl.github.io/files/claude-academic-guide.html) — 经济学家实操指南
