# Econ Paper Studio

面向实证经济学论文的本地工作流 CLI / Agent Skill。它不替研究者“自动写论文”，而是把一篇经验研究拆成可检查、可跳过、可复现的五个阶段：

```text
question -> design -> execute -> verify -> write
```

定位很简单：把 StatsPAI 的计量执行、Academic Research Skills 的论文流程、Stata skill 的语法/包参考、social-science skills 的方法硬约束，编排成一个中文友好、Stata-first、离线可跑的研究助手。

## 当前可用

| 阶段 | 命令 | 当前能力 |
|---|---|---|
| doctor | `python scripts\cli.py doctor --json` | 自检 Python 版本、关键文件、核心依赖和可选依赖 |
| question | `python scripts\cli.py brainstorm` | 打开研究问题五问模板 |
| design | `python scripts\cli.py identify --brief <brief.yaml>` | 根据 brief 推荐 DiD/RDD/IV/SCM/Matching/DML，并输出文献基准与稳健性清单 |
| execute | `python scripts\cli.py scaffold --strategy DiD --session <name> --lang stata` | 生成 Stata/R 分析骨架、表图目录和可复现 session 结构 |
| verify | `python scripts\cli.py verify --strategy DiD --analysis outputs\<name> --paper draft.md` | 离线扫描方法稳健性证据、AI 味短语、引用占位符和因果过度声称 |
| write | `python scripts\cli.py init/list/show/add/add-review/promote` | 管理论文版本、审稿意见和终稿标记 |

## 快速试用

PowerShell 下直接跑：

```powershell
python -m pip install -e ".[dev]"

python scripts\cli.py doctor --json

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

python scripts\cli.py verify `
  --strategy DiD `
  --analysis outputs\min-wage-demo `
  --output outputs\min-wage-demo\verify_report.md `
  --fail-under 6
```

如果安装了 package entry point，也可以把 `python scripts\cli.py` 换成 `econ-studio`。

## 设计取舍

本项目不重造这些上游能力：

| 上游 | 这里怎么用 |
|---|---|
| `brycewang-stanford/StatsPAI` | 作为计量执行和函数对照层；本仓库只生成可落地调用和检查清单 |
| `Imbad0202/academic-research-skills` | 借鉴 research -> write -> review -> revise -> finalize 流程，尤其 integrity gate |
| `obra/superpowers` | 借鉴设计、TDD、验证先行的工程纪律 |
| `dylantmoore/stata-skill` | 借鉴 Stata idiom 和社区包参考，脚手架默认 Stata-first |
| `sshtomar/claude-code-skills-social-science` | 借鉴“方法要求必须有证据”的约束方式，如 DiD 必查平行趋势 |

本仓库做的是 adapter + 编排层：把研究问题、识别策略、代码骨架、稳健性证据、论文版本放在一个本地 session 里。

## Stage 4 verifier 的边界

`verify` 是离线静态检查器。它会扫描 `.do` / `.R` / `.py` / `.md` / `.tex` 等文本文件，检查是否有：

- DiD: cluster SE、平行趋势/event study、现代错时 DiD 替代、安慰剂、多重检验校正
- RDD: `rdrobust`、密度/操纵检验、bandwidth、placebo cutoff、donut RD
- IV: first-stage/weak-IV、排除限制、over-id、弱工具稳健区间
- 写作: 常见 AI 味填充短语
- 写作: 因果过度声称，例如未限定的 `robustly demonstrates a causal effect`
- 引用: 明显 placeholder、缺 References/Bibliography 的风险

它不会声称“证明引用真实”或“证明结果正确”。真实引用仍需要 Crossref/OpenAlex/Semantic Scholar 或人工核验；数值结果仍需要在 Stata/R/Python 中实际运行。

## Testing

当前测试为 111 个，全部离线、无 API key、无需 Stata/R：

```powershell
python -m pytest tests/ -p no:cacheprovider
```

覆盖：

| 测试文件 | 数量 | 覆盖 |
|---|---:|---|
| `tests/test_cli.py` | 25 | CLI 子命令、别名、Windows ASCII-safe banner |
| `tests/test_doctor.py` | 2 | 本地环境与项目文件健康检查 |
| `tests/test_identify_strategy.py` | 30 | 六类识别策略评分、brief 加载、报告渲染 |
| `tests/test_scaffold.py` | 20 | Stata/R 模板、目录生成、CLI 端到端 |
| `tests/test_session.py` | 27 | session 生命周期、manifest、CHANGELOG、终稿标记 |
| `tests/test_robustness_checks.py` | 7 | Stage 4 verifier、AI 味扫描、因果过度声称、引用 placeholder、fail-under |

## License

MIT。详见 [LICENSE](./LICENSE)。
