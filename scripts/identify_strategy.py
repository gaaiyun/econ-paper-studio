#!/usr/bin/env python3
"""
identify_strategy.py — 阶段 2：识别策略选择

输入研究问题 brief（YAML），通过决策树推荐 1-2 个候选识别策略，
列出每个的关键 trade-off + 文献基准 + StatsPAI 函数对照 + 必做稳健性。

用法:
  # 交互式：从命令行回答几个问题
  python scripts/identify_strategy.py --interactive

  # 从已有 brief 推荐
  python scripts/identify_strategy.py --brief outputs/my-paper/research_brief.yaml

  # 输出 markdown 报告
  python scripts/identify_strategy.py --brief brief.yaml --output strategy.md
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ============ 决策树规则 ============

@dataclass
class Strategy:
    name: str
    chinese: str
    score: float = 0.0  # 0-100，越高越推荐
    rationale: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    statspai_funcs: list[str] = field(default_factory=list)
    robustness_must: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)


def evaluate_strategies(brief: dict) -> list[Strategy]:
    """根据 brief 评估各策略的适用性，返回按 score 降序排列的策略列表。"""

    data = brief.get('data', {})
    structure = (data.get('structure') or '').lower()
    seed = (brief.get('identification_seed') or '').lower()
    natural_exp = (brief.get('natural_experiment') or '').lower()
    confounders = brief.get('confounders', []) or []

    strategies: list[Strategy] = []

    # ---------- DiD ----------
    did = Strategy(
        name='DiD',
        chinese='双重差分',
        references=[
            "Bertrand, Duflo & Mullainathan (2004) — How Much Should We Trust DiD",
            "Callaway & Sant'Anna (2021) — DiD with multiple time periods",
            "Sun & Abraham (2021) — Estimating dynamic treatment effects",
            "Roth (2022 AERI) — Pretest with Caution",
        ],
        statspai_funcs=[
            "sp.did(...)  # 自动 dispatch 2x2 / staggered",
            "sp.callaway_santanna(data, y, g, t, id)  # 错时治疗推荐",
            "sp.sun_abraham(...)  # 错时治疗 alternative",
            "sp.honest_did(...)  # 平行趋势敏感性",
            "sp.bacon_decomposition(...)  # TWFE 负权重诊断",
        ],
        robustness_must=[
            "事件研究 (event study) 检验平行趋势",
            "Goodman-Bacon 分解（如错时治疗）",
            "HonestDiD 敏感性分析",
            "安慰剂检验：虚假治疗时间 / 虚假治疗组",
            "Cluster SE at treatment unit level",
            "Multi-outcome correction（Bonferroni / Romano-Wolf）如 K>5",
        ],
        pitfalls=[
            "TWFE 在错时治疗下有负权重问题（Goodman-Bacon 2021）",
            "平行趋势检验通过 ≠ 假设满足（Roth 2022）",
            "Cluster SE 选错层级（如个人层 cluster 政策层）",
        ],
    )

    if 'panel' in structure or '面板' in structure:
        did.score += 50
        did.rationale.append('数据是面板结构，DiD 的基础前提满足')
    if 'natural' in natural_exp or '政策' in natural_exp or '冲击' in natural_exp:
        did.score += 30
        did.rationale.append('有自然实验/政策冲击，DiD 识别外生性更强')
    if 'did' in seed or '双重差分' in seed:
        did.score += 20
        did.rationale.append('用户已倾向 DiD')
    if any('遗漏变量' in c or 'confounders' in c.lower() for c in confounders):
        did.score += 10
        did.rationale.append('遗漏变量是主要威胁，DiD 通过 unit FE 部分解决')

    strategies.append(did)

    # ---------- RDD ----------
    rdd = Strategy(
        name='RDD',
        chinese='断点回归',
        references=[
            "Imbens & Lemieux (2008) — RD Designs: A Guide to Practice",
            "Calonico, Cattaneo & Titiunik (2014) — Robust nonparametric CIs (CCT)",
            "McCrary (2008) — Manipulation testing",
            "Cattaneo, Idrobo & Titiunik (2019) — Practical Introduction to RD",
        ],
        statspai_funcs=[
            "sp.rdrobust(y, x, c=0)  # CCT bandwidth + 局部线性",
            "sp.rdplot(y, x, c=0)  # 可视化",
            "sp.rddensity(x, c=0)  # CJM 密度检验（替代 McCrary）",
            "sp.rdpower(y, x, c=0)  # 功效分析",
            "sp.rdsensitivity(y, x, c=0)  # bandwidth 敏感性",
        ],
        robustness_must=[
            "McCrary 密度检验（防止操纵）",
            "替代 bandwidth（CCT optimal vs IK）",
            "替代 polynomial order（局部线性 vs 二次）",
            "Donut RD（剔除 cutoff 附近若干观测）",
            "安慰剂 cutoff（虚假断点）",
            "covariates balance check",
        ],
        pitfalls=[
            "Bandwidth 选择导致过拟合（Gelman-Imbens 2019 反对高阶多项式）",
            "Cutoff 附近样本量太小导致功效不足",
            "存在操纵（如分数线附近作弊）让 RD 失效",
        ],
    )

    if 'cutoff' in seed or '断点' in seed or 'rdd' in seed or '分数线' in seed:
        rdd.score += 80
        rdd.rationale.append('用户已识别明确 cutoff，RDD 适用')
    if 'cross_section' in structure or '截面' in structure:
        rdd.score += 10
        rdd.rationale.append('截面数据，RDD 也可用（不需要面板）')
    if any('test' in c.lower() or '考试' in c or '分数' in c for c in confounders):
        rdd.score += 20
        rdd.rationale.append('提到考试/分数等典型 cutoff 场景')

    strategies.append(rdd)

    # ---------- IV ----------
    iv = Strategy(
        name='IV',
        chinese='工具变量',
        references=[
            "Angrist & Krueger (2001) — Instrumental Variables and the Search for Identification",
            "Andrews, Stock & Sun (2019 ARE) — Weak Instruments",
            "Mogstad, Torgovitsky, Walters (2024) — IV review",
        ],
        statspai_funcs=[
            "sp.ivreg(y ~ x | z + controls)  # 2SLS",
            "sp.liml(...)  # LIML 弱工具变量更稳",
            "sp.jive(...)  # 多工具变量",
            "sp.feols(y ~ x | fe | x ~ z)  # 高维 FE + IV",
        ],
        robustness_must=[
            "First-stage F > 10（弱工具变量阈值，2026 标准更严：> 30）",
            "排除限制（exclusion restriction）经济学论证",
            "多工具变量时做 over-identification test",
            "LIML 作为 2SLS 的 robustness（弱工具更稳）",
            "Anderson-Rubin CI（弱工具变量下唯一可信 CI）",
        ],
        pitfalls=[
            "弱工具变量（F<10）导致 2SLS 严重偏倚",
            "排除限制无法检验，只能论证（最致命）",
            "Compliers 的 LATE ≠ ATE（异质性）",
        ],
    )

    if 'iv' in seed or '工具变量' in seed:
        iv.score += 60
        iv.rationale.append('用户倾向 IV')
    if any('反向因果' in c or 'reverse' in c.lower() for c in confounders):
        iv.score += 20
        iv.rationale.append('反向因果是主要威胁，IV 是经典解决方案')
    iv_candidates = data.get('iv_candidates', []) or []
    if iv_candidates and any(iv_candidates):
        iv.score += 20
        iv.rationale.append(f'已有候选工具变量：{", ".join(iv_candidates)}')

    strategies.append(iv)

    # ---------- SCM ----------
    scm = Strategy(
        name='SCM',
        chinese='合成控制',
        references=[
            "Abadie (2021 JEL) — Using Synthetic Controls: Feasibility, Data Requirements",
            "Ben-Michael, Feller & Rothstein (2021) — ASCM Augmented SCM",
            "Arkhangelsky et al. (2021) — Synthetic Difference-in-Differences",
        ],
        statspai_funcs=[
            "sp.synth(...)  # 经典 Abadie",
            "sp.ascm(...)  # Augmented SCM（小样本更稳）",
            "sp.sdid(...)  # Synthetic DiD",
            "sp.synth_compare(...)  # 一次跑全部 20 个 estimator 对比",
            "sp.synth_recommend(...)  # 自动选最适合",
        ],
        robustness_must=[
            "Pre-period RMSPE 检查",
            "Placebo in-space（其他单位做虚假治疗）",
            "Placebo in-time（虚假治疗时间）",
            "Leave-one-out（去掉一个 donor）",
            "Sensitivity to donor pool 选择",
        ],
        pitfalls=[
            "Donor pool 选择主观（应预先注册）",
            "适用于「少数治疗单位 + 多个对照单位」场景",
            "SC 权重不唯一时如何选（regularization）",
        ],
    )

    if 'scm' in seed or '合成控制' in seed or '合成对照' in seed:
        scm.score += 70
        scm.rationale.append('用户倾向 SCM')
    if 'panel' in structure:
        scm.score += 30
        scm.rationale.append('SCM 需要面板数据')
        # SCM 适合"少数治疗单位"场景
        if data.get('granularity', '').lower() in ('province', 'country', 'state', '省', '国家', '城市'):
            scm.score += 20
            scm.rationale.append('颗粒度是省/国家/城市级，SCM 经典应用场景')

    strategies.append(scm)

    # ---------- PSM / Matching ----------
    matching = Strategy(
        name='Matching',
        chinese='倾向得分匹配',
        references=[
            "Rosenbaum & Rubin (1983) — PSM Original",
            "Imbens (2015 JHR) — Matching Methods in Practice",
            "King & Nielsen (2019) — Why PSM should not be used (provocative)",
        ],
        statspai_funcs=[
            "sp.match(treat, X, method='nn')  # 最近邻",
            "sp.match(..., method='kernel')  # Kernel matching",
            "sp.ebalance(...)  # Entropy balancing（更现代）",
        ],
        robustness_must=[
            "Common support 检查",
            "Covariate balance（标准化差异 < 0.1）",
            "敏感性分析（Rosenbaum bounds）",
            "替代 matching method（NN vs Kernel vs Entropy）",
        ],
        pitfalls=[
            "选择 on observables 假设无法检验（最致命）",
            "King & Nielsen (2019) 指出 PSM 增加 model dependence",
            "近年学术界更推荐 entropy balancing / cardinality matching",
        ],
    )

    if 'matching' in seed or 'psm' in seed or '匹配' in seed:
        matching.score += 60
        matching.rationale.append('用户倾向 Matching')
    if any('选择' in c or 'selection' in c.lower() for c in confounders):
        matching.score += 20
        matching.rationale.append('选择性偏误，但建议优先 IV 而非 PSM')
    matching.score = max(matching.score - 10, 0)  # 整体降权（学术界共识：弱于 DiD/RDD/IV）

    strategies.append(matching)

    # ---------- DML / Causal Forest ----------
    dml = Strategy(
        name='DML',
        chinese='Double Machine Learning',
        references=[
            "Chernozhukov et al. (2018) — Double/debiased ML",
            "Wager & Athey (2018) — Causal Forest",
            "Athey & Imbens (2019) — ML in Econometrics",
        ],
        statspai_funcs=[
            "sp.dml(y, t, X)  # Double ML",
            "sp.causal_forest(y, t, X)  # 异质性 CATE",
            "sp.metalearner(method='X')  # X / S / T learner",
            "sp.tmle(...)  # Targeted ML",
        ],
        robustness_must=[
            "Cross-fitting (K-fold)",
            "Multiple ML methods 对比（lasso / RF / NN）",
            "Sample-splitting 稳定性",
            "Sensitivity to hyperparameters",
        ],
        pitfalls=[
            "Confounders selection on observables 假设依然是核心威胁",
            "ML 模型选择影响估计（不像 OLS 那么 deterministic）",
            "异质性结果难以解读（如何呈现 CATE 分布）",
        ],
    )

    if 'dml' in seed or 'machine' in seed or '机器学习' in seed:
        dml.score += 60
        dml.rationale.append('用户倾向 DML/ML 因果')
    if data.get('sample_size', '').lower() in ('large', '大', '万', '十万', '百万'):
        dml.score += 20
        dml.rationale.append('大样本场景 DML 适用')
    if len(data.get('controls', []) or []) > 10:
        dml.score += 15
        dml.rationale.append('控制变量多，DML 比 OLS 处理高维更稳健')

    strategies.append(dml)

    # 排序
    strategies.sort(key=lambda s: s.score, reverse=True)
    return strategies


# ============ Brief 加载 / 交互 ============

def load_brief(path: Path) -> dict:
    if yaml is None:
        # fallback：JSON 也支持
        return json.loads(path.read_text(encoding='utf-8'))
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def interactive_brief() -> dict:
    """交互式收集 brief。"""
    print('=' * 70)
    print('econ-paper-studio :: Stage 2 — Identification Strategy Selector')
    print('=' * 70)
    print('回答几个问题，根据 5 核心问题（见 RESEARCH_QUESTION.md）。')
    print('每题可以为空（直接回车）。\n')

    def ask(q: str, default: str = '') -> str:
        prompt = f'  {q}'
        if default:
            prompt += f' [{default}]'
        prompt += ': '
        ans = input(prompt).strip()
        return ans or default

    brief = {
        'question': ask('Q1 研究问题（一句话，X→Y 形式）'),
        'data': {
            'structure': ask('Q4 数据结构 (panel/cross_section/ts/nested)', 'panel'),
            'granularity': ask('Q4 颗粒度 (个人/企业/城市/省份)', '城市'),
            'sample_size': ask('Q4 样本量 (small/medium/large)', 'medium'),
            'iv_candidates': [s for s in ask('Q4 IV 候选 (逗号分隔, 可空)').split(',') if s.strip()],
            'controls': [s for s in ask('Q4 控制变量 (逗号分隔, 可空)').split(',') if s.strip()],
        },
        'identification_seed': ask('Q5 识别策略雏形 (DiD/RDD/IV/SCM/PSM/DML/unsure)', 'unsure'),
        'natural_experiment': ask('Q6 自然实验/政策冲击 (描述)'),
        'confounders': [s for s in ask('Q7 主要识别威胁 (反向因果/遗漏变量/选择/...)').split(',') if s.strip()],
    }
    return brief


# ============ 渲染 ============

def render_report(brief: dict, strategies: list[Strategy], top_k: int = 3) -> str:
    lines: list[str] = []
    lines.append('# Identification Strategy Recommendation')
    lines.append('')
    lines.append('## Brief Summary')
    lines.append('')
    if brief.get('question'):
        lines.append(f"- **Research question**: {brief['question']}")
    data = brief.get('data', {})
    if data.get('structure'):
        lines.append(f"- **Data structure**: {data['structure']}")
    if data.get('granularity'):
        lines.append(f"- **Granularity**: {data['granularity']}")
    if data.get('sample_size'):
        lines.append(f"- **Sample size**: {data['sample_size']}")
    if brief.get('identification_seed'):
        lines.append(f"- **User seed**: {brief['identification_seed']}")
    if brief.get('natural_experiment'):
        lines.append(f"- **Natural experiment**: {brief['natural_experiment']}")
    if brief.get('confounders'):
        lines.append(f"- **Identified threats**: {', '.join(brief['confounders'])}")
    lines.append('')

    lines.append(f'## Top {top_k} Recommendations')
    lines.append('')
    lines.append('| Rank | Strategy | Score | Why |')
    lines.append('|---|---|---|---|')
    for i, s in enumerate(strategies[:top_k], start=1):
        why = '; '.join(s.rationale[:2]) if s.rationale else '基础适用'
        if len(why) > 80:
            why = why[:77] + '…'
        lines.append(f'| {i} | **{s.chinese} ({s.name})** | {s.score:.0f} | {why} |')
    lines.append('')

    for i, s in enumerate(strategies[:top_k], start=1):
        lines.append(f'## #{i}: {s.chinese} ({s.name})')
        lines.append('')
        lines.append(f'**Score**: {s.score:.0f} / 100')
        lines.append('')
        if s.rationale:
            lines.append('**Rationale**:')
            for r in s.rationale:
                lines.append(f'- {r}')
            lines.append('')
        if s.statspai_funcs:
            lines.append('**StatsPAI calls**:')
            lines.append('```python')
            lines.append('import statspai as sp')
            for fn in s.statspai_funcs:
                lines.append(fn)
            lines.append('```')
            lines.append('')
        if s.robustness_must:
            lines.append('**Robustness checks (mandatory)**:')
            for r in s.robustness_must:
                lines.append(f'- [ ] {r}')
            lines.append('')
        if s.pitfalls:
            lines.append('**Common pitfalls**:')
            for p in s.pitfalls:
                # 用 ASCII (!) 替代 ⚠️ —— 后者在 Windows GBK 终端报
                # UnicodeEncodeError（CLI 实跑时发现）。Markdown 渲染仍清晰。
                lines.append(f'- (!) {p}')
            lines.append('')
        if s.references:
            lines.append('**Key references**:')
            for ref in s.references:
                lines.append(f'- {ref}')
            lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('## Next steps')
    lines.append('')
    lines.append('1. 看 #1 的 robustness checklist，加到你的 stage 4 必做项')
    lines.append('2. 跑 `python scripts/scaffold.py --strategy <chosen> --session <name>` 生成代码骨架')
    lines.append('3. 不确定时，**至少跑两个不同方法**对比（如 DiD + SCM），看是否一致')
    return '\n'.join(lines)


# ============ Main ============

def main() -> int:
    parser = argparse.ArgumentParser(description='Identification strategy selector for empirical research.')
    parser.add_argument('--brief', help='Path to research_brief.yaml (or JSON)')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--output', help='Write report to this file (Markdown)')
    parser.add_argument('--top', type=int, default=3, help='Number of top strategies to show (default 3)')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of Markdown')
    args = parser.parse_args()

    if args.interactive:
        brief = interactive_brief()
    elif args.brief:
        path = Path(args.brief)
        if not path.exists():
            print(f'[error] Brief file not found: {path}', file=sys.stderr)
            return 1
        brief = load_brief(path)
    else:
        parser.error('Must provide --brief or --interactive')
        return 2

    strategies = evaluate_strategies(brief)

    if args.json:
        out = {
            'brief': brief,
            'recommendations': [
                {
                    'name': s.name, 'chinese': s.chinese, 'score': s.score,
                    'rationale': s.rationale, 'references': s.references,
                    'statspai_funcs': s.statspai_funcs,
                    'robustness_must': s.robustness_must, 'pitfalls': s.pitfalls,
                }
                for s in strategies[:args.top]
            ],
        }
        text = json.dumps(out, ensure_ascii=False, indent=2)
    else:
        text = render_report(brief, strategies, top_k=args.top)

    # Windows GBK 终端不能渲染所有 Unicode（中文 OK，但 Emoji 不行）。
    # 先尝试正常打印；失败时 fallback 到 utf-8 + replace 错误字符。
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode('utf-8', errors='replace') + b'\n')

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding='utf-8')
        print(f'\n[ok] Written to: {out_path}', file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
