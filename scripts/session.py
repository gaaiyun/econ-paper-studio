#!/usr/bin/env python3
"""
session.py — 阶段 5 工具化：session 管理器

参考自 design-image-studio/scripts/session.py，针对论文项目场景。

子命令:
  init <name> --rq "..." --strategy DiD       创建新论文 session
  list                                         列出所有 sessions
  show <name>                                  显示详情和历史
  add <name> --version v1 --note "first draft" 记录一次迭代
  add-review <name> --version r1 --letter ... 记录审稿意见
  promote <name> --version v2                  标记为终稿
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_BASE = Path("outputs")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='econ-paper-studio session manager')
    p.add_argument('--base-dir', default=str(DEFAULT_BASE))
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('init', help='Create a new paper session')
    sp.add_argument('name')
    sp.add_argument('--rq', '--research-question', required=True, dest='rq')
    sp.add_argument('--strategy', default='unsure')
    sp.add_argument('--target-journal', default='')
    sp.add_argument('--data-source', default='')

    sub.add_parser('list', help='List all sessions')

    sp = sub.add_parser('show', help='Show session details')
    sp.add_argument('name')

    sp = sub.add_parser('add', help='Record one paper iteration')
    sp.add_argument('name')
    sp.add_argument('--version', required=True)
    sp.add_argument('--paper', help='Path to paper draft')
    sp.add_argument('--note', required=True)
    sp.add_argument('--score', type=float, default=None,
                    help='Optional verify score 0-10')

    sp = sub.add_parser('add-review', help='Record a referee letter')
    sp.add_argument('name')
    sp.add_argument('--version', required=True, help='e.g. r1, r2')
    sp.add_argument('--letter', required=True, help='Path to referee letter')
    sp.add_argument('--decision', default='', help='accept/minor/major/reject')

    sp = sub.add_parser('promote', help='Mark a version as final')
    sp.add_argument('name')
    sp.add_argument('--version', required=True)

    return p.parse_args()


def session_dir(base: Path, name: str) -> Path:
    return base / name


def manifest_path(s_dir: Path) -> Path:
    return s_dir / 'manifest.json'


def changelog_path(s_dir: Path) -> Path:
    return s_dir / 'CHANGELOG.md'


def cmd_init(args) -> int:
    s_dir = session_dir(Path(args.base_dir), args.name)
    if s_dir.exists():
        print(f'[error] Session already exists: {s_dir}', file=sys.stderr)
        return 1
    for sub in ('data', 'do', 'R', 'tables', 'figures', 'robustness',
                'paper', 'paper/v1', 'referee_response'):
        (s_dir / sub).mkdir(parents=True, exist_ok=True)

    manifest = {
        'name': args.name,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'research_question': args.rq,
        'strategy': args.strategy,
        'target_journal': args.target_journal,
        'data_source': args.data_source,
        'iterations': [],
        'reviews': [],
        'final_version': None,
    }
    manifest_path(s_dir).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    cl = [
        f'# Session: {args.name}',
        '',
        f'- **Created**: {manifest["created_at"]}',
        f'- **RQ**: {args.rq}',
        f'- **Strategy**: `{args.strategy}`',
    ]
    if args.target_journal:
        cl.append(f'- **Target Journal**: {args.target_journal}')
    if args.data_source:
        cl.append(f'- **Data**: {args.data_source}')
    cl += ['', '## Paper Iterations', '', '_(none yet)_', '',
           '## Referee Reviews', '', '_(none yet)_', '']
    changelog_path(s_dir).write_text('\n'.join(cl), encoding='utf-8')

    print(f'[ok] Session created: {s_dir}')
    print(f'     manifest:  {manifest_path(s_dir)}')
    print(f'     changelog: {changelog_path(s_dir)}')
    print()
    print('Next:')
    print(f'  1. python scripts/identify_strategy.py --interactive')
    print(f'  2. python scripts/scaffold.py --strategy <chosen> --session {args.name}')
    print(f'  3. Develop paper draft in {s_dir}/paper/v1/')
    return 0


def cmd_list(args) -> int:
    base = Path(args.base_dir)
    if not base.exists():
        print(f'(no sessions: {base} does not exist)')
        return 0
    sessions = []
    for sub in base.iterdir():
        m = manifest_path(sub)
        if m.exists():
            try:
                meta = json.loads(m.read_text(encoding='utf-8'))
                sessions.append((sub.name, meta))
            except json.JSONDecodeError:
                pass
    if not sessions:
        print(f'(no valid sessions under {base})')
        return 0
    print(f'{"NAME":<30} {"STRATEGY":<10} {"VERS":<5} {"REVS":<5} {"FINAL":<8} JOURNAL')
    print('-' * 100)
    for name, meta in sorted(sessions, key=lambda kv: kv[1].get('created_at', '')):
        n_iter = len(meta.get('iterations', []))
        n_rev = len(meta.get('reviews', []))
        final = meta.get('final_version') or '—'
        journal = (meta.get('target_journal') or '').strip()[:40]
        print(f'{name:<30} {meta.get("strategy", "?"):<10} {n_iter:<5} {n_rev:<5} {final:<8} {journal}')
    return 0


def cmd_show(args) -> int:
    s_dir = session_dir(Path(args.base_dir), args.name)
    m = manifest_path(s_dir)
    if not m.exists():
        print(f'[error] Session not found: {s_dir}', file=sys.stderr)
        return 1
    meta = json.loads(m.read_text(encoding='utf-8'))
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print()
    cl = changelog_path(s_dir)
    if cl.exists():
        print('=' * 70)
        print('CHANGELOG.md')
        print('=' * 70)
        print(cl.read_text(encoding='utf-8'))
    return 0


def cmd_add(args) -> int:
    s_dir = session_dir(Path(args.base_dir), args.name)
    m_path = manifest_path(s_dir)
    if not m_path.exists():
        print(f'[error] Session not found: {s_dir}', file=sys.stderr)
        return 1
    meta = json.loads(m_path.read_text(encoding='utf-8'))

    iter_record = {
        'version': args.version,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'note': args.note,
        'paper': args.paper,
        'score': args.score,
    }
    meta.setdefault('iterations', []).append(iter_record)
    m_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    cl_path = changelog_path(s_dir)
    cl = cl_path.read_text(encoding='utf-8') if cl_path.exists() else ''
    cl = cl.replace('## Paper Iterations\n\n_(none yet)_\n', '## Paper Iterations\n')
    new = [f'\n### {args.version} ({iter_record["timestamp"]})', '',
           f'- **Note**: {args.note}']
    if args.paper:
        new.append(f'- **Paper**: `{args.paper}`')
    if args.score is not None:
        new.append(f'- **Score**: **{args.score} / 10**')
    new.append('')
    cl_path.write_text(cl + '\n'.join(new), encoding='utf-8')
    print(f'[ok] Iteration {args.version} recorded')
    return 0


def cmd_add_review(args) -> int:
    s_dir = session_dir(Path(args.base_dir), args.name)
    m_path = manifest_path(s_dir)
    if not m_path.exists():
        print(f'[error] Session not found: {s_dir}', file=sys.stderr)
        return 1
    meta = json.loads(m_path.read_text(encoding='utf-8'))

    review_record = {
        'version': args.version,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'letter': args.letter,
        'decision': args.decision,
    }
    meta.setdefault('reviews', []).append(review_record)
    m_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    cl_path = changelog_path(s_dir)
    cl = cl_path.read_text(encoding='utf-8') if cl_path.exists() else ''
    cl = cl.replace('## Referee Reviews\n\n_(none yet)_\n', '## Referee Reviews\n')
    new = [f'\n### {args.version} ({review_record["timestamp"]})', '',
           f'- **Letter**: `{args.letter}`',
           f'- **Decision**: {args.decision or "(pending)"}', '']
    cl_path.write_text(cl + '\n'.join(new), encoding='utf-8')
    print(f'[ok] Review {args.version} recorded')
    return 0


def cmd_promote(args) -> int:
    s_dir = session_dir(Path(args.base_dir), args.name)
    m_path = manifest_path(s_dir)
    if not m_path.exists():
        print(f'[error] Session not found: {s_dir}', file=sys.stderr)
        return 1
    meta = json.loads(m_path.read_text(encoding='utf-8'))
    target = next((it for it in meta.get('iterations', []) if it['version'] == args.version), None)
    if not target:
        print(f'[error] Version {args.version} not found', file=sys.stderr)
        return 1

    if target.get('paper'):
        src = Path(target['paper'])
        if src.exists():
            dst = s_dir / 'paper' / 'final.docx'
            shutil.copy2(src, dst)
            print(f'[ok] Copied {src} -> {dst}')

    meta['final_version'] = args.version
    meta['promoted_at'] = datetime.now().isoformat(timespec='seconds')
    m_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

    cl_path = changelog_path(s_dir)
    if cl_path.exists():
        cl = cl_path.read_text(encoding='utf-8')
        promo = f'\n### **PROMOTED**: {args.version} ({meta["promoted_at"]})\n\n> Final version. See `paper/final.docx`.\n'
        cl_path.write_text(cl + promo, encoding='utf-8')
    print(f'[ok] {args.version} promoted as final')
    return 0


def main() -> int:
    args = parse_args()
    handlers = {
        'init': cmd_init, 'list': cmd_list, 'show': cmd_show,
        'add': cmd_add, 'add-review': cmd_add_review, 'promote': cmd_promote,
    }
    return handlers[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
