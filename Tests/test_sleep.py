import unittest
from typing import Any, Dict, List

import TagScriptEngine as tse
from TagScriptEngine import Interpreter, block


class TestSleepBlock(unittest.TestCase):
    def setUp(self):
        # The sleep block records its position relative to the command blocks,
        # so both are needed to exercise it properly.
        self.engine: Interpreter = Interpreter([block.SleepBlock(), block.CommandBlock()])

    def sleeps(self, script: str) -> List[Dict[str, Any]]:
        return self.engine.process(script).actions.get("sleeps", [])

    # -- acceptance --------------------------------------------------------

    def test_aliases(self):
        for name in ("sleep", "pause", "wait"):
            self.assertEqual(self.sleeps("{%s(2)}" % name), [{"index": 0, "seconds": 2.0}], name)

    def test_payload_form(self):
        self.assertEqual(self.sleeps("{sleep:2}"), [{"index": 0, "seconds": 2.0}])

    def test_bare_block_is_consumed(self):
        # Was asserted to echo "{sleep}". Sleep is an action block, so it now
        # consumes the verb rather than leaking raw tagscript into the message.
        response = self.engine.process("{sleep}")
        self.assertEqual(response.body, "")
        self.assertNotIn("sleeps", response.actions)

    def test_block_leaves_no_text(self):
        self.assertEqual(self.engine.process("a{sleep(1)}b").body, "ab")

    # -- position tracking -------------------------------------------------

    def test_index_counts_preceding_commands(self):
        # {c:ping} {sleep(3)} {c:help} -> the sleep sits after 1 command.
        self.assertEqual(self.sleeps("{c:ping}{sleep(3)}{c:help}"), [{"index": 1, "seconds": 3.0}])

    def test_leading_sleep_has_index_zero(self):
        self.assertEqual(self.sleeps("{sleep(3)}{c:ping}"), [{"index": 0, "seconds": 3.0}])

    def test_trailing_sleep_indexes_past_last_command(self):
        self.assertEqual(self.sleeps("{c:ping}{sleep(3)}"), [{"index": 1, "seconds": 3.0}])

    def test_multiple_sleeps_keep_order_and_position(self):
        response = self.engine.process("{sleep(1)}{c:ping}{sleep(2)}{c:help}{sleep(3)}")
        self.assertEqual(
            response.actions["sleeps"],
            [
                {"index": 0, "seconds": 1.0},
                {"index": 1, "seconds": 2.0},
                {"index": 2, "seconds": 3.0},
            ],
        )
        self.assertEqual(response.actions["commands"], ["ping", "help"])

    def test_sleeps_do_not_count_toward_command_limit(self):
        # Three commands is the default cap; the sleeps between them must not
        # consume any of that budget.
        response = self.engine.process("{c:a}{sleep(1)}{c:b}{sleep(1)}{c:c}")
        self.assertEqual(response.actions["commands"], ["a", "b", "c"])
        self.assertNotIn("COMMAND LIMIT", response.body)

    # -- parsing / validation ----------------------------------------------

    def test_fractional_seconds(self):
        self.assertEqual(self.sleeps("{sleep(1.5)}"), [{"index": 0, "seconds": 1.5}])

    def test_non_number_errors(self):
        self.assertIn("Sleep Parse Error", self.engine.process("{sleep(abc)}").body)

    def test_zero_and_negative_error(self):
        for payload in ("0", "-3"):
            self.assertIn(
                "must be greater than 0", self.engine.process("{sleep(%s)}" % payload).body
            )

    # -- budget ------------------------------------------------------------

    def test_total_budget_is_capped(self):
        engine = Interpreter([block.SleepBlock(limit=5)])
        response = engine.process("{sleep(3)}{sleep(3)}")
        self.assertIn("MAX SLEEP REACHED", response.body)
        # The first sleep is kept, the one that would bust the budget is not.
        self.assertEqual(response.actions["sleeps"], [{"index": 0, "seconds": 3.0}])

    def test_sleep_exactly_at_budget_is_allowed(self):
        engine = Interpreter([block.SleepBlock(limit=5)])
        response = engine.process("{sleep(5)}")
        self.assertEqual(response.actions["sleeps"], [{"index": 0, "seconds": 5.0}])
        self.assertNotIn("MAX SLEEP", response.body)

    def test_configurable_limit(self):
        engine = Interpreter([block.SleepBlock(limit=30)])
        self.assertEqual(
            engine.process("{sleep(30)}").actions["sleeps"], [{"index": 0, "seconds": 30.0}]
        )

    def test_exported_at_top_level(self):
        self.assertTrue(hasattr(tse, "SleepBlock"))


if __name__ == "__main__":
    unittest.main()
