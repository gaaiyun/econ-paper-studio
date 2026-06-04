# Agent Runbook

这个 runbook 给接手项目的 agent 看。目标不是“写得更像论文”，而是把研究过程按顺序推进，留下可复查的证据。

## 0. 接手前先做

```powershell
cd "<path-to-econ-paper-studio>"
econ-studio doctor --strict
```

然后读：

1. `AGENTS.md`
2. `SKILL.md`
3. `agent_manifest.yaml`
4. `docs/SKILL_LOADOUT.md`
5. `docs/UPSTREAM_SKILLS.md`
6. `WORKFLOW.md`
7. 目标 session 或目标论文目录里的 handoff / README / changelog

如果用户给了自己的数据目录或论文目录，先读那里的说明。不要先改文件。

如果平台支持 skills，先按 `skill_loadout.yaml` 和 `docs/UPSTREAM_SKILLS.md` 加载上游技能包；如果不支持，就读取对应上游文档，并把缺失项写进交付说明。

## 1. 研究问题

如果用户没有给清楚的研究问题，先把 brief 补完整。

最低要求：

- X 是什么，Y 是什么；
- 样本单位和时间单位是什么；
- 为什么 X 的变化有识别意义；
- 主要内生性威胁是什么；
- 目标期刊或交付场景是什么。

产物是 `research_brief.yaml`。可以参考 `examples/case-min-wage-did/research_brief.yaml`。

## 2. 识别策略

```powershell
econ-studio identify `
  --brief path\to\research_brief.yaml `
  --output outputs\<session>\identify_strategy.md
```

读输出时不要只看排名第一。还要看：

- 被排除的方法为什么不合适；
- 剩余识别威胁是什么；
- 哪些稳健性是必须补的。

## 3. 数据审计

在任何回归前先跑：

```powershell
econ-studio data-audit `
  --csv path\to\analysis_panel.csv `
  --key unit_id `
  --key year `
  --outcome outcome_var `
  --treatment treatment_var `
  --cluster cluster_id `
  --output outputs\<session>\data_audit.md `
  --fail-on-critical
```

critical failure 不要硬跑模型。先处理重复键、空样本、处理变量不变化、结果变量不是数值这类问题。

## 4. 生成代码骨架

```powershell
econ-studio scaffold `
  --strategy DiD `
  --session <session> `
  --lang stata
```

生成的是骨架，不是真实结果。下一步要替换变量名、数据路径、固定效应、聚类层级和导出路径。

## 5. 计量核验

```powershell
econ-studio verify `
  --strategy DiD `
  --analysis outputs\<session> `
  --paper path\to\draft.md `
  --output outputs\<session>\verify_report.md `
  --fail-under 6
```

`verify` 只检查脚本和文本中有没有证据钩子。它不跑 Stata/R，也不证明结果正确。

## 6. 论文写作

先从大纲开始：

```powershell
econ-studio paper outline `
  --brief path\to\research_brief.yaml `
  --output outputs\<session>\paper_outline.md
```

有草稿后跑：

```powershell
econ-studio paper audit `
  --paper path\to\draft.md `
  --output outputs\<session>\paper_audit.md `
  --fail-under 8
```

重点改：

- 空泛的贡献表述；
- 未限定的因果声称；
- 作者年份占位符和 citation-needed；
- “结果”“图 1”这种信息不足的标题；
- 没有说明样本、时间、估计量和不确定性的表图注。

## 7. 版本记录

```powershell
econ-studio init <session> --rq "..." --strategy DiD
econ-studio add <session> --version v1 --paper path\to\draft.md --note "first complete draft"
econ-studio add-review <session> --version r1 --letter path\to\review.md --decision major
econ-studio promote <session> --version v2
```

每一轮都要能说明：改了什么、为什么改、证据在哪个脚本或表图里。

## 8. 结束前必须说明

结束前至少确认：

- `econ-studio doctor --strict` 能启动本项目入口；
- 数据审计、方法核验和论文审计的报告路径已经写清楚；
- 哪些模型真实运行过，哪些只是脚手架或待运行；
- 哪些引用真实核验过，哪些还只是待核验；
- 交付稿没有把静态检查包装成实证结果。

没有这些说明，就不要说完成。
