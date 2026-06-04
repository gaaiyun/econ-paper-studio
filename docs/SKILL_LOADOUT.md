# Skill Loadout

`econ-paper-studio` 本身是一个编排 skill。它能独立运行，但如果要让 agent 真正接手“计量执行 + 论文写作 + 引用边界 + 交付核验”，建议同时加载下面这些 skills。

同一份清单也放在根目录的 `skill_loadout.yaml`。人读这份文档，agent 或脚本可以读 YAML。平台入口和安全命令映射放在 `AGENTS.md` 与 `agent_manifest.yaml`。上游安装和来源看 `docs/UPSTREAM_SKILLS.md`。

## 加载顺序

| 顺序 | Skill | 作用 |
|---:|---|---|
| 1 | `superpowers:using-superpowers` | 先确认本轮任务需要哪些技能，避免直接开改 |
| 2 | `superpowers:executing-plans` | 按计划推进，长任务不跳步骤 |
| 3 | `superpowers:systematic-debugging` | 处理 CSDID、DML、TERGM、Stata/R/Python 报错时先找根因 |
| 4 | `superpowers:verification-before-completion` | 结束前必须跑验证，不能凭感觉说完成 |
| 5 | `data:statistical-analysis` | 约束效应量、显著性、样本量、多重检验和因果表述边界 |
| 6 | `data:validate-data` | 查重复键、join explosion、缺失、分母错位、聚类层级和结论是否被数据支持 |
| 7 | `data:create-viz` | 做论文级图形，检查坐标、尺度、误差线、图注和可读性 |
| 8 | `content-research-writer` | 写论文结构、引言、贡献、文献组织和逐段反馈 |
| 9 | `documents:documents` | 处理 Word/docx 投稿稿、渲染和视觉 QA |

如果平台不支持自动一次加载多个 skills，就按这个顺序手动加载。先加载流程类，再加载数据/写作/文档类。

## 上游 Skills

这些资料不是本仓库的一部分，也不应该复制进本仓库。部署本项目给 agent 使用时，应把它们安装到 agent 自己的 skill 目录，或放在不提交的外部参考目录。

| 资料 | 用法 |
|---|---|
| `Awesome-Agent-Skills-for-Empirical-Research` | 上游导航，帮助 agent 找到经验研究任务所需技能 |
| `StatsPAI` | 计量函数、因果推断 API、Stata/R 结果对照 |
| `academic-research-skills` | 论文流程、文献组织、review/revise/finalize |
| `obra/superpowers` | 技能路由、执行计划、系统排错、完成前核验 |
| `stata-skill` | Stata do-file、社区包、数据管理和图表导出 |
| `claude-code-skills-social-science` | DiD/RDD/IV 等社会科学方法纪律 |
| `awesome-ai-research-writing` | 查逻辑检查、图表标题、实验分析、reviewer 视角和模型选择 |
| `humanizer` | 查空泛拔高、promotional language、vague attribution、AI 高频词、破折号滥用、三段式堆砌 |
| `AI-research-SKILLs/ml-paper-writing` | 保留“不编造引用”“repo-first 理解”“one-sentence contribution”“reviewer checklist” |
| `AI-research-SKILLs/academic-plotting` | 保留 booktabs、矢量图、误差线、caption、审稿可读性 |

经济学论文不要硬套机器学习会议术语。可以借鉴写作纪律和图表标准，但识别策略、稳健性和贡献表述要按实证经济学来写。

## 在本项目中的落点

| 本项目文件 | 对应技能 |
|---|---|
| `scripts/data_audit.py` | `data:validate-data` |
| `scripts/identify_strategy.py` | `data:statistical-analysis` + 社会科学方法约束 |
| `scripts/scaffold.py` | Stata/R 参考 + 计量执行 |
| `scripts/robustness_checks.py` | `verification-before-completion` + 方法稳健性 |
| `scripts/paper_pipeline.py` | `content-research-writer` + `humanizer` + citation boundary |
| `references/writing_quality_protocol.md` | 去空话、贡献句、引用边界、图表标题 |
| `references/data_validation_protocol.md` | 数据结构审计和并表风险 |
| `AGENTS.md` / `agent_manifest.yaml` | 平台入口、接手顺序和命令边界 |

## 缺失时怎么降级

| 缺失项 | 降级方式 |
|---|---|
| 没有 superpowers skills | 仍按 `AGENT_RUNBOOK.md` 的顺序执行，并在结束前跑 `QUALITY_GATES.md` |
| 没有 data skills | 跑 `econ-studio data-audit` 和 `econ-studio verify`，但需要人工检查统计口径 |
| 没有 writing/humanizer skills | 跑 `econ-studio paper audit`，再按 `references/writing_quality_protocol.md` 人工修 |
| 没有 documents skill | Markdown/LaTeX 仍可审计；Word/docx 需要人工渲染检查 |

## Agent 使用提示

当用户说“用 econ-paper-studio 接手论文/计量项目”时，agent 应先做三件事：

1. 读 `AGENTS.md`、`SKILL.md`、`agent_manifest.yaml`、`WORKFLOW.md`、`docs/AGENT_RUNBOOK.md`。
2. 按 `docs/UPSTREAM_SKILLS.md` 部署、定位或加载上游 skills。
3. 跑 `econ-studio doctor --strict`，确认本地入口和依赖可用。

之后再开始改数据、跑模型或写论文。不要跳过数据审计，也不要在没有来源核验时补引用。
