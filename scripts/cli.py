#!/usr/bin/env python3
"""
cli.py — econ-paper-studio 统一子命令入口

git 风格的子命令分发器：

  econ-studio init <name> --rq "..." --strategy DiD     (= session.py init)
  econ-studio identify --brief brief.yaml               (= identify_strategy.py)
  econ-studio scaffold --strategy DiD --session my-paper (= scaffold.py)
  econ-studio data-audit --csv panel.csv                (= data_audit.py)
  econ-studio verify --strategy DiD --analysis outputs/my-paper (= robustness_checks.py)
  econ-studio paper audit --paper draft.md              (= paper_pipeline.py)
  econ-studio skills plan --task full-paper             (= skills.py)
  econ-studio design-memo --brief brief.yaml            (= evidence_pipeline.py design-memo)
  econ-studio ledger init/add/audit                     (= evidence_pipeline.py ledger)
  econ-studio claim-audit --paper draft.md --ledger ledger.json
  econ-studio reviewer-gauntlet --paper draft.md --ledger ledger.json
  econ-studio doctor                                    (= doctor.py)
  econ-studio session list                              (= session.py list)
  econ-studio brainstorm                                (= 打开 RESEARCH_QUESTION.md)
  econ-studio workflow                                  (= 打开 WORKFLOW.md)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

SUBCOMMANDS = {
    'doctor':    SCRIPT_DIR / 'doctor.py',
    'identify':  SCRIPT_DIR / 'identify_strategy.py',
    'scaffold':  SCRIPT_DIR / 'scaffold.py',
    'data-audit': SCRIPT_DIR / 'data_audit.py',
    'verify':    SCRIPT_DIR / 'robustness_checks.py',
    'paper':     SCRIPT_DIR / 'paper_pipeline.py',
    'skills':    SCRIPT_DIR / 'skills.py',
    'design-memo': ('evidence_pipeline.py', 'design-memo'),
    'ledger':    ('evidence_pipeline.py', 'ledger'),
    'claim-audit': ('evidence_pipeline.py', 'claim-audit'),
    'reviewer-gauntlet': ('evidence_pipeline.py', 'reviewer-gauntlet'),
    'session':   SCRIPT_DIR / 'session.py',
    # init / add / list 等也通过 session 入口
    'init':      ('session.py', 'init'),
    'list':      ('session.py', 'list'),
    'show':      ('session.py', 'show'),
    'add':       ('session.py', 'add'),
    'promote':   ('session.py', 'promote'),
}

ALIASES = {
    'i': 'identify', 'identify-strategy': 'identify',
    's': 'session', 'sess': 'session',
    'sc': 'scaffold',
    'da': 'data-audit', 'data': 'data-audit', 'audit-data': 'data-audit',
    'v': 'verify', 'check': 'verify',
    'p': 'paper', 'write': 'paper',
    'sk': 'skills',
    'dm': 'design-memo',
    'claims': 'claim-audit',
    'reviewers': 'reviewer-gauntlet',
    'd': 'doctor',
    'b': 'brainstorm', 'q': 'brainstorm', 'rq': 'brainstorm',
    'w': 'workflow',
}


def banner() -> None:
    print('econ-paper-studio - empirical economics workflow CLI')
    print('=' * 60)
    print('Stage commands:')
    print('  doctor         Check local install and project health')
    print('  brainstorm     Open RESEARCH_QUESTION.md (stage 1)')
    print('  identify       Identify strategy (stage 2)')
    print('  scaffold       Generate code skeleton (stage 3)')
    print('  data-audit     Audit CSV keys, missingness, treatment variation, and clusters')
    print('  verify         Run static robustness/writing checks (stage 4)')
    print('  paper          Render outline or audit draft writing quality (stage 5)')
    print('  skills         Plan or audit upstream skills for agent use')
    print('  design-memo    Render identification contract from a brief')
    print('  ledger         Manage evidence ledger entries')
    print('  claim-audit    Map paper claims to ledger evidence')
    print('  reviewer-gauntlet  Run method/data/citation/writing/replication review')
    print('  session        Manage paper iterations and review history')
    print()
    print('Session shortcuts:')
    print('  init / list / show / add / promote')
    print()
    print('Examples:')
    print('  econ-studio doctor --json')
    print('  econ-studio brainstorm')
    print('  econ-studio identify --interactive')
    print('  econ-studio identify --brief brief.yaml')
    print('  econ-studio scaffold --strategy DiD --session my-paper --lang stata')
    print('  econ-studio data-audit --csv panel.csv --key city_id --key year --outcome y')
    print('  econ-studio verify --strategy DiD --analysis outputs/my-paper')
    print('  econ-studio paper outline --brief brief.yaml --output outline.md')
    print('  econ-studio paper audit --paper draft.md --fail-under 8')
    print('  econ-studio skills plan --task full-paper')
    print('  econ-studio design-memo --brief brief.yaml')
    print('  econ-studio ledger init --ledger evidence_ledger.json')
    print('  econ-studio claim-audit --paper draft.md --ledger evidence_ledger.json')
    print('  econ-studio reviewer-gauntlet --paper draft.md --ledger evidence_ledger.json')
    print('  econ-studio init my-paper --rq "..." --strategy DiD')
    print('  econ-studio list')
    print('  econ-studio show my-paper')
    print('  econ-studio add my-paper --version v1 --note "first draft"')
    print()
    print('Run `econ-studio <cmd> --help` for sub-script options.')


def open_doc(filename: str) -> int:
    target = PROJECT_ROOT / filename
    if not target.exists():
        print(f'[error] {filename} not found in project root', file=sys.stderr)
        return 1
    print(f'[info] {filename} location:')
    print(f'  {target}')
    print()
    print(target.read_text(encoding='utf-8'))
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        banner()
        return 0

    cmd = sys.argv[1]
    cmd = ALIASES.get(cmd, cmd)

    if cmd == 'brainstorm':
        return open_doc('RESEARCH_QUESTION.md')
    if cmd == 'workflow':
        return open_doc('WORKFLOW.md')

    if cmd not in SUBCOMMANDS:
        print(f'[error] Unknown subcommand: {cmd}', file=sys.stderr)
        print()
        banner()
        return 2

    target = SUBCOMMANDS[cmd]
    extra_args = sys.argv[2:]
    if isinstance(target, tuple):
        # session 子命令的快捷方式
        script_name, sub_cmd = target
        target_script = SCRIPT_DIR / script_name
        forwarded = [sys.executable, str(target_script), sub_cmd, *extra_args]
    else:
        forwarded = [sys.executable, str(target), *extra_args]

    proc = subprocess.run(forwarded, check=False)
    return proc.returncode


if __name__ == '__main__':
    sys.exit(main())
