#!/usr/bin/env python3
"""
cli.py — econ-paper-studio 统一子命令入口

git 风格的子命令分发器：

  econ-studio init <name> --rq "..." --strategy DiD     (= session.py init)
  econ-studio identify --brief brief.yaml               (= identify_strategy.py)
  econ-studio scaffold --strategy DiD --session my-paper (= scaffold.py)
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
    'identify':  SCRIPT_DIR / 'identify_strategy.py',
    'scaffold':  SCRIPT_DIR / 'scaffold.py',
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
    'b': 'brainstorm', 'q': 'brainstorm', 'rq': 'brainstorm',
    'w': 'workflow',
}


def banner() -> None:
    print('econ-paper-studio — empirical economics workflow CLI')
    print('=' * 60)
    print('Stage commands:')
    print('  brainstorm     Open RESEARCH_QUESTION.md (stage 1)')
    print('  identify       Identify strategy (stage 2)')
    print('  scaffold       Generate code skeleton (stage 3)')
    print('  session        Manage paper iterations (stage 5)')
    print()
    print('Session shortcuts:')
    print('  init / list / show / add / promote')
    print()
    print('Examples:')
    print('  econ-studio brainstorm')
    print('  econ-studio identify --interactive')
    print('  econ-studio identify --brief brief.yaml')
    print('  econ-studio scaffold --strategy DiD --session my-paper --lang stata')
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
