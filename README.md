# 计量经济学实证和论文 Agent

> 从模糊研究想法到 R&R response 的端到端工作流。  
> 给中国实证研究学生 + 中国期刊投稿场景。

---

## 项目状态

🚧 **初始化中**（2026-04-19）

本项目当前处于规划与骨架搭建阶段。详细的全网调研报告与仿建策略见：

- [`RESEARCH_REPORT.md`](../design%20agent/RESEARCH_REPORT.md) — 全网调研报告（10K+ stars 项目全景 + 5 个最值得仿建项目深度分析）
- [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) — 项目规划与拆解（接下来要做什么）
- [`SKILL.md`](./SKILL.md) — Skill 入口（被 Cursor / Claude Code 自动识别）

---

## 一句话定位

融合 **Stanford 团队的 StatsPAI 计量执行** + **Imbad0202 的学术论文 pipeline** + **obra 的工程纪律** + **Stata 大佬们的方法论沉淀**，给中国实证研究者一个**可裁剪的本地工作流**。

---

## 不重新造的轮子

我们 **不做** 这些（已有人做得很好，我们 reference + adapter）：

| 上游 | 我们怎么用 |
|---|---|
| [`brycewang-stanford/StatsPAI`](https://github.com/brycewang-stanford/StatsPAI) | 直接 `pip install`，作为执行层 |
| [`Imbad0202/academic-research-skills`](https://github.com/Imbad0202/academic-research-skills) | junction 链接到 `~/.claude/skills/`，论文写作复用 |
| [`obra/superpowers`](https://github.com/obra/superpowers) | 同上，工程纪律复用 |
| [`sshtomar/claude-code-skills-social-science`](https://github.com/sshtomar/claude-code-skills-social-science) | 同上，DiD/RCT 方法论复用 |
| [`dylantmoore/stata-skill`](https://github.com/dylantmoore/stata-skill) | 同上，Stata reference 复用 |

---

## 我们做什么（差异化）

1. **本地中文优先** —— CHN/EN 双语 skills，集成 CSSCI/CSI 期刊定位、SSCI 投稿模板
2. **Stata-first** —— CoPaper.AI 等偏 Python，我们尊重国内学术习惯
3. **数据脱敏 + 隐私合规** —— 中国数据敏感，提供本地数据处理工具
4. **R&R 全流程** —— 从研究问题到 response 一条龙，含中文期刊 referee response 模板
5. **可裁剪** —— 不强制走完五阶段，每阶段有"何时跳过"判断

---

## 五阶段工作流

```
question  →  design  →  execute  →  verify  →  publish
```

| 阶段 | 用什么 | 解决什么 |
|---|---|---|
| **question** | `RESEARCH_QUESTION.md` 模板 | 防止"我想做个研究"直接进入数据导致 generic 结果 |
| **design** | `scripts/identify_strategy.py` 决策树 | 根据问题类型 + 数据结构推荐 DiD/RDD/IV/SCM/Matching |
| **execute** | `scripts/scaffold_dofile.py` 生成 Stata/R/Python 代码骨架 | 把方法选择落到可执行 do-file |
| **verify** | `scripts/robustness_checks.py` 自动稳健性检验 | 平行趋势/安慰剂/Bonferroni/异质性自动化 |
| **publish** | `scripts/paper_session.py` R&R 版本管理 + referee response 起草 | 论文版本追溯 + 审稿意见点对点回应 |

完整说明见 [`WORKFLOW.md`](./WORKFLOW.md)（待写）。

---

## 快速试用

🚧 **scripts 还在开发中**

待 v0.1.0 release 后会提供：

```powershell
# 安装依赖
pip install -r requirements.txt

# 注册 skill 到 Cursor / Claude Code
.\scripts\install.ps1

# 用 dry-run 模式跑一遍流程
python scripts\identify_strategy.py --question "最低工资政策对就业的影响" --data panel
```

---

## License

MIT。详见 [LICENSE](./LICENSE)（待加）。

---

## Credits

- 上游导航：[Awesome Agent Skills for Empirical Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research)（CoPaper.AI / Stanford REAP）
- 计量执行：[StatsPAI](https://github.com/brycewang-stanford/StatsPAI)
- 论文 pipeline：[Academic Research Skills](https://github.com/Imbad0202/academic-research-skills)
- 工程纪律：[obra/superpowers](https://github.com/obra/superpowers)
- Stata reference：[dylantmoore/stata-skill](https://github.com/dylantmoore/stata-skill)
- 社会科学方法：[sshtomar/claude-code-skills-social-science](https://github.com/sshtomar/claude-code-skills-social-science)
