# Anti-AI Phrases — 论文写作中要去掉的"AI 味"短语

> 这些短语在 ChatGPT/Claude 生成的学术文本中出现频率远高于人类写作。  
> 不是说它们错——是说它们**过度使用**会让 reviewer 一眼看出是 AI 写的。

## 高频开篇/过渡词（中英对照）

### 英文

| AI 高频 | 替代写法 |
|---|---|
| **It is worth noting that** ... | (直接说事，不需要 hedging) |
| **It is important to note that** ... | (同上) |
| **In addition / Furthermore / Moreover** | (用空行分段或 "Also") |
| **Importantly** ... | (如果真的重要，让事实自己说) |
| **In particular** | (用 "specifically" 或直接举例) |
| **Notably** | 删除 |
| **Interestingly** | 删除（让结果自己 interesting） |
| **As mentioned earlier** | (除非真的要回指，否则删) |
| **In conclusion** | "We conclude that..." 或直接说结论 |
| **In summary** | (同上) |
| **It can be observed that** ... | "We observe..." 或 "Figure X shows..." |
| **Plays a crucial role in** ... | "[X] determines [Y]" / "[X] drives [Y]" |
| **Provides valuable insights** | 删除（什么都没说） |
| **A wide range of** ... | "many" / "various" |
| **Significantly enhances** | (改成具体数字) |
| **Cutting-edge** / **state-of-the-art** | (除非和文献争议直接相关) |
| **Robustly demonstrates** | (单独用 "demonstrates" 或具体说怎么稳健) |
| **Comprehensive analysis** | (一般是空话) |
| **In-depth examination** | 删除 |
| **Holistic approach** | 删除 |
| **Leverage** (作动词) | "use" |
| **Utilize** | "use" |
| **Unprecedented** | (除非真的史无前例，否则别用) |

### 中文（中文论文里的 AI 套路）

| AI 高频 | 替代写法 |
|---|---|
| **值得注意的是** | (直接说) |
| **此外/同时/另外/更重要的是** | (用段落分隔) |
| **不可否认** | 删除 |
| **众所周知** | 删除 |
| **综上所述** | "本文得出三点结论：..." |
| **从某种意义上来说** | 删除 |
| **在一定程度上** | (具体到什么程度) |
| **具有重要的现实意义** | (说什么意义) |
| **本文的主要贡献在于** | "我们贡献了..." |
| **本文系统地/全面地分析了** | "本文分析了" |
| **深入探讨** | "分析" |
| **加以深入研究** | "研究" |
| **进一步丰富了 X 的研究** | (删除，让结果自己说) |
| **本文的研究结果具有重要的政策启示** | (说明是什么启示) |

## 句法 / 结构性 AI 套路

### 1. The "Triple Parallel" 三件套排比

**AI 写法**:
> This paper makes three contributions. First, we ... Second, we ... Third, we ...

**问题**: 大部分论文只有一个核心贡献。三件套式排比是 AI 自动产生 "完整感" 的套路。

**正确**:
> Our central contribution is [ONE thing, stated concretely]. This builds on [related work] but differs in [specific way].

### 2. The "On the One Hand / On the Other Hand" 套路

**AI 写法**:
> On the one hand, [argument A]. On the other hand, [argument B].

**问题**: 真正的论证很少是简单 binary。

**正确**:
> While [argument A] is supported by [evidence], it conflicts with [argument B], because [mechanism].

### 3. The "Define Then Discuss" 套路

**AI 写法**:
> Difference-in-differences (DiD) is a quasi-experimental approach widely used in causal inference. It compares ...

**问题**: 你的读者是经济学家，不需要从定义教起。

**正确**:
> We follow [author year] and use a CS-DiD design to recover staggered treatment effects.

### 4. The "List Without Reasoning" 套路

**AI 写法**:
> We use the following methods: 1. OLS regression; 2. Robust standard errors; 3. Fixed effects; 4. Clustering.

**问题**: 没说为什么。

**正确**:
> We estimate by OLS with two-way clustered SE at the [unit] and [year] levels. Two-way clustering is necessary because [shock structure]. (Cite Cameron, Gelbach & Miller 2011.)

## "AI 味" 自检清单

### 在你交稿前，对每段做这个检查：

- [ ] 有没有 "It is worth noting" / "Furthermore" / "Importantly" / "Notably" 等填充词？删掉。
- [ ] 有没有"三件套"排比？真的是三件吗，还是凑出来的？
- [ ] 第一句话是不是定义性的？读者已经懂这个概念。
- [ ] 有没有 "This paper makes a comprehensive contribution to ..." 这种空话？删掉。
- [ ] 段落开头有没有 "In addition / Moreover" 等过渡词？多数情况不需要。
- [ ] 有没有泛化的形容词："robust", "comprehensive", "in-depth"，不带具体数字？

### 长句子拆解

AI 倾向写长句，人倾向写短句。如果一段话只有 1-2 个长句，重写成 3-5 个短句。

**AI**:
> This paper investigates the causal effect of minimum wage on employment in China by leveraging a difference-in-differences design exploiting the staggered rollout of provincial minimum wage adjustments from 2010 to 2020, with results suggesting a negative but statistically insignificant effect on overall employment but a robust negative effect on the employment of low-skilled workers.

**人**:
> We study how minimum wage affects employment in China. We use a staggered DiD on provincial wage adjustments, 2010-2020. The effect on overall employment is negative but small (-1.2%, SE=1.0). The effect on low-skilled workers is larger (-3.8%, SE=1.4) and robust to alternative specifications.

## 不是所有"AI 味"都要删

有些短语在学术写作中是必要的：
- ✅ "We estimate the following equation:" — 标准句式
- ✅ "The dependent variable is ..." — 定义需要
- ✅ "Following [author year], we ..." — 文献承接
- ✅ "Robustness to alternative specifications is reported in Table X." — 引用稳健性

**删的是套路化的填充，不是必要的学术句式。**

## 自动化检查（可以加到 verify 阶段）

```python
# 简单实现：扫描文本，匹配高频词，输出 warning
import re

ANTI_AI_PATTERNS_EN = [
    r'\bIt is worth noting that\b',
    r'\bIt is important to note that\b',
    r'\bIn addition,\s*$',  # 段首的 In addition
    r'\bFurthermore,\s*$',
    r'\bMoreover,\s*$',
    r'\bImportantly,\s*$',
    r'\bNotably,\s*$',
    r'\bInterestingly,\s*$',
    r'\bIn conclusion\b',
    r'\bIn summary\b',
    r'\bplays? an? (crucial|important|significant) role\b',
    r'\bprovides? valuable insights?\b',
    r'\bcomprehensive analysis\b',
    r'\bin-depth (examination|analysis)\b',
    r'\bholistic approach\b',
]

ANTI_AI_PATTERNS_CN = [
    r'值得注意的是',
    r'^此外，',
    r'^更重要的是，',
    r'综上所述',
    r'从某种意义上来说',
    r'本文的研究结果具有重要的政策启示',
    r'进一步丰富了.*研究',
]

# 用法：scan(text) → 输出每行哪个模式被触发
```

## 必读

- Pinker, Steven. *The Sense of Style: The Thinking Person's Guide to Writing in the 21st Century*.
- Strunk & White, *The Elements of Style*.
- McCloskey, *Economical Writing*.
- Cochrane, John. ["Writing tips for PhD students"](https://www.johnhcochrane.com/research-all/writing-tips-for-phd-students).

每次写完一段，问自己一个问题：**「如果我把这段话给一个真人助理改，他会不会保留每个字？」** 不会保留的，就是 AI 味。
