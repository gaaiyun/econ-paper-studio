# Examples

每个子目录是一个完整的实证案例，包含从研究问题到论文初稿的全流程产出。  
跑通其中任何一个都能验证 econ-paper-studio 工作流是否正常。

## 案例清单

| 案例 | 状态 | 方法 | 数据 | 适合学习什么 |
|---|---|---|---|---|
| `case-min-wage-did/` | 可跑 smoke | Staggered DiD (CS-DiD + Sun-Abraham) | 城市-年份面板示例 brief | 错时治疗 + 现代 DiD + HonestDiD 敏感性 |
| `case-rdd-college/` | 规划中 | Sharp RDD (CCT bandwidth) | 高考分数线断点 | 经典 RDD + bandwidth 选择 + manipulation test |
| `case-iv-export/` | 规划中 | IV (Bartik shift-share) | 中国出口数据 + 海外需求 | 弱工具变量诊断 + 当代 IV 谨慎做法 |

## 通用约定

每个 case 都包含：

```
case-xxx/
├── RQ.md                    # 研究问题（stage 1 产出）
├── identify_strategy.md     # 识别策略（stage 2 产出）
├── do/                      # Stata do-file（stage 3 产出）
├── R/                       # R 脚本（stage 3 产出）
├── tables/                  # 主结果表
├── figures/                 # 主结果图
├── robustness/              # 稳健性检验（stage 4 产出）
│   ├── CHECKLIST.md
│   └── ...
└── paper/                   # 论文初稿（stage 5 产出）
    └── v1/
        ├── main.tex
        └── tables.tex
```

## 跑通顺序建议

1. 先看 `case-min-wage-did/`（最常见的 staggered DiD，国内研究主流）
2. 再看 `case-rdd-college/`（清晰的 cutoff，学习 RDD bandwidth 选择）
3. 最后 `case-iv-export/`（IV 是最难做对的方法，看这个学谨慎）

每个 case 的 README 里有：
- 该案例预期能教会用户什么
- 完整命令序列（可直接复制粘贴）
- 预期的 verify 报告分数
- 学术参考文献（如果想做严肃研究，先读这些）

## 状态

当前已提供 `case-min-wage-did/research_brief.yaml`，可直接用于 `identify` smoke test。其余案例仍是后续扩展计划。
