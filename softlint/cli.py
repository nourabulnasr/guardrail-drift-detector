"""Command-line entry point for softlint.

Three ways to use it:

  softlint diff OLD_FILE NEW_FILE
      Compare two files on disk directly. No git required. This is the
      30-second demo path.

  softlint check FILE [--staged]
      Compare a file's git HEAD version against its current working-tree
      (or, with --staged, index/staged) version. Must be run inside a git
      repo.

  softlint check-staged [PATTERN ...]
      Find all staged files matching the given glob patterns (default:
      CLAUDE.md, AGENTS.md, SKILL.md, and *SKILL.md at any depth) that
      already existed at HEAD, and run `check --staged` on each. This is
      what the pre-commit hook calls.

  softlint install-hook
      Write a pre-commit hook into the current repo's .git/hooks/ that
      runs `check-staged` and blocks the commit if it finds violations.

Exit code is 1 if any violation is found (so it composes as a git hook or
CI check), 0 otherwise.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

from .core import find_softenings

DEFAULT_PATTERNS = ["CLAUDE.md", "AGENTS.md", "SKILL.md", "*SKILL.md"]

PRE_COMMIT_HOOK = """#!/bin/sh
# Installed by softlint (constraint-softening-linter).
# Blocks commits that silently soften constraint language in
# CLAUDE.md / AGENTS.md / SKILL.md files.
python -m softlint check-staged
exit $?
"""


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout


def _print_violations(violations, source: str) -> None:
    if not violations:
        print(f"softlint: {source} - no constraint-softening detected. Clean.")
        return
    print(f"softlint: {source} - {len(violations)} constraint-softening violation(s) found:\n")
    for v in violations:
        print(v.format())
        print()


def cmd_diff(args: argparse.Namespace) -> int:
    old_text = Path(args.old_file).read_text(encoding="utf-8")
    new_text = Path(args.new_file).read_text(encoding="utf-8")
    violations = find_softenings(old_text, new_text)
    _print_violations(violations, f"{args.old_file} -> {args.new_file}")
    return 1 if violations else 0


def cmd_check(args: argparse.Namespace) -> int:
    path = args.file
    try:
        old_text = _run_git(["show", f"HEAD:{path}"])
    except RuntimeError as e:
        print(f"softlint: could not read HEAD version of {path}: {e}", file=sys.stderr)
        return 2

    if args.staged:
        new_text = _run_git(["show", f":{path}"])
    else:
        new_text = Path(path).read_text(encoding="utf-8")

    violations = find_softenings(old_text, new_text)
    _print_violations(violations, path)
    return 1 if violations else 0


def cmd_check_staged(args: argparse.Namespace) -> int:
    patterns = args.patterns or DEFAULT_PATTERNS
    try:
        staged_files = [
            line for line in _run_git(
                ["diff", "--cached", "--name-only", "--diff-filter=M"]
            ).splitlines() if line.strip()
        ]
    except RuntimeError as e:
        print(f"softlint: {e}", file=sys.stderr)
        return 2

    matched = [
        f for f in staged_files
        if any(fnmatch.fnmatch(Path(f).name, pat) for pat in patterns)
    ]

    if not matched:
        print("softlint: no staged CLAUDE.md / AGENTS.md / SKILL.md changes to check.")
        return 0

    exit_code = 0
    for path in matched:
        ns = argparse.Namespace(file=path, staged=True)
        code = cmd_check(ns)
        exit_code = max(exit_code, code)
    return exit_code


def cmd_install_hook(args: argparse.Namespace) -> int:
    try:
        git_dir = _run_git(["rev-parse", "--git-dir"]).strip()
    except RuntimeError as e:
        print(f"softlint: not inside a git repo: {e}", file=sys.stderr)
        return 2

    hooks_dir = Path(git_dir) / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists() and not args.force:
        print(
            f"softlint: {hook_path} already exists. Re-run with --force to overwrite.",
            file=sys.stderr,
        )
        return 2

    hook_path.write_text(PRE_COMMIT_HOOK, encoding="utf-8", newline="\n")
    hook_path.chmod(0o755)
    print(f"softlint: installed pre-commit hook at {hook_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="softlint", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_diff = sub.add_parser("diff", help="Compare two files directly (no git needed)")
    p_diff.add_argument("old_file")
    p_diff.add_argument("new_file")
    p_diff.set_defaults(func=cmd_diff)

    p_check = sub.add_parser("check", help="Compare a file's HEAD version vs working tree/staged")
    p_check.add_argument("file")
    p_check.add_argument("--staged", action="store_true", help="Compare against staged (index) content instead of working tree")
    p_check.set_defaults(func=cmd_check)

    p_staged = sub.add_parser("check-staged", help="Check all staged CLAUDE.md/AGENTS.md/SKILL.md files")
    p_staged.add_argument("patterns", nargs="*", help="Override default filename glob patterns")
    p_staged.set_defaults(func=cmd_check_staged)

    p_hook = sub.add_parser("install-hook", help="Install the pre-commit hook into this repo")
    p_hook.add_argument("--force", action="store_true")
    p_hook.set_defaults(func=cmd_install_hook)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
