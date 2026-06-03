# Testing Guide

## Run

```bash
pip install -e ".[dev]"     # 装 pytest + pytest-cov + ruff
pytest tests/
```

111 个测试，约数秒跑完。无网络 / 无外部依赖（Stata / R / LLM 全 mock 或不需要）。

## 覆盖的模块

| 测试文件 | 目标模块 | 测试数 | 覆盖的能力 |
|---|---|---|---|
| `tests/test_session.py` | `scripts/session.py` | 27 | session 生命周期：init / list / show / add / add-review / promote |
| `tests/test_identify_strategy.py` | `scripts/identify_strategy.py` | 30 | 6 个识别策略（DiD / RDD / IV / SCM / Matching / DML）的决策树打分规则 + 报告渲染 |
| `tests/test_scaffold.py` | `scripts/scaffold.py` | 20 | Stata / R 模板字典完整性 + 模板内容质量（必含 reghdfe / event study / rdrobust 等）+ CLI 端到端 |
| `tests/test_cli.py` | `scripts/cli.py` | 25 | 子命令分发 / 别名解析 / banner / open_doc + subprocess 端到端 |
| `tests/test_doctor.py` | `scripts/doctor.py` | 2 | 本地环境 / 关键文件 / 依赖健康检查 |
| `tests/test_robustness_checks.py` | `scripts/robustness_checks.py` | 7 | Stage 4 静态 verifier / AI 味扫描 / 因果过度声称 / 引用 placeholder / fail-under |

## 测试分类

### 单元测试

直接调函数，断言返回值或抛错：

```python
from session import cmd_init
code = cmd_init(args)
assert code == 0
```

### 决策树测试（identify_strategy）

用最小化 brief 构造每条规则触发条件，断言分数下界 / 排序结果：

```python
def test_did_panel_data_scored_higher():
    panel = evaluate_strategies({"data": {"structure": "panel"}})
    cross = evaluate_strategies({"data": {"structure": "cross_section"}})
    did_panel = next(s for s in panel if s.name == "DiD")
    did_cross = next(s for s in cross if s.name == "DiD")
    assert did_panel.score > did_cross.score
```

每个策略至少 3 条规则被测：

- **DiD**: panel boost、自然实验关键词、中文 seed
- **RDD**: cutoff 关键词、中文断点、test/分数情景
- **IV**: seed boost、反向因果加分、候选工具变量加分
- **SCM**: panel + 颗粒度叠加加分、中文合成控制
- **Matching**: 全局降权检查、不变负数
- **DML**: ML 关键词、高维控制变量加分

### CLI 端到端测试

用 `subprocess.run([sys.executable, cli.py, ...])` 启子进程，验证：

- exit code
- stdout / stderr 内容
- 真实写出的文件存在 + 内容正确

`tests/test_scaffold.py::test_cli_did_stata_creates_files` 跑完后会在
`tmp_path/test-paper/do/` 下生成全部 7 个 `.do` 文件，并验证 `00_master.do`
包含 session 名替换。

## 实跑捕获的 bug（v1 修复）

| Bug | 位置 | 表现 | 修法 |
|---|---|---|---|
| `⚠️` emoji 在 Windows GBK 终端 UnicodeEncodeError | `identify_strategy.py:420` | `python cli.py identify --brief ...` 输出报告时直接崩 | 改用 ASCII `(!)` + `print(text)` 加 try/except fallback 到 utf-8 |

## CI 友好

所有测试：

- 不联网（无 mock 也无 fixture 网络调用）
- 不需要 Stata / R / Python ML 库（模板只验证字符串内容，不真跑回归）
- 不需要 LLM API key
- 用 `tmp_path` fixture 隔离文件 IO
- 用 `monkeypatch` / `patch.object(sys, "argv", ...)` 切 CLI 入参

GitHub Actions 配置参考：

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.10" }
- run: pip install -e ".[dev]"
- run: pytest tests/ --cov=scripts --cov-report=term-missing
```

## 已知 gap（暂未覆盖）

- `interactive_brief()` 用 `input()` 收集 brief，需要 mock stdin —— 实际跑过
  人工验证过，但没写 pytest（mock stdin 多行交互会让测试很难读）。
- `R_TEMPLATES["RDD"]` 还没在 v1 实现，scaffold 跑 RDD + R 会报 "No template"。
  测试通过 `test_cli_unknown_strategy_fails` 间接覆盖了"未实现策略"的报错路径。

要补这两块：

1. 用 `monkeypatch.setattr("builtins.input", lambda _: "panel")` 串模拟一次完
   整的 interactive_brief 会话。
2. 加 `R_TEMPLATES["RDD"]` 真模板，然后加个对应的 CLI 测试。
