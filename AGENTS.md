# Agent Instructions: econ-paper-studio

这个仓库是给 agent 接手实证经济学论文用的，不是普通 Python 包说明书。接手时先按下面顺序做。

## 先读

1. `SKILL.md`
2. `skill_loadout.yaml`
3. `research_skill_registry.yaml`
4. `docs/UPSTREAM_SKILLS.md`
5. `docs/AGENT_RUNBOOK.md`
6. `docs/SKILL_LOADOUT.md`
7. `docs/QUALITY_GATES.md`

## 定位

`econ-paper-studio` 是 agent-native 研究工作流：

- 允许并鼓励 agent 调 Stata/R/Python、联网引用核验、MCP、数据库、Coze workflow、OpenAlex/Crossref/Semantic Scholar 等真实工具。
- 本地 CLI 质量闸门用于预检、流程回归和交付前核验，不是为了限制 agent 调用真实研究工具。
- 不允许在没有真实数据、真实运行或真实来源核验时编造结果、引用或结论。
- `ledger` 和 `claim-audit` 是论文结论的证据账本，不是装饰性文档；核心结论必须能回到表图、代码、数据、样本、模型和引用核验状态。

## 必须加载的配套 skills

可用时按 `skill_loadout.yaml` 和 `docs/UPSTREAM_SKILLS.md` 加载或部署：

- `superpowers:using-superpowers`
- `superpowers:executing-plans`
- `superpowers:systematic-debugging`
- `superpowers:verification-before-completion`
- `data:statistical-analysis`
- `data:validate-data`
- `data:create-viz`
- `content-research-writer`
- `documents:documents`

缺失时不要停住，按 `docs/AGENT_RUNBOOK.md` 和 `docs/QUALITY_GATES.md` 降级执行。

上游 skill 仓库不要复制进本仓库。需要安装时放到 agent 的 skill 目录，或放到不提交的外部参考目录，并先读上游 `SKILL.md` 再调用。

## 标准接手流程

1. `econ-studio doctor --strict`
2. 读目标论文/数据项目的 handoff、README、changelog、audit 文档。
3. `econ-studio skills plan --task full-paper` 确认本轮应加载哪些上游 skills。
4. `econ-studio identify` 和 `econ-studio design-memo` 确认识别策略、estimand、假设和威胁。
5. `econ-studio data-audit` 查数据结构并生成 data contract。
6. 真实运行 Stata/R/Python 代码，不能只看模板。
7. 用 `econ-studio ledger init/add/audit` 记录表图、代码、数据、样本、模型、estimand 和聚类层级。
8. `econ-studio verify` 查方法证据和引用/写作风险。
9. `econ-studio claim-audit` 和 `econ-studio reviewer-gauntlet` 查论文 claim 是否有证据链。
10. `econ-studio paper audit` 查论文草稿。
11. 需要 docx 时用 `documents:documents` 或对应文档工具做视觉 QA。
12. 结束前跑 `doctor` 和相关质量闸门，并写清哪些模型、引用、文档渲染已经真实执行。

## 边界

- 静态检查通过不等于实证结果正确。
- paper audit 通过不等于引用真实。
- data-audit 通过不等于数据来源可靠。
- 真实论文必须记录脚本路径、数据版本、样本限制、聚类层级、引用核验方式。
