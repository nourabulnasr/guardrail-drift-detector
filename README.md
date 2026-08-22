# softlint — constraint-softening lexical linter

A pre-commit hook that catches a specific, silent failure mode in
agent rule files (`CLAUDE.md`, `AGENTS.md`, `SKILL.md`): someone edits a
hard constraint into a hedge without meaning to weaken it, and nobody
notices because the diff still reads like a normal wording tweak.

The pain point is real and named by an actual source: [blog.bgener.nl]
gives the example of `"never write secrets"` being quietly rewritten to
`"avoid writing secrets to config files"` — a one-word change that turns
a hard rule into a suggestion, with no review flag anywhere to catch it.

softlint catches that class of edit: it diffs the old and new version of
a rule file, and flags any place where a **strict** word (never, must,
required, forbidden, ...) disappeared and a **softened** counterpart
(avoid, should, recommended, discouraged, ...) took its place in the
same spot.

[blog.bgener.nl]: https://blog.bgener.nl/

## What this does NOT do

- It is **not an LLM judge**. It is a static word-list + line diff. Zero
  network calls, zero API keys, fully deterministic. That's the point —
  it's cheap, auditable, and it can't hallucinate a false sense of
  security.
- It only catches **known word swaps** (see `softlint/rules.py` for the
  full list — `never→avoid`, `must→should`, `required→recommended`,
  `forbidden→discouraged`, `mandatory→optional`, `shall→should`,
  `cannot→should not`, `will→may`, `critical→important`, `do not→try not
  to`, `non-negotiable→preferred`, and a few more). A rewrite it doesn't
  recognize will slip through. It is a lint, not a proof.
- It does not catch a strict rule being **deleted outright** with no
  replacement text — that's a different failure mode (silent removal,
  not softening) and this tool doesn't claim to catch it.
- It's line-diff based (`difflib`), so a constraint reworded across a
  paragraph reflow rather than a clean line-for-line edit may be missed
  or reported with a wider snippet than the single line that changed.

## How it works

1. `difflib.SequenceMatcher` finds the changed line-blocks between the
   old and new version of a file.
2. For each changed block, check every rule in `softlint/rules.py`: did
   a strict word that was present in the old block disappear from the
   new block, replaced by that rule's softened counterpart?
3. If yes → violation. Report the rule, the exact old/new line(s), and
   exit code `1` (so it composes as a git hook or CI check).

## 30-second demo (no git needed)

```bash
pip install -e .          # optional — stdlib only, this just gets you the `softlint` command
python -m softlint diff demo/before.md demo/after.md
```

Expected output: 5 violations, one per softened line in
[`demo/after.md`](demo/after.md) vs [`demo/before.md`](demo/before.md)
— including two rules firing on the same edited line (`required` →
`recommended` AND `must` → `should` in one sentence) — and **zero**
false positives on the benign edits in that same diff (an unrelated
wording tweak, a strict word that's merely restated more emphatically,
and a rewrite with no recognized soft word). Exit code `1`.

## Using it as a real pre-commit hook

```bash
cd your-repo
python -m softlint install-hook
```

This writes `.git/hooks/pre-commit`, which runs `softlint check-staged`
on every commit. It finds any staged `CLAUDE.md` / `AGENTS.md` /
`SKILL.md` (or `*SKILL.md`) file that already existed at `HEAD`, diffs
the staged version against `HEAD`, and **blocks the commit** if a
softening swap is detected.

This was verified for real on this repo, not just asserted: a
`CLAUDE.md` was committed with strict wording, then staged with the
softened wording from `demo/after.md`, then `git commit` was run with
the hook installed. The commit was rejected (exit code 1, no commit
created) — see `build-summary.md` in the job folder for the actual
terminal transcript.

## CLI reference

| Command | What it does |
|---|---|
| `softlint diff OLD NEW` | Compare two files directly. No git needed. |
| `softlint check FILE [--staged]` | Compare `FILE`'s `HEAD` version against its working-tree (or, with `--staged`, index) version. Run inside a git repo. |
| `softlint check-staged [PATTERN ...]` | Check all staged files matching the given filename globs (default: `CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `*SKILL.md`) that already exist at `HEAD`. What the hook calls. |
| `softlint install-hook [--force]` | Write the pre-commit hook into the current repo. |

## Run the tests

```bash
python -m pytest tests/ -v
```

9 tests, stdlib + pytest only, no network, no API keys.

## Project layout

```
softlint/
  rules.py     # the strict -> soft word-pair list (the whole "brain" of the tool)
  core.py      # the diff + match engine
  cli.py       # argparse CLI: diff / check / check-staged / install-hook
demo/
  before.md    # a CLAUDE.md-style rules file, all strict language
  after.md     # the same file after 5 silent softening edits + 2 benign edits
tests/
  test_core.py # unit tests, including a full before/after.md regression test
```

## What's missing / what a human should do before shipping this wider

- The word list in `rules.py` is a starting set (~13 pairs), not
  exhaustive. Extending it is just adding another `Rule(...)` entry —
  no code changes needed.
- No packaging/publish step (no `pyproject.toml` `[project]` metadata
  beyond the minimum to make `pip install -e .` work) — fine for a
  single-repo hook, would need real packaging to distribute as a
  standalone pip package.
- `check-staged`'s default file-matching is filename-based
  (`CLAUDE.md`, `AGENTS.md`, `SKILL.md`, `*SKILL.md`), not path-based —
  a repo with unusually named rule files would need
  `softlint check-staged '*.rules.md'`-style overrides.
- No CI workflow file included (e.g. a GitHub Action running `softlint
  check` against the last commit on every PR) — the pre-commit hook is
  local-only and can be bypassed with `git commit --no-verify`, same as
  any pre-commit hook.
