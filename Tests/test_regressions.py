"""Regression tests for the 3.3.4 audit fixes."""

import json
import random
import time
import unittest

from TagScriptEngine import Interpreter, StringAdapter, Verb, block
from TagScriptEngine.block.helpers import helper_parse_if, helper_split
from TagScriptEngine.utils import truncate


class TestPythonBlockCrash(unittest.TestCase):
    """{in}/{contains}/{index} without a payload used to raise ProcessError."""

    def setUp(self):
        self.engine = Interpreter([block.PythonBlock()])

    def test_missing_payload_does_not_crash(self):
        for script in ("{in(apple)}", "{contains(x)}", "{index(x)}"):
            self.assertEqual(self.engine.process(script).body, script)

    def test_empty_payload_is_answered(self):
        # A payload that resolved to "" is a real question with a real answer.
        # Declining leaked `{contains(|):}` into the message and, worse, made the
        # enclosing `{if(...==false)}` guard unsatisfiable.
        self.assertEqual(self.engine.process("{contains(x):}").body, "false")
        self.assertEqual(self.engine.process("{in(x):}").body, "false")
        self.assertEqual(self.engine.process("{index(x):}").body, "-1")

    def test_empty_parameter_still_declines(self):
        # Unlike the payload, an empty parameter is not a question.
        for script in ("{contains():x}", "{in():x}", "{index():x}"):
            self.assertEqual(self.engine.process(script).body, script)

    def test_normal_usage_still_works(self):
        self.assertEqual(self.engine.process("{in(apple):apple pie}").body, "true")
        self.assertEqual(self.engine.process("{contains(pie):apple pie}").body, "true")
        self.assertEqual(self.engine.process("{index(pie):apple pie}").body, "1")


class TestBreakBlockCrash(unittest.TestCase):
    """Bare {break} used to raise ProcessError from None.lower()."""

    def setUp(self):
        self.engine = Interpreter([block.BreakBlock()])

    def test_bare_break_does_not_crash(self):
        for script in ("hello {break}", "hello {short}", "hello {shortcircuit}"):
            self.assertEqual(self.engine.process(script).body, "hello")

    def test_break_still_triggers(self):
        self.assertEqual(self.engine.process("ignored {break(true):msg}").body, "msg")


class TestCaseBlocks(unittest.TestCase):
    """{upper(none)} used to be eaten by a string sentinel check."""

    def setUp(self):
        self.engine = Interpreter([block.UpperBlock(), block.LowerBlock()])

    def test_literal_none_is_preserved(self):
        self.assertEqual(self.engine.process("{upper(none)}").body, "NONE")
        self.assertEqual(self.engine.process("{lower(NONE)}").body, "none")

    def test_missing_parameter_is_consumed(self):
        # See TestCaseBlocksConsumeWithoutParameter: declining here would leak
        # the raw block whenever no same-named variable exists.
        self.assertEqual(self.engine.process("{upper}").body, "")
        self.assertEqual(self.engine.process("{lower}").body, "")

    def test_normal_usage(self):
        self.assertEqual(self.engine.process("{upper(abc)}").body, "ABC")
        self.assertEqual(self.engine.process("{lower(ABC)}").body, "abc")


class TestSeededRandomIsolation(unittest.TestCase):
    """Seeded blocks used to reseed the process-wide RNG."""

    def test_seeded_range_does_not_touch_global_rng(self):
        engine = Interpreter([block.RangeBlock()])
        state = random.getstate()
        engine.process("{range(5):1-10}")
        self.assertEqual(random.getstate(), state)

    def test_seeded_random_does_not_touch_global_rng(self):
        engine = Interpreter([block.RandomBlock()])
        state = random.getstate()
        engine.process("{random(seed):a,b,c}")
        self.assertEqual(random.getstate(), state)

    def test_seeded_blocks_stay_deterministic(self):
        engine = Interpreter([block.RandomBlock(), block.RangeBlock()])
        picks = {engine.process("{random(seed):a,b,c}").body for _ in range(10)}
        self.assertEqual(len(picks), 1)
        rolls = {engine.process("{range(5):1-10}").body for _ in range(10)}
        self.assertEqual(len(rolls), 1)


class TestCooldownBlock(unittest.TestCase):
    def setUp(self):
        block.CooldownBlock.COOLDOWNS.clear()
        self.engine = Interpreter([block.CooldownBlock()])

    def test_malformed_parameter_fails_closed(self):
        body = self.engine.process("{cooldown(1|x):key}").body
        self.assertIn("cooldown error", body)

    def test_fractional_per_is_accepted(self):
        # rate is the use count (int), per is seconds (float) - 1.5s is legal.
        self.assertEqual(self.engine.process("{cooldown(1|1.5):key}").body, "")

    def test_eviction_cap(self):
        for i in range(block.CooldownBlock.MAX_COOLDOWNS + 10):
            block.CooldownBlock.create_cooldown(f"key-{i}", 1, 10.0)
        self.assertLessEqual(len(block.CooldownBlock.COOLDOWNS), block.CooldownBlock.MAX_COOLDOWNS)


class TestMathBlockLimits(unittest.TestCase):
    def setUp(self):
        self.engine = Interpreter([block.MathBlock()])

    def test_power_is_right_associative(self):
        self.assertEqual(float(self.engine.process("{math:2^3^2}").body), 512.0)

    def test_huge_exponent_is_refused(self):
        # Previously this overflowed to a raw block. It is now refused up front
        # with a message, so the user can tell the expression was rejected.
        self.assertIn("MATH LIMIT EXCEEDED", self.engine.process("{math:9^9^9}").body)

    def test_integer_pow_cannot_hang(self):
        # round()/trunc()/abs() return Python ints, and int ** int is arbitrary
        # precision - it never raises OverflowError, it just runs forever.
        # `round(9)^round(9)^round(9)` is 9**387420489. Before the guard this
        # pinned the event loop indefinitely; it must now return promptly.
        start = time.monotonic()
        body = self.engine.process("{math:round(9)^round(9)^round(9)}").body
        self.assertLess(time.monotonic() - start, 5.0)
        self.assertIn("MATH LIMIT EXCEEDED", body)

    def test_ordinary_math_still_works(self):
        self.assertEqual(self.engine.process("{math:2+3}").body, "5.0")
        self.assertEqual(self.engine.process("{math:round(7/3)}").body, "2")
        self.assertEqual(self.engine.process("{math:2^10}").body, "1024.0")
        self.assertEqual(self.engine.process("{math:sqrt(144)}").body, "12.0")


class TestVerbDotParameter(unittest.TestCase):
    """Dot-parameter payloads used to keep the colon and drop the payload."""

    def test_payload_after_colon(self):
        v = Verb("{user.name:x}", dot_parameter=True)
        self.assertEqual(v.declaration, "user")
        self.assertEqual(v.parameter, "name")
        self.assertEqual(v.payload, "x")

    def test_no_payload(self):
        v = Verb("{user.name}", dot_parameter=True)
        self.assertEqual(v.declaration, "user")
        self.assertEqual(v.parameter, "name")
        self.assertIsNone(v.payload)


class TestHelperParseIf(unittest.TestCase):
    def test_equality_splits_once(self):
        # "a==a==a" must compare "a" against "a==a", not silently drop the tail.
        self.assertFalse(helper_parse_if("a==a==a"))
        self.assertTrue(helper_parse_if("a==a"))
        self.assertTrue(helper_parse_if("a!=a==a"))

    def test_chained_numeric_comparison_is_invalid(self):
        # "3>2>1" is not a valid comparison; it must not silently compare
        # only the first two operands.
        self.assertIsNone(helper_parse_if("3>2>1"))
        self.assertTrue(helper_parse_if("3>2"))


class TestEmbedBlockMalformedJson(unittest.TestCase):
    """Non-dict "embed"/non-str "timestamp" keys used to raise ProcessError."""

    def setUp(self):
        self.engine = Interpreter([block.EmbedBlock()])

    def test_malformed_json_degrades_gracefully(self):
        for script in (
            '{embed({"embed":"hi"})}',
            '{embed({"embed":5})}',
            '{embed({"timestamp":123})}',
        ):
            body = self.engine.process(script).body
            self.assertIn("Embed Parse Error", body, script)

    def test_valid_embed_still_parses(self):
        response = self.engine.process('{embed({"title":"hello"})}')
        self.assertEqual(response.body, "")
        self.assertEqual(response.actions["embed"].title, "hello")


class TestAssignEmptyPayload(unittest.TestCase):
    """{=(x)} used to store the literal string "None"."""

    def test_assign_without_payload_is_empty(self):
        engine = Interpreter([block.AssignmentBlock(), block.LooseVariableGetterBlock()])
        self.assertEqual(engine.process("{=(x)}{x}").body, "")


class TestComponentCompAlias(unittest.TestCase):
    def test_comp_alias_accepted(self):
        engine = Interpreter([block.ComponentBlock()])
        response = engine.process("{comp(text):hi}")
        self.assertIn("components_v2", response.actions)


class TestTruncateReservesVarLength(unittest.TestCase):
    """truncate() hardcoded 3 chars regardless of how long `var` actually was."""

    def test_default_var(self):
        self.assertEqual(len(truncate("x" * 100, max=10)), 10)

    def test_longer_var_still_fits(self):
        self.assertEqual(len(truncate("x" * 100, max=10, var="[snip]")), 10)

    def test_empty_var_uses_full_budget(self):
        self.assertEqual(len(truncate("x" * 100, max=10, var="")), 10)

    def test_var_longer_than_max_does_not_go_negative(self):
        self.assertEqual(truncate("x" * 100, max=2, var="....."), ".....")

    def test_short_text_untouched(self):
        self.assertEqual(truncate("abc", max=10), "abc")


class TestStrfIsUTC(unittest.TestCase):
    """fromtimestamp()/now() returned host-local time stamped as UTC."""

    def setUp(self):
        self.engine = Interpreter([block.StrfBlock()])

    def test_epoch_zero_is_utc(self):
        # Independent of the host timezone this must be the UTC epoch.
        self.assertEqual(self.engine.process("{strf(0):%Y-%m-%d %H:%M}").body, "1970-01-01 00:00")

    def test_known_timestamp_is_utc(self):
        self.assertEqual(
            self.engine.process("{strf(1420070400):%Y-%m-%d %H:%M}").body, "2015-01-01 00:00"
        )

    def test_unix_alias_still_works(self):
        self.assertTrue(self.engine.process("{unix}").body.isdigit())


class TestSleepRejectsNonFinite(unittest.TestCase):
    """nan poisoned the running total, because every nan comparison is False."""

    def setUp(self):
        self.engine = Interpreter([block.SleepBlock(limit=10.0)])

    def test_nan_is_rejected(self):
        response = self.engine.process("{sleep(nan)}")
        self.assertFalse(response.actions.get("sleeps"))

    def test_nan_does_not_unlock_the_budget(self):
        # The second sleep is far over the 10s cap and must still be refused.
        # Before the fix both were recorded, including the 9999s one.
        response = self.engine.process("{sleep(nan)}{sleep(9999)}")
        self.assertFalse(response.actions.get("sleeps"))

    def test_inf_is_rejected(self):
        self.assertFalse(self.engine.process("{sleep(inf)}").actions.get("sleeps"))

    def test_normal_sleep_still_recorded(self):
        sleeps = self.engine.process("{sleep(3)}").actions["sleeps"]
        self.assertEqual([s["seconds"] for s in sleeps], [3.0])


class TestOrdBlockExports(unittest.TestCase):
    """ordblock.__all__ named a class that does not exist."""

    def test_star_import_resolves(self):
        namespace = {}
        exec("from TagScriptEngine.block.ordblock import *", namespace)
        self.assertIn("OrdinalBlock", namespace)


class TestVerbMultiDotParameter(unittest.TestCase):
    """Every dot opened a new level, so multi-dot parameters never closed."""

    def test_multi_dot_parameter(self):
        v = Verb("{user.name.thing}", dot_parameter=True)
        self.assertEqual(v.declaration, "user")
        self.assertEqual(v.parameter, "name.thing")

    def test_multi_dot_with_payload(self):
        v = Verb("{user.name.thing:hi}", dot_parameter=True)
        self.assertEqual(v.declaration, "user")
        self.assertEqual(v.parameter, "name.thing")
        self.assertEqual(v.payload, "hi")

    def test_single_dot_unchanged(self):
        v = Verb("{user.name}", dot_parameter=True)
        self.assertEqual((v.declaration, v.parameter), ("user", "name"))

    def test_parenthesis_mode_unaffected(self):
        v = Verb("{user(name)}")
        self.assertEqual((v.declaration, v.parameter), ("user", "name"))


class TestControlUnparseableTakesElse(unittest.TestCase):
    """{if} leaked raw text while {all}/{any} silently treated None as false."""

    def setUp(self):
        self.engine = Interpreter(
            [block.IfBlock(), block.AllBlock(), block.AnyBlock(), block.LooseVariableGetterBlock()]
        )

    def test_unparseable_if_returns_else(self):
        self.assertEqual(self.engine.process("{if(garbage):yes|no}").body, "no")

    def test_unparseable_all_returns_else(self):
        self.assertEqual(self.engine.process("{all(garbage):yes|no}").body, "no")

    def test_true_and_false_still_work(self):
        self.assertEqual(self.engine.process("{if(1==1):yes|no}").body, "yes")
        self.assertEqual(self.engine.process("{if(1==2):yes|no}").body, "no")

    def test_extra_pipes_pass_the_whole_payload(self):
        # Not a two-arm payload, so it is not split: handed over whole on true,
        # dropped on false. See TestConditionalEmbedFieldIdiom for why.
        self.assertEqual(self.engine.process("{if(1==1):then|else|c}").body, "then|else|c")
        self.assertEqual(self.engine.process("{if(1==2):then|else|c}").body, "")

    def test_multi_statement_parameter_unaffected(self):
        self.assertEqual(self.engine.process("{all(1==1|2==2):yes|no}").body, "yes")
        self.assertEqual(self.engine.process("{all(1==1|2==3):yes|no}").body, "no")
        self.assertEqual(self.engine.process("{any(1==2|2==2):yes|no}").body, "yes")

    def test_argument_with_paren_takes_else(self):
        # The reported case: user input containing an unbalanced paren used to
        # corrupt the enclosing verb so no block accepted it at all. Escaping
        # the seed adapter keeps the verb intact and the else branch is taken.
        seed = {"args": StringAdapter("(", escape=True)}
        self.assertEqual(self.engine.process("{if({args}==1):yes|no}", seed).body, "no")


class TestStrictGetterSurvivesVerbRewrite(unittest.TestCase):
    """A digit-named variable made {1} raise ProcessError when `args` was unset.

    ShortCutRedirectBlock rewrites `{1}` into `{args(1)}` during process, but the
    acceptor list was fixed from the original declaration - so the strict getter
    had already approved `1` and then looked up `args`, which need not exist.
    Reachable as `[p]tag run {=(1):x}{1}`, which seeds no `args`.
    """

    def setUp(self):
        self.blocks = [
            block.AssignmentBlock(),
            block.FiftyFiftyBlock(),
            block.ShortCutRedirectBlock("args"),
            block.LooseVariableGetterBlock(),
            block.StrictVariableGetterBlock(),
        ]

    def run_script(self, script, seed=None):
        return Interpreter(self.blocks).process(script, seed or {}).body

    def test_digit_variable_without_args_does_not_crash(self):
        for script in ("{=(1):x}{1}", "{=(50):x}{50}", "{=(5050):x}{5050}"):
            with self.subTest(script=script):
                # The shortcut still wins - the variable is simply unreachable -
                # but an unresolved verb is left as text, not raised.
                self.assertEqual(self.run_script(script), script[script.index("}") + 1 :])

    def test_shortcut_still_resolves_when_args_exists(self):
        seed = {"args": StringAdapter("Coolaid is setting up the table.")}
        self.assertEqual(self.run_script("{1}", seed), "Coolaid")
        self.assertEqual(self.run_script("{2}", seed), "is")

    def test_shortcut_resolves_against_an_assigned_args(self):
        # `args` need not be seeded - assigning it works the same way.
        script = "{=(args):Coolaid is setting up the table.}{1}|{args(1)}|{5}"
        self.assertEqual(self.run_script(script), "Coolaid|Coolaid|the")


class TestConditionalEmbedFieldIdiom(unittest.TestCase):
    """`{{if(cond):embed(field):name|value|inline}}` - a conditional embed field.

    The payload has three pipe-separated parts on purpose, so {if} must hand it
    over whole rather than treat the first `|` as its then/else separator. The
    outer braces turn the result into a real block on true, and into `{}` on
    false - which the blank variable `{=():}` renders as nothing.
    """

    SCRIPT = (
        "{=():}"
        "{{if({contains(|):{args(7+)}}==true):"
        "embed(field): __**Requirement**__:|> `{args(2):|}`|true}}"
    )

    def setUp(self):
        self.engine = Interpreter(
            [
                block.IfBlock(),
                block.AssignmentBlock(),
                block.PythonBlock(),
                block.EmbedBlock(),
                block.LooseVariableGetterBlock(),
                block.StrictVariableGetterBlock(),
            ]
        )

    def run_with(self, args):
        return self.engine.process(self.SCRIPT, {"args": StringAdapter(args)})

    def test_condition_false_renders_nothing(self):
        response = self.run_with("")
        self.assertEqual(response.body, "")
        self.assertNotIn("embed", response.actions)

    def test_condition_true_builds_the_field(self):
        response = self.run_with("a b c d e f | da")
        self.assertEqual(response.body, "")
        embed = response.actions["embed"]
        self.assertEqual(len(embed.fields), 1)
        field = embed.fields[0]
        self.assertEqual(field.name, " __**Requirement**__:")
        self.assertEqual(field.value, "> ` da`")
        self.assertIs(field.inline, True)


class TestCaseBlocksConsumeWithoutParameter(unittest.TestCase):
    """{upper}/{lower} briefly declined a bare block so a same-named variable
    could win. That leaked the raw `{upper}` whenever no such variable existed,
    which is the common case - consuming it is the lesser evil."""

    def setUp(self):
        self.engine = Interpreter(
            [
                block.MathBlock(),
                block.UpperBlock(),
                block.LowerBlock(),
                block.AssignmentBlock(),
                block.LooseVariableGetterBlock(),
            ]
        )

    def test_bare_block_never_leaks(self):
        self.assertEqual(self.engine.process("{upper}").body, "")
        self.assertEqual(self.engine.process("{lower}").body, "")

    def test_bare_block_wins_over_a_same_named_variable(self):
        self.assertEqual(self.engine.process("{=(upper):zzz} {upper(hi)} {upper}").body, "HI")
        self.assertEqual(self.engine.process("{=(lower):zzz} {lower(HI)} {lower}").body, "hi")

    def test_math_still_declines(self):
        # {math} takes a payload, not a parameter, so a bare {math} is a form the
        # block genuinely cannot handle and the variable is still reachable.
        self.assertEqual(self.engine.process("{=(math):zzz} {math:1+1} {math}").body, "2.0 zzz")

    def test_normal_use_unaffected(self):
        self.assertEqual(self.engine.process("{upper(hi)}").body, "HI")
        self.assertEqual(self.engine.process("{lower(HI)}").body, "hi")


class TestRepeatActionBlocksAreConsumed(unittest.TestCase):
    """A second require/blacklist/allowedmentions leaked its raw block text."""

    def test_repeat_require(self):
        engine = Interpreter([block.RequireBlock()])
        self.assertEqual(engine.process("{require(a)}{require(b)}").body, "")

    def test_repeat_blacklist(self):
        engine = Interpreter([block.BlacklistBlock()])
        self.assertEqual(engine.process("{blacklist(a)}{blacklist(b)}").body, "")

    def test_repeat_allowedmentions(self):
        engine = Interpreter([block.AllowedMentionsBlock()])
        self.assertEqual(engine.process("{allowedmentions}{allowedmentions}").body, "")

    def test_first_one_still_wins(self):
        engine = Interpreter([block.RequireBlock()])
        response = engine.process("{require(first)}{require(second)}")
        self.assertEqual(response.actions["requires"]["items"], ["first"])


class TestShortCutRedirectKeepsPayload(unittest.TestCase):
    """`{1:,}` dropped its payload, so the custom delimiter never reached the
    adapter and the value was always split on spaces."""

    def setUp(self):
        self.engine = Interpreter(
            [block.ShortCutRedirectBlock("args"), block.LooseVariableGetterBlock()]
        )

    def run_with(self, script, args):
        return self.engine.process(script, {"args": StringAdapter(args)}).body

    def test_default_space_delimiter(self):
        self.assertEqual(self.run_with("{1}", "hello world"), "hello")
        self.assertEqual(self.run_with("{2}", "hello world"), "world")

    def test_custom_delimiter_survives(self):
        self.assertEqual(self.run_with("{2:,}", "a,b,c"), "b")
        self.assertEqual(self.run_with("{3:,}", "a,b,c"), "c")

    def test_blank_verb_state_is_initialised(self):
        # ShortCutRedirectBlock builds a bare Verb(); touching its parse state
        # used to raise AttributeError.
        verb = Verb()
        self.assertEqual(verb.parsed_string, "")
        self.assertEqual(verb.dec_depth, 0)
        self.assertIsNone(verb.dec_start)
        self.assertFalse(verb.skip_next)


class TestSimpleAdapterDefaults(unittest.TestCase):
    """Base attributes were applied *after* update_attributes(), so a subclass
    could not override them."""

    def test_subclass_can_override_a_default(self):
        from TagScriptEngine.interface import SimpleAdapter

        class Overriding(SimpleAdapter):
            def update_attributes(self):
                self._attributes["name"] = "subclass"

            def get_value(self, ctx):
                return self._attributes.get(ctx.parameter)

        adapter = Overriding(base=object(), defaults={"name": "base", "id": 1})
        self.assertEqual(adapter._attributes["name"], "subclass")
        self.assertEqual(adapter._attributes["id"], 1)


class TestSlotsAreEffective(unittest.TestCase):
    """The `_X(Protocol)` bases gave every "slotted" class a __dict__ anyway."""

    def test_core_classes_have_no_dict(self):
        from TagScriptEngine import IntAdapter, Node, Response, StringAdapter

        for obj in (Verb("{a}"), Node((0, 2)), Response(), StringAdapter("x"), IntAdapter(1)):
            self.assertFalse(hasattr(obj, "__dict__"), type(obj).__name__)

    def test_undeclared_attribute_is_rejected(self):
        with self.assertRaises(AttributeError):
            Verb("{a}").nonsense = 1

    def test_protocol_twins_are_gone(self):
        from TagScriptEngine import interpreter, verb

        for module, name in [
            (interpreter, "_Interpreter"),
            (interpreter, "_Node"),
            (interpreter, "_Response"),
            (interpreter, "_Context"),
            (verb, "_Verb"),
        ]:
            self.assertFalse(hasattr(module, name), name)


class TestAdapterMissingValue(unittest.TestCase):
    """Absent attributes rendered as None (raw leak), False, or prose."""

    def setUp(self):
        from TagScriptEngine.interface import SimpleAdapter

        class Sample(SimpleAdapter):
            def update_attributes(self):
                self._attributes.update({"present": "yes", "empty": "", "nothing": None})

        self.adapter = Sample(base="OBJ")

    def test_known_attribute(self):
        self.assertEqual(self.adapter.get_value(Verb("{x(present)}")), "yes")

    def test_unknown_attribute_is_empty_not_none(self):
        # None would leave the block unresolved, leaking the raw tagscript.
        self.assertEqual(self.adapter.get_value(Verb("{x(bogus)}")), "")

    def test_none_valued_attribute_is_empty(self):
        self.assertEqual(self.adapter.get_value(Verb("{x(nothing)}")), "")

    def test_no_parameter_uses_default(self):
        self.assertEqual(self.adapter.get_value(Verb("{x}")), "OBJ")

    def test_methods_are_resolved(self):
        from TagScriptEngine.interface import SimpleAdapter

        class WithMethod(SimpleAdapter):
            def update_methods(self):
                self._methods["calls"] = lambda: 42

        self.assertEqual(WithMethod(base="o").get_value(Verb("{x(calls)}")), "42")


class TestRangeFloatBounds(unittest.TestCase):
    """{rangef} truncated its bounds with int(x)*10, dropping the decimals."""

    def setUp(self):
        self.engine = Interpreter([block.RangeBlock()])

    def test_float_bounds_are_respected(self):
        seen = {float(self.engine.process("{rangef:5.5-7.5}").body) for _ in range(200)}
        self.assertGreaterEqual(min(seen), 5.5)
        self.assertLessEqual(max(seen), 7.5)

    def test_integer_range_unaffected(self):
        seen = {int(self.engine.process("{range:1-10}").body) for _ in range(200)}
        self.assertGreaterEqual(min(seen), 1)
        self.assertLessEqual(max(seen), 10)


class TestEmbedFieldErrorShowsValue(unittest.TestCase):
    """The error printed the Python variable name instead of the bad value."""

    def test_bad_inline_value_is_named(self):
        engine = Interpreter([block.EmbedBlock()])
        body = engine.process("{embed(field):a|b|notabool}").body
        self.assertIn("notabool", body)
        self.assertNotIn("_inline", body)


class TestWorkloadCeiling(unittest.TestCase):
    """charlimit was never passed by the host, so this guard was unreachable."""

    def setUp(self):
        self.engine = Interpreter([block.AssignmentBlock(), block.LooseVariableGetterBlock()])
        self.build = (
            "{=(a):0123456789}{=(b):" + "{a}" * 10 + "}"
            "{=(c):" + "{b}" * 10 + "}{=(d):" + "{c}" * 5 + "}"
        )

    def test_amplifier_is_refused(self):
        from TagScriptEngine import WorkloadExceededError

        with self.assertRaises(WorkloadExceededError):
            self.engine.process(self.build + "{d}" * 600, charlimit=100_000)

    def test_ordinary_tag_is_unaffected(self):
        body = self.engine.process("Hello {=(n):world}{n}!", charlimit=100_000).body
        self.assertEqual(body, "Hello world!")

    def test_no_charlimit_still_unbounded(self):
        # Passing no charlimit keeps the old behaviour, so the ceiling is opt-in.
        self.assertIsNotNone(self.engine.process(self.build + "{d}" * 100).body)


class TestLengthBlockAlwaysHasParameter(unittest.TestCase):
    """The `else "-1"` branch was unreachable."""

    def test_length(self):
        engine = Interpreter([block.LengthBlock()])
        self.assertEqual(engine.process("{len(hello)}").body, "5")
        self.assertEqual(engine.process("{length(hello world)}").body, "11")

    def test_empty_parameter_declines(self):
        engine = Interpreter([block.LengthBlock()])
        self.assertEqual(engine.process("{len()}").body, "{len()}")


class TestCooldownValidationAndEviction(unittest.TestCase):
    """Cooldown accepted nan/inf/negative windows, and evicted by insertion
    order so 1024 cold tags could flush a hot rate limit."""

    def setUp(self):
        block.CooldownBlock.COOLDOWNS.clear()
        self.engine = Interpreter([block.CooldownBlock()])

    def tearDown(self):
        block.CooldownBlock.COOLDOWNS.clear()

    def test_rejects_non_finite_and_negative(self):
        for script in (
            "{cooldown(1|nan):k}",
            "{cooldown(1|inf):k}",
            "{cooldown(1|-5):k}",
            "{cooldown(0|10):k}",
        ):
            self.assertIn("cooldown error", self.engine.process(script).body, script)

    def test_valid_cooldown_still_works(self):
        self.assertEqual(self.engine.process("{cooldown(1|10):k}").body, "")

    def test_eviction_is_least_recently_used(self):
        cd = block.CooldownBlock
        cd.create_cooldown("hot", 1, 10.0)
        for i in range(cd.MAX_COOLDOWNS - 1):
            cd.create_cooldown(f"cold-{i}", 1, 10.0)
        # Touch "hot" so it becomes the most recently used, then overflow.
        cd.COOLDOWNS.move_to_end("hot")
        for i in range(10):
            cd.create_cooldown(f"later-{i}", 1, 10.0)
        self.assertIn("hot", cd.COOLDOWNS)
        self.assertLessEqual(len(cd.COOLDOWNS), cd.MAX_COOLDOWNS)


class TestWarningsDeadCodeRemoved(unittest.TestCase):
    def test_removal_helpers_are_gone(self):
        from TagScriptEngine import _warnings

        for name in ("TagScriptEngineAttributeRemovalWarning", "remove", "removal", "depricate"):
            self.assertFalse(hasattr(_warnings, name), name)

    def test_deprecation_warning_still_exported(self):
        import TagScriptEngine as tse

        self.assertTrue(hasattr(tse, "TagScriptEngineDeprecationWarning"))


class TestActionBlocksNeverEchoRawTagscript(unittest.TestCase):
    """process() returning None means "not handled", so the literal
    {block(...)} survived into the message. Action blocks must consume."""

    def run_with(self, blocks, script):
        return Interpreter(blocks).process(script).body

    def test_override_consumes_every_form(self):
        body = self.run_with(
            [block.OverrideBlock()],
            "hi {override} hi {override(x)} hi {override()} hi {override:} hi {override:x}",
        )
        self.assertEqual(body, "hi  hi  hi  hi  hi")

    def test_sleep_consumes_bare_forms(self):
        body = self.run_with(
            [block.SleepBlock()], "hi {sleep} {sleep()} {sleep(x)} {sleep:} {sleep:x}"
        )
        self.assertNotIn("{sleep}", body)
        self.assertNotIn("{sleep()}", body)
        self.assertEqual(body.count("Sleep Parse Error"), 2)

    def test_embed_consumes_every_form(self):
        body = self.run_with(
            [block.EmbedBlock()],
            "hi {embed(bogus):x} {embed} {embed()} {embed(x)} {embed:} "
            "{embed:x} {embed(title)}, {embed(color)}",
        )
        self.assertNotIn("{embed", body)

    def test_empty_embed_is_not_registered(self):
        # A registered empty embed made the host send a message Discord drops,
        # so the whole tag output vanished.
        response = Interpreter([block.EmbedBlock()]).process("hi {embed}")
        self.assertNotIn("embed", response.actions)
        self.assertEqual(response.body, "hi")

    def test_embed_with_content_still_registers(self):
        response = Interpreter([block.EmbedBlock()]).process("{embed(title):Hello}")
        self.assertIn("embed", response.actions)
        self.assertEqual(response.actions["embed"].title, "Hello")

    def test_non_text_only_embed_still_registers(self):
        # len() counts text only, so these looked empty and were dropped.
        for script in ("{embed(color):red}", "{embed(url):https://x/}"):
            self.assertIn("embed", Interpreter([block.EmbedBlock()]).process(script).actions)

    def test_colour_set_before_any_text_survives(self):
        # The embed is built across several blocks; one that is not registered is
        # one the next block cannot add to, so a colour-first embed lost it.
        response = Interpreter([block.EmbedBlock()]).process(
            "{embed(color):red}{embed(description):hi}"
        )
        embed = response.actions["embed"]
        self.assertEqual(embed.description, "hi")
        self.assertIsNotNone(embed.colour)

    def test_component_consumes_every_form(self):
        body = self.run_with(
            [block.ComponentBlock()],
            "hi {component(text)}, {component(image)}, {component(thumbnail)}, {component(color)}",
        )
        self.assertNotIn("{component", body)

    def test_list_out_of_bounds_renders_empty(self):
        self.assertEqual(self.run_with([block.ListBlock()], "hi {list(99):90,105}"), "hi")

    def test_ordinal_and_replace_report_errors(self):
        self.assertIn("Ordinal Error", self.run_with([block.OrdinalBlock()], "{ord:abc}"))
        self.assertIn(
            "Replace Error", self.run_with([block.ReplaceBlock()], "{replace(noComma):x}")
        )


class TestRangeAcceptsReversedBounds(unittest.TestCase):
    def setUp(self):
        self.engine = Interpreter([block.RangeBlock()])

    def test_reversed_range_is_sorted(self):
        seen = {int(self.engine.process("{range:10-1}").body) for _ in range(60)}
        self.assertGreaterEqual(min(seen), 1)
        self.assertLessEqual(max(seen), 10)

    def test_reversed_float_range(self):
        seen = {float(self.engine.process("{rangef:7.5-5.5}").body) for _ in range(60)}
        self.assertGreaterEqual(min(seen), 5.5)
        self.assertLessEqual(max(seen), 7.5)

    def test_unparseable_range_still_echoes(self):
        self.assertEqual(self.engine.process("{range:abc}").body, "{range:abc}")


class TestValueBlocksStillEcho(unittest.TestCase):
    """Deliberate: for value blocks, echoing the block IS the error signal, and
    it is what lets a variable of that name resolve. Do not 'fix' these."""

    def assert_unchanged(self, blocks, script):
        self.assertEqual(Interpreter(blocks).process(script).body, script)

    def test_math(self):
        self.assert_unchanged([block.MathBlock()], "hi {math} {math:x} {math(x)} {math()}")
        self.assert_unchanged([block.MathBlock()], "hi {math:abc} {math} {math:}")

    def test_strf(self):
        self.assert_unchanged([block.StrfBlock()], "hi {strf(abc):%Y} {strf}")

    def test_substring(self):
        self.assert_unchanged(
            [block.SubstringBlock()],
            "hi {substr(abc):hello} {substr} {substr(x)} {substr(2)} {substr:} {substr:x}",
        )

    def test_bare_name_still_falls_through_to_a_variable(self):
        engine = Interpreter(
            [block.MathBlock(), block.AssignmentBlock(), block.LooseVariableGetterBlock()]
        )
        self.assertEqual(engine.process("{=(math):zzz} {math:1+1} {math}").body, "2.0 zzz")


class TestAllowedMentionsMerged(unittest.TestCase):
    """The cog kept a near-identical copy of this block and registered that one,
    so fixing the engine's copy alone left the bug live. Now single-sourced."""

    def setUp(self):
        self.engine = Interpreter([block.AllowedMentionsBlock()])

    def test_all_three_aliases(self):
        # `allowedmention` was only in the cog's copy before the merge.
        for script in ("{allowedmentions}", "{allowedmention}", "{mentions}"):
            response = self.engine.process(script)
            self.assertEqual(response.body, "", script)
            self.assertEqual(
                response.actions["allowed_mentions"], {"mentions": True, "override": False}
            )

    def test_override_payload(self):
        response = self.engine.process("{allowedmention:override}")
        self.assertTrue(response.actions["allowed_mentions"]["override"])

    def test_role_scoping(self):
        response = self.engine.process("{allowedmentions(@Admin, Moderator):override}")
        self.assertEqual(response.actions["allowed_mentions"]["mentions"], ["@Admin", "Moderator"])

    def test_repeat_is_consumed_and_first_wins(self):
        response = self.engine.process("{allowedmentions(A)}{allowedmentions(B)}")
        self.assertEqual(response.body, "")
        self.assertEqual(response.actions["allowed_mentions"]["mentions"], ["A"])

    def test_unknown_payload_still_declines(self):
        # will_accept rejects it, so the block never runs and the text passes
        # through - that is the designed behaviour, not a leak.
        self.assertEqual(
            self.engine.process("{allowedmentions:bogus}").body, "{allowedmentions:bogus}"
        )


class TestEmbedFieldTruncation(unittest.TestCase):
    """
    A field over BOTH per-field limits used to raise ProcessError: the first
    set_field_at replaced the field, so the second embed.fields.index(field)
    lookup for the same (now stale) proxy raised ValueError.
    """

    def setUp(self):
        self.engine = Interpreter([block.EmbedBlock()])

    def _field(self, name, value, inline=False):
        script = '{embed({"fields":[%s]})}' % json.dumps(
            {"name": name, "value": value, "inline": inline}
        )
        response = self.engine.process(script)
        return response.actions["embed"].fields[0]

    def test_over_both_limits_does_not_crash(self):
        field = self._field("N" * 300, "V" * 2000)
        self.assertEqual(len(field.name), 256)
        self.assertEqual(len(field.value), 1024)

    def test_over_name_only_leaves_value_alone(self):
        field = self._field("N" * 300, "ok")
        self.assertEqual(len(field.name), 256)
        self.assertEqual(field.value, "ok")

    def test_over_value_only_leaves_name_alone(self):
        field = self._field("ok", "V" * 2000)
        self.assertEqual(field.name, "ok")
        self.assertEqual(len(field.value), 1024)

    def test_within_limits_untouched(self):
        field = self._field("name", "value", inline=True)
        self.assertEqual((field.name, field.value, field.inline), ("name", "value", True))

    def test_every_over_limit_field_is_truncated(self):
        # .index() matched by value, so two identical over-limit fields both
        # resolved to index 0 and the second was left over the limit.
        script = '{embed({"fields":[%s,%s]})}' % (
            json.dumps({"name": "N" * 300, "value": "V" * 2000, "inline": False}),
            json.dumps({"name": "N" * 300, "value": "V" * 2000, "inline": False}),
        )
        fields = self.engine.process(script).actions["embed"].fields
        self.assertEqual([(len(f.name), len(f.value)) for f in fields], [(256, 1024)] * 2)


class TestMathBlockRealResultsOnly(unittest.TestCase):
    """
    A fractional exponent on a negative base returned a Python complex, whose
    repr leaked into the message. It now declines, like {math:sqrt(-1)}.
    """

    def setUp(self):
        self.engine = Interpreter([block.MathBlock()])

    def test_complex_result_declines(self):
        for script in ("{math:(0-2)^0.5}", "{math:sqrt(-1)}"):
            self.assertEqual(self.engine.process(script).body, script)

    def test_real_powers_still_work(self):
        self.assertAlmostEqual(float(self.engine.process("{math:2^0.5}").body), 2**0.5)
        self.assertEqual(float(self.engine.process("{math:2^10}").body), 1024)
        self.assertAlmostEqual(float(self.engine.process("{math:(0-2)^3}").body), -8)

    def test_wide_int_result_does_not_raise(self):
        # math.isfinite() converts to float, so an int past ~1.8e308 raised
        # OverflowError out of process(). int**int stays exact, and
        # round()/trunc() feed the pow ints, so this is reachable from a tag.
        self.assertEqual(self.engine.process("{math:round(10)^round(400)}").body, "1" + "0" * 400)


class TestHelperSplitEscapedDelimiter(unittest.TestCase):
    """
    Pins the escaped-delimiter behaviour as intended, not a bug. An escaped `|`
    is a literal, so it neither splits nor falls through to `~` - a payload that
    escaped its only delimiter simply has no split, and callers that need 2-3
    parts raise their own parse error. Do not "fix" this into a tilde fallback.
    """

    def test_escaped_only_pipe_does_not_split(self):
        self.assertEqual(helper_split(r"a\|b"), [r"a\|b"])

    def test_escaped_pipe_does_not_fall_through_to_tilde(self):
        self.assertEqual(helper_split(r"a\|b~c"), [r"a\|b~c"])

    def test_unescaped_pipe_still_splits(self):
        self.assertEqual(helper_split("a|b"), ["a", "b"])

    def test_escaped_pipe_alongside_a_real_pipe_splits_on_the_real_one(self):
        self.assertEqual(helper_split(r"a\|b|c"), [r"a\|b", "c"])


if __name__ == "__main__":
    unittest.main()
