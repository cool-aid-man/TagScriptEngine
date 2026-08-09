import unittest

import TagScriptEngine as tse
from TagScriptEngine import Interpreter, block


class TestEscapes(unittest.TestCase):
    def setUp(self):
        self.engine = Interpreter(
            [
                block.MathBlock(),
                block.RandomBlock(),
                block.IfBlock(),
                block.LooseVariableGetterBlock(),
            ]
        )

    def test_escape_content_escapes_special_characters(self):
        self.assertEqual(tse.escape_content("message provided :"), "message provided \\:")
        self.assertEqual(tse.escape_content("{a(b):c|d}"), "\\{a\\(b\\)\\:c\\|d\\}")

    def test_escape_content_none_passthrough(self):
        self.assertIsNone(tse.escape_content(None))

    def test_escaped_braces_are_not_processed(self):
        # A backslash-escaped block must stay literal even when a matching
        # block is registered.
        script = r"\{random:a,b\}"
        self.assertEqual(self.engine.process(script).body, script)
        script = r"\{math:1+1\}"
        self.assertEqual(self.engine.process(script).body, script)

    def test_unescaped_braces_are_processed(self):
        self.assertEqual(float(self.engine.process("{math:1+1}").body), 2.0)

    def test_escaped_variable_content_does_not_break_if_block(self):
        # Escaped user content must not terminate the if-block's payload early.
        msg = tse.escape_content("message provided :")
        response = self.engine.process(
            "{if({msg}==):provide a message|{msg}}", {"msg": tse.StringAdapter(msg)}
        )
        self.assertEqual(response.body, "message provided \\:")


if __name__ == "__main__":
    unittest.main()
