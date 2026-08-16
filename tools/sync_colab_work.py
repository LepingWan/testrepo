#!/usr/bin/env python3
"""Sync the Colab Drive work directory into this Git repo.

Run from the repo root, either in Colab or on a machine where Google Drive
is mounted locally. The default source is the Colab Drive path used by this
project:

    /content/drive/MyDrive/panini-course-project-work

The destination defaults to:

    ./panini-course-project-work

The script copies durable project outputs, including cache JSONL files,
submission files, figures, environment files, RUNME, and student_code. It avoids
notebook checkpoints and Python cache files. JSONL files are copied in a way
that drops an incomplete final line if a long-running Colab process is appending
while the sync is happening.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_SOURCE = Path('/content/drive/MyDrive/panini-course-project-work')
DEFAULT_DEST = Path('panini-course-project-work')
EXCLUDE_DIRS = {
    '.ipynb_checkpoints',
    '__pycache__',
    '.git',
}
EXCLUDE_PATTERNS = (
    '*.pyc',
    '*.pyo',
    '*.tmp',
    '*.temp',
    '*.partial',
    '*.lock',
    '.DS_Store',
)
GITHUB_WARN_BYTES = 90 * 1024 * 1024
GITHUB_HARD_LIMIT_BYTES = 100 * 1024 * 1024


def should_exclude(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDE_PATTERNS)


def iter_files(source: Path):
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        dirs[:] = [name for name in dirs if not should_exclude(root_path / name)]
        for name in files:
            path = root_path / name
            if not should_exclude(path):
                yield path


def copy_jsonl_safely(src: Path, dst: Path) -> tuple[int, int]:
    """Copy JSONL while avoiding a partially-written trailing row.

    Returns (lines_written, invalid_lines_skipped). Invalid non-empty lines are
    skipped in the destination snapshot so the committed file remains parseable.
    The source file is never modified.
    """
    data = src.read_bytes()
    if data and not data.endswith(b'\n'):
        data = data.rsplit(b'\n', 1)[0] + b'\n' if b'\n' in data else b''

    lines_written = 0
    invalid = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open('wb') as handle:
        for raw_line in data.splitlines(keepends=True):
            line = raw_line.strip()
            if not line:
                continue
            try:
                json.loads(line.decode('utf-8'))
            except Exception:
                invalid += 1
                continue
            handle.write(raw_line if raw_line.endswith(b'\n') else raw_line + b'\n')
            lines_written += 1
    return lines_written, invalid


def copy_one(src: Path, dst: Path, *, dry_run: bool) -> dict:
    size = src.stat().st_size
    info = {'source': str(src), 'dest': str(dst), 'bytes': size, 'jsonl_lines': None, 'invalid_jsonl': 0}
    if dry_run:
        return info

    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + '.syncing')
    if src.suffix == '.jsonl':
        lines, invalid = copy_jsonl_safely(src, tmp)
        info['jsonl_lines'] = lines
        info['invalid_jsonl'] = invalid
    else:
        shutil.copy2(src, tmp)
    tmp.replace(dst)
    return info


def remove_stale_files(dest: Path, expected: set[Path], *, dry_run: bool) -> list[Path]:
    stale = []
    if not dest.exists():
        return stale
    for path in dest.rglob('*'):
        if path.is_file() and path not in expected and path.name != 'README.md':
            stale.append(path)
    if not dry_run:
        for path in stale:
            path.unlink()
        for path in sorted(dest.rglob('*'), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return stale


def run_git(args: list[str], *, cwd: Path) -> None:
    print('+ git ' + ' '.join(args), flush=True)
    subprocess.run(['git', *args], cwd=cwd, check=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--dest', type=Path, default=DEFAULT_DEST)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--keep-stale', action='store_true', help='Do not remove files that disappeared from source.')
    parser.add_argument('--commit', action='store_true', help='Commit copied files after sync.')
    parser.add_argument('--push', action='store_true', help='Push after committing. Implies --commit.')
    parser.add_argument('--message', default='Sync Colab work outputs')
    args = parser.parse_args(argv)

    repo = Path.cwd().resolve()
    source = args.source.expanduser().resolve()
    dest = (repo / args.dest).resolve() if not args.dest.is_absolute() else args.dest.resolve()

    if not source.exists():
        print(f'ERROR: source does not exist: {source}', file=sys.stderr)
        print('Run this in Colab after mounting Drive, or pass --source to a local Google Drive path.', file=sys.stderr)
        return 2
    if not source.is_dir():
        print(f'ERROR: source is not a directory: {source}', file=sys.stderr)
        return 2
    if repo not in dest.parents and dest != repo:
        print(f'ERROR: destination must be inside the current repo: {dest}', file=sys.stderr)
        return 2

    files = list(iter_files(source))
    expected = {dest / path.relative_to(source) for path in files}
    total_bytes = 0
    large_files = []
    copied = []

    print(f'source: {source}')
    print(f'dest:   {dest}')
    print(f'files:  {len(files)}')

    for src in files:
        rel = src.relative_to(source)
        dst = dest / rel
        info = copy_one(src, dst, dry_run=args.dry_run)
        copied.append(info)
        total_bytes += info['bytes']
        if info['bytes'] >= GITHUB_WARN_BYTES:
            large_files.append((rel, info['bytes']))
        line_note = ''
        if info['jsonl_lines'] is not None:
            line_note = f" jsonl_lines={info['jsonl_lines']} invalid_skipped={info['invalid_jsonl']}"
        print(f"copied: {rel} bytes={info['bytes']}{line_note}")

    stale = [] if args.keep_stale else remove_stale_files(dest, expected, dry_run=args.dry_run)
    for path in stale:
        print(f'removed stale: {path.relative_to(dest)}')

    print(f'total copied bytes: {total_bytes}')
    if large_files:
        print('WARNING: large files near or above GitHub file limits:')
        for rel, size in large_files:
            marker = 'HARD_LIMIT' if size >= GITHUB_HARD_LIMIT_BYTES else 'WARN'
            print(f'  {marker}: {rel} bytes={size}')
        print('Consider not committing files above 100MB to GitHub.')

    if args.dry_run:
        print('dry run complete; no files changed')
        return 0

    if args.commit or args.push:
        run_git(['add', str(args.dest)], cwd=repo)
        status = subprocess.run(['git', 'status', '--short', str(args.dest)], cwd=repo, check=True, capture_output=True, text=True).stdout
        if status.strip():
            run_git(['commit', '-m', args.message], cwd=repo)
        else:
            print('No changes to commit.')
        if args.push:
            run_git(['push'], cwd=repo)

    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
