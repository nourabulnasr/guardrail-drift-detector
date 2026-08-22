"""Core diff-based detection: compare an old and new version of a text file
and report constraint-softening swaps."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from .rules import RULES, Rule


@dataclass(frozen=True)
class Violation:
    rule_id: str
    note: str
    old_line_no: int  # 1-indexed, first line of the changed old block
    new_line_no: int  # 1-indexed, first line of the changed new block
    old_snippet: str
    new_snippet: str
    matched_strict: str
    matched_soft: str

    def format(self) -> str:
        return (
            f"[{self.rule_id}] {self.note}\n"
            f"  - old (line {self.old_line_no}): {self.old_snippet.strip()!r}\n"
            f"  + new (line {self.new_line_no}): {self.new_snippet.strip()!r}"
        )


def _word_re(fragment: str) -> re.Pattern:
    # Fragments already contain their own boundaries where needed (e.g. \b);
    # for plain words, wrap with word boundaries so "must" doesn't match
    # "mustard".
    if fragment.startswith(r"\b") or " " in fragment or fragment.endswith(")"):
        pattern = fragment
    else:
        pattern = rf"\b{fragment}\b"
    return re.compile(pattern, re.IGNORECASE)


def _first_match(patterns: tuple[str, ...], text: str) -> str | None:
    for frag in patterns:
        m = _word_re(frag).search(text)
        if m:
            return m.group(0)
    return None


def find_softenings(old_text: str, new_text: str) -> list[Violation]:
    """Compare two full-file text strings and return a list of Violations.

    Uses a line-based diff (difflib.SequenceMatcher) to find changed
    blocks, then checks each changed block against the known strict->soft
    word-pair rules in rules.RULES.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    violations: list[Violation] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag not in ("replace", "delete"):
            continue

        old_chunk = "\n".join(old_lines[i1:i2])
        # For a pure delete (strict line removed, nothing added in its
        # place), compare against the immediate surrounding new context so
        # a strict rule that was deleted outright (not softened, just
        # dropped) is not falsely flagged as "softened" — that's a
        # different failure mode (silent removal) this tool intentionally
        # does not claim to catch. Only 'replace' blocks are evaluated for
        # softening because a softening requires replacement text.
        if tag == "delete":
            continue

        # When a replace hunk has the same number of old and new lines, we
        # can pair them 1:1 and report a precise single-line snippet
        # instead of the whole (possibly multi-line) hunk. When the line
        # counts differ (e.g. a line was also inserted in the same hunk),
        # fall back to matching against the hunk as a whole block.
        old_block = old_lines[i1:i2]
        new_block = new_lines[j1:j2]

        if len(old_block) == len(new_block):
            pairs = [
                ((line_old,), (line_new,), i1 + k + 1, j1 + k + 1)
                for k, (line_old, line_new) in enumerate(zip(old_block, new_block))
            ]
        else:
            pairs = [(tuple(old_block), tuple(new_block), i1 + 1, j1 + 1)]

        for old_part, new_part, old_no, new_no in pairs:
            old_chunk = "\n".join(old_part)
            new_chunk = "\n".join(new_part)

            for rule in RULES:
                strict_match = _first_match(rule.strict, old_chunk)
                if not strict_match:
                    continue
                # If the strict word is STILL present in the new chunk,
                # this isn't a softening — the rule may just be restated.
                if _first_match(rule.strict, new_chunk):
                    continue
                soft_match = _first_match(rule.soft, new_chunk)
                if not soft_match:
                    continue

                violations.append(
                    Violation(
                        rule_id=rule.id,
                        note=rule.note,
                        old_line_no=old_no,
                        new_line_no=new_no,
                        old_snippet=old_chunk,
                        new_snippet=new_chunk,
                        matched_strict=strict_match,
                        matched_soft=soft_match,
                    )
                )

    return violations
