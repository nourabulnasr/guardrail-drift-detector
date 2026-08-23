import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardrail_drift_detector.core import find_softenings


class TestFindSoftenings(unittest.TestCase):
    def test_never_softened_to_avoid(self):
        old = "Never write secrets to config files."
        new = "Avoid writing secrets to config files."
        violations = find_softenings(old, new)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "never->avoid")

    def test_must_softened_to_should(self):
        old = "You must validate all input."
        new = "You should validate all input."
        violations = find_softenings(old, new)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "must->should")

    def test_required_softened_to_recommended(self):
        old = "A rollback plan is required for every PR."
        new = "A rollback plan is recommended for every PR."
        violations = find_softenings(old, new)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].rule_id, "required->recommended")

    def test_two_rules_fire_on_same_line(self):
        old = "Required: every PR must include a rollback plan."
        new = "Recommended: every PR should include a rollback plan."
        violations = find_softenings(old, new)
        ids = {v.rule_id for v in violations}
        self.assertIn("required->recommended", ids)
        self.assertIn("must->should", ids)

    def test_no_false_positive_on_unrelated_edit(self):
        old = "Always run the test suite before committing."
        new = "Always run the full test suite before committing."
        violations = find_softenings(old, new)
        self.assertEqual(violations, [])

    def test_no_false_positive_when_strict_word_kept(self):
        old = "You must never skip code review."
        new = "You must never, under any circumstance, skip code review."
        violations = find_softenings(old, new)
        self.assertEqual(violations, [])

    def test_no_false_positive_on_addition_only(self):
        old = "Run the linter."
        new = "Run the linter.\nTag every deploy with a version."
        violations = find_softenings(old, new)
        self.assertEqual(violations, [])

    def test_rewording_without_known_soft_word_not_flagged(self):
        # Silent removal is a different failure mode than softening —
        # this tool only claims to catch strict->soft *word* swaps.
        old = "Do not push directly to the main branch."
        new = "Pushing directly to the main branch is not the standard workflow."
        violations = find_softenings(old, new)
        self.assertEqual(violations, [])

    def test_full_demo_files_produce_expected_violation_count(self):
        demo_dir = Path(__file__).resolve().parent.parent / "demo"
        old = (demo_dir / "before.md").read_text(encoding="utf-8")
        new = (demo_dir / "after.md").read_text(encoding="utf-8")
        violations = find_softenings(old, new)
        ids = sorted(v.rule_id for v in violations)
        self.assertEqual(
            ids,
            sorted([
                "never->avoid",
                "must->should",
                "forbidden->discouraged",
                "required->recommended",
                "must->should",
            ]),
        )


if __name__ == "__main__":
    unittest.main()
