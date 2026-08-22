"""softlint — a constraint-softening lexical linter for agent rule files.

Detects when a strict constraint word in a SKILL.md / CLAUDE.md / AGENTS.md
style file has been silently rewritten into a softer, hedged version
(e.g. "never" -> "avoid", "must" -> "should") between two versions of the
same file. No LLM calls, no network access — pure text diffing.
"""

__version__ = "0.1.0"
