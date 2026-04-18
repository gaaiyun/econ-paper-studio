# DiD（双重差分）方法详解

> 实证因果推断里最常用的方法。也是最容易做错的方法之一——错时治疗下的 TWFE 负权重问题在 2018 年后才被广泛认识。

## 核心思想

比较「治疗组从前期到后期的变化」与「控制组从前期到后期的变化」之差，即：

$$
\hat{\beta}^{DiD} = (\bar{Y}^{T}_{post} - \bar{Y}^{T}_{pre}) - (\bar{Y}^{C}_{post} - \bar{Y}^{C}_{pre})
$$

通过两次差分消除：
1. 治疗组与控制组之间的固定差异（unit fixed effects）
2. 影响所有人的共同时间趋势（time fixed effects）

## 识别假设

**核心假设：平行趋势**（Parallel Trends Assumption）

> 如果治疗组没有接受治疗，它的 trajectory 应该和控制组平行。

**这个假设无法直接检验**——只能通过 pre-treatment period 的对比来「support」它。

## 何时用 DiD

✅ 适合：
- 有 panel 数据（多个 unit × 多个 time period）
- 治疗在某个 time point 引入（cross-section 之间有差异）
- 政策冲击 / 自然实验外生

❌ 不适合：
- 只有 cross-section（没有 pre-period）→ 用 RDD / IV / Matching
- 治疗几乎所有 unit 同时接受 → 没有控制组
- 治疗与未观测变量相关（confounders）→ 平行趋势可能违反

## 现代 DiD 全景图

| 场景 | 推荐方法 | 警示 |
|---|---|---|
| **2×2 简单 DiD**（一个治疗组 + 一个控制组 + 一个时间冲击） | TWFE OK | 经典案例，没坑 |
| **多组同期治疗**（K 个治疗组在同一年接受治疗） | TWFE OK | 注意 cluster SE |
| **错时治疗**（不同 unit 在不同时间接受治疗） | ❌ 标准 TWFE → 用 Callaway-Sant'Anna / Sun-Abraham / BJS | TWFE 会出现负权重，结果不可信 |
| **连续治疗强度**（不是 0/1，而是连续 dose） | Callaway, Goodman-Bacon, Sant'Anna (2024) 连续 DiD | 新方法，2024 年才发表 |
| **治疗可逆**（unit 接受了又退出） | de Chaisemartin & D'Haultfœuille | 极少见但要注意 |

## StatsPAI 调用对照

```python
import statspai as sp

# 自动 dispatch（推荐）
result = sp.did(
    data=df, y='outcome', t='post', g='treat',
    id_var='id', time_var='year', method='auto'
)

# CS-DiD（错时治疗推荐）
cs = sp.callaway_santanna(
    data=df, y='outcome',
    g='first_treat_year',  # 第一次接受治疗的年份，未治疗为 0 或 NaN
    t='year', id='id',
    control_group='notyettreated',  # 或 'nevertreated'
    method='dripw',  # doubly robust IPW
)
cs.summary()
cs.plot(type='dynamic')

# Sun-Abraham
sa = sp.sun_abraham(data=df, y='outcome', cohort='first_treat_year',
                    period='year', id='id')

# Goodman-Bacon 分解（诊断 TWFE 是否有负权重问题）
bd = sp.bacon_decomposition(data=df, y='outcome', t='post', g='treat',
                            id='id', time='year')
print(bd.summary())  # 如果 'always_treated' or 'switching' 部分占比大，说明有问题

# HonestDiD 敏感性分析
sens = sp.honest_did(att=cs, periods=[1, 2, 3], M_vec=[0.5, 1.0, 1.5, 2.0])
```

## 必做稳健性检验

> 没做这些就交付 = 给 referee 留把柄。

### 1. 平行趋势（事件研究图）

跑事件研究：
```python
es = sp.event_study(data=df, y='outcome',
                    event_time='years_from_treatment',
                    leads=5, lags=5)
es.plot()  # pre-period 系数应在 0 附近，没有显著趋势
```

**关键看**：
- `leads_-1`、`leads_-2` 等 pre-period 系数是否 95% CI 跨过 0
- pre-period 系数是否有显著的趋势（不是要它们等于 0，而是要它们 *平行*）

### 2. Goodman-Bacon 分解

只在错时治疗时需要。看 always-treated / never-treated / switching 部分各占多少权重。如果 switching 部分（用「先治疗的」做「后治疗的」的对照）占比 > 30%，就要严重警惕——它会引入负权重。

### 3. HonestDiD 敏感性

由 Rambachan & Roth (2023) 提出。允许平行趋势小幅违反，看你的 ATT 在多大的 pre-trend slope 下还显著。

### 4. 安慰剂检验

- **虚假治疗时间**：把治疗时间提前 2-3 年。如果系数仍显著 → 有问题
- **虚假治疗组**：随机选一些没接受治疗的 unit 标为「治疗组」。如果系数仍显著 → 有问题

### 5. 替代规范

- 不同 cluster 层级（个人 / 公司 / 行业 / 地区）
- 不同 control set（裸模型 vs 全控制 vs 加 unit-time interactions）
- 不同 sample 切法（去掉 outliers / 去掉特定子样本）

## 常见 pitfall

⚠️ **误用 TWFE 处理错时治疗**：见上文。2026 年的 referee 看到 staggered DiD 没用 CS/SA/BJS 几乎肯定 reject。

⚠️ **Cluster SE 选错层级**：政策在省级实施，但你 cluster 在个人层 → SE 严重低估。**Cluster 应在 treatment level**。

⚠️ **平行趋势检验通过 = 假设满足？不**。Roth (2022 AERI) 证明了：在 pre-period 通过 t-test 的样本下，post-treatment 偏倚反而更大。建议配合 HonestDiD 使用。

⚠️ **多重比较未校正**：跑了 10 个 outcome / 10 个 subsample，至少有一个 p<0.05 是巧合。Bonferroni 或 Romano-Wolf 校正必做。

⚠️ **不报 `g.` （或 R 的 `i.`）等基础 spec**：直接上 `reghdfe` + 炫技 fixed effects 之前，先报最简单的 2×2 DiD，让 referee 能 sanity check。

## 必读文献

| 论文 | 一句话总结 |
|---|---|
| Bertrand, Duflo & Mullainathan (2004 QJE) | 不 cluster SE 会让 false positive 从 5% 飙到 45% |
| Callaway & Sant'Anna (2021 JoE) | 错时治疗下，doubly robust 估计比 TWFE 更稳，提供 CS estimator |
| Sun & Abraham (2021 JoE) | 错时治疗下，event study 系数会被其他 cohort 污染，提出 SA estimator |
| Borusyak, Jaravel & Spiess (2024 RES) | 提出 imputation estimator (BJS)，效率最高 |
| Goodman-Bacon (2021 JoE) | 把 TWFE 系数分解，证明可能有负权重 |
| Rambachan & Roth (2023 RES) | HonestDiD，平行趋势敏感性 |
| Roth (2022 AERI) | "Pre-test with caution"，平行趋势检验本身有问题 |

## 经典论文（DiD 的"模板"实例）

- **Card & Krueger (1994 AER)**: 最经典，最低工资对就业。新泽西 vs 宾夕法尼亚边境。
- **Acemoglu, Naidu, Restrepo & Robinson (2019 JPE)**: 民主对经济增长。staggered，CS-DiD。
- **Lu & Yu (2015 AEJ Applied)**: 中国 WTO 入世对 markup 的影响。连续 DiD。
- **Almond, Hoynes & Schanzenbach (2011 RES)**: 食品券对儿童健康。多 outcome 校正。

## 写作模板

```markdown
## Identification Strategy

We exploit the staggered rollout of [policy] across [units] from [year_start] to [year_end]
to identify the causal effect on [outcome]. Following Callaway and Sant'Anna (2021), we
estimate group-time average treatment effects using the not-yet-treated as the control group.

The key identifying assumption is parallel trends: in the absence of [policy], outcomes in
treated and control units would have evolved similarly. We assess the credibility of this
assumption in three ways:

1. We plot event-study estimates (Figure 2) to test for differential pre-trends.
2. We apply HonestDiD (Rambachan and Roth 2023) to bound the bias from any modest
   pre-trend violation.
3. We run placebo tests with synthetic treatment timing.

[继续...]
```
