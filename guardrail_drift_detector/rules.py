"""The word-list of known strict -> softened constraint-language swaps.

Each rule is a pair of word groups. A violation fires when a line (or
contiguous block of changed lines) that matched one of the STRICT patterns
in the old version no longer matches any STRICT pattern in the new version,
but the new version does match one of the SOFT patterns for that same rule.

This is deliberately a static word list, not an LLM judgment call — that's
the whole point (deterministic, zero-cost, auditable). It will miss
rephrasings it doesn't know about, and that's a known, stated limitation
(see README "What this does NOT do").
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    strict: tuple[str, ...]   # regex fragments, matched case-insensitively, word-bounded
    soft: tuple[str, ...]     # regex fragments that indicate the strict word was hedged
    note: str


RULES: tuple[Rule, ...] = (
    Rule(
        id="never->avoid",
        strict=(r"never",),
        soft=(r"avoid", r"try (?:to )?not to", r"generally avoid"),
        note='"never" softened to a word that allows exceptions',
    ),
    Rule(
        id="always->try-to",
        strict=(r"always",),
        soft=(r"try to", r"generally", r"usually", r"typically", r"where possible"),
        note='"always" softened to a word that allows exceptions',
    ),
    Rule(
        id="must->should",
        strict=(r"must(?!\s+not)",),
        soft=(r"should", r"ought to", r"try to", r"it'?s (?:best|better) to"),
        note='"must" (obligation) softened to "should" (suggestion)',
    ),
    Rule(
        id="must-not->should-not",
        strict=(r"must not", r"mustn'?t"),
        soft=(r"should not", r"shouldn'?t", r"try not to", r"better not to"),
        note='"must not" (prohibition) softened to "should not" (suggestion)',
    ),
    Rule(
        id="required->recommended",
        strict=(r"required", r"requires",),
        soft=(r"recommended", r"suggested", r"preferred", r"encouraged"),
        note='"required" softened to "recommended" - no longer mandatory',
    ),
    Rule(
        id="mandatory->optional",
        strict=(r"mandatory",),
        soft=(r"optional", r"preferred", r"encouraged"),
        note='"mandatory" softened to "optional"',
    ),
    Rule(
        id="forbidden->discouraged",
        strict=(r"forbidden", r"prohibited",),
        soft=(r"discouraged", r"not recommended", r"generally avoided"),
        note='"forbidden" softened to "discouraged" - no longer a hard block',
    ),
    Rule(
        id="shall->should",
        strict=(r"shall(?!\s+not)",),
        soft=(r"should", r"may"),
        note='"shall" softened to "should"',
    ),
    Rule(
        id="cannot->should-not",
        strict=(r"cannot", r"can not", r"can'?t"),
        soft=(r"should not", r"shouldn'?t", r"try (?:to )?not to"),
        note='"cannot" (hard block) softened to "should not" (guidance)',
    ),
    Rule(
        id="will->may",
        strict=(r"\bwill\b",),
        soft=(r"\bmay\b", r"\bmight\b", r"\bcould\b"),
        note='"will" (certainty) softened to "may" (possibility)',
    ),
    Rule(
        id="critical->important",
        strict=(r"critical", r"crucial"),
        soft=(r"important", r"helpful", r"useful"),
        note='"critical" softened to a weaker priority word',
    ),
    Rule(
        id="do-not->try-not-to",
        strict=(r"do not\b", r"don'?t\b"),
        soft=(r"try (?:to )?not to", r"avoid", r"generally avoid"),
        note='"do not" (instruction) softened to "try not to" (hedge)',
    ),
    Rule(
        id="non-negotiable->preferred",
        strict=(r"non-negotiable", r"not negotiable"),
        soft=(r"preferred", r"flexible", r"a strong preference"),
        note='"non-negotiable" softened to "preferred"',
    ),
)
