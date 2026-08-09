import unittest
from typing import Any, Dict, List

import discord

import TagScriptEngine as tse
from TagScriptEngine import Interpreter, block
from TagScriptEngine.block.component import (
    MAX_COMPONENTS,
    MAX_MEDIA_ITEMS,
    TEXT_LIMIT,
    build_components_v2_view,
)


class TestComponentBlock(unittest.TestCase):
    def setUp(self):
        self.blocks: List[tse.Block] = [block.ComponentBlock()]
        self.engine: Interpreter = Interpreter(self.blocks)

    def tearDown(self):
        self.blocks: List[tse.Block] = None  # type: ignore
        self.engine: Interpreter = None  # type: ignore

    def layout(self, script: str) -> Dict[str, Any]:
        return self.engine.process(script).actions["components_v2"]

    # -- acceptance --------------------------------------------------------

    def test_aliases(self):
        for name in ("component", "cv2", "c2"):
            layout = self.layout("{%s(text):hi}" % name)
            self.assertEqual(layout["items"], [{"type": "text", "content": "hi"}])

    def test_unknown_attribute_is_not_accepted(self):
        # will_accept gates on the parameter, so an unknown one passes through
        # literally and never creates a layout.
        response = self.engine.process("{component(bogus):x}")
        self.assertEqual(response.body, "{component(bogus):x}")
        self.assertNotIn("components_v2", response.actions)

    def test_bare_component_is_not_accepted(self):
        response = self.engine.process("{component}")
        self.assertEqual(response.body, "{component}")
        self.assertNotIn("components_v2", response.actions)

    # -- layout accumulation -----------------------------------------------

    def test_items_accumulate_in_order(self):
        layout = self.layout(
            "{component(text):first}{component(separator)}{component(text):second}"
        )
        self.assertEqual(
            layout["items"],
            [
                {"type": "text", "content": "first"},
                {"type": "separator", "visible": True, "large": False},
                {"type": "text", "content": "second"},
            ],
        )

    def test_separator_keywords(self):
        for keyword, expected in (
            ("", (True, False)),
            ("small", (True, False)),
            ("large", (True, True)),
            ("big", (True, True)),
            ("hidden", (False, False)),
            ("invisible", (False, False)),
            ("blank", (False, False)),
        ):
            script = (
                "{component(separator)}" if not keyword else "{component(separator):%s}" % keyword
            )
            item = self.layout(script)["items"][0]
            self.assertEqual((item["visible"], item["large"]), expected, keyword)

    def test_thumbnail_promotes_preceding_text_to_section(self):
        layout = self.layout("{component(text):body}{component(thumbnail):http://e.com/t.png}")
        self.assertEqual(
            layout["items"],
            [{"type": "section", "content": "body", "thumbnail": "http://e.com/t.png"}],
        )

    def test_thumbnail_without_text_creates_empty_section(self):
        layout = self.layout("{component(thumbnail):http://e.com/t.png}")
        self.assertEqual(
            layout["items"],
            [{"type": "section", "content": "", "thumbnail": "http://e.com/t.png"}],
        )

    def test_images_coalesce_into_one_gallery(self):
        layout = self.layout(
            "{component(image):http://e.com/1.png}{component(image):http://e.com/2.png}"
        )
        self.assertEqual(
            layout["items"],
            [{"type": "gallery", "urls": ["http://e.com/1.png", "http://e.com/2.png"]}],
        )

    def test_images_split_on_double_semicolon(self):
        layout = self.layout("{component(image):http://e.com/1.png;;http://e.com/2.png}")
        self.assertEqual(layout["items"][0]["urls"], ["http://e.com/1.png", "http://e.com/2.png"])

    def test_image_does_not_coalesce_across_other_items(self):
        # A gallery only absorbs images when it is the most recent item, so
        # document order is preserved.
        layout = self.layout(
            "{component(image):http://e.com/1.png}"
            "{component(text):between}"
            "{component(image):http://e.com/2.png}"
        )
        self.assertEqual(
            [item["type"] for item in layout["items"]], ["gallery", "text", "gallery"]
        )

    # -- framing -----------------------------------------------------------

    def test_container_aliases_set_framed(self):
        for name in ("container", "box", "frame"):
            layout = self.layout("{component(%s)}" % name)
            self.assertTrue(layout["framed"], name)
            self.assertIsNone(layout["accent_color"])

    def test_container_accepts_colour_payload(self):
        layout = self.layout("{component(container):#5865F2}")
        self.assertTrue(layout["framed"])
        self.assertEqual(layout["accent_color"], 0x5865F2)

    def test_colour_implies_framed(self):
        layout = self.layout("{component(color):#5865F2}")
        self.assertTrue(layout["framed"])
        self.assertEqual(layout["accent_color"], 0x5865F2)

    def test_layout_defaults_unframed(self):
        layout = self.layout("{component(text):plain}")
        self.assertFalse(layout["framed"])
        self.assertIsNone(layout["accent_color"])

    # -- colour parsing ----------------------------------------------------

    def test_colour_hex_forms(self):
        for payload in ("#5865F2", "0x5865F2", "5865F2", "5865f2", "  #5865F2  "):
            self.assertEqual(
                self.layout("{component(color):%s}" % payload)["accent_color"], 0x5865F2
            )

    def test_colour_named(self):
        # Parity with the embed block: any non-`from_*` discord.Colour
        # classmethod resolves, so this tracks discord.py rather than a list.
        self.assertEqual(
            self.layout("{component(color):red}")["accent_color"], discord.Colour.red().value
        )
        self.assertEqual(
            self.layout("{component(color):blurple}")["accent_color"],
            discord.Colour.blurple().value,
        )

    def test_colour_named_with_space(self):
        self.assertEqual(
            self.layout("{component(color):dark blue}")["accent_color"],
            discord.Colour.dark_blue().value,
        )

    def test_colour_invalid_returns_error(self):
        for payload in ("nonsense", "#zzzzzz", "from_rgb"):
            response = self.engine.process("{component(color):%s}" % payload)
            self.assertTrue(
                response.body.startswith("Component Parse Error:"), (payload, response.body)
            )

    def test_colour_out_of_range_returns_error(self):
        response = self.engine.process("{component(color):1000000}")
        self.assertTrue(response.body.startswith("Component Parse Error:"))

    def test_failed_container_colour_does_not_frame(self):
        response = self.engine.process("{component(container):nonsense}")
        self.assertTrue(response.body.startswith("Component Parse Error:"))
        self.assertFalse(response.actions["components_v2"]["framed"])

    def test_empty_colour_payload_is_ignored(self):
        # A no-op, but consumed: it was asserted to echo "{component(color)}",
        # which leaked raw tagscript into the message.
        response = self.engine.process("{component(color)}")
        self.assertEqual(response.body, "")

    # -- limits ------------------------------------------------------------

    def test_text_limit(self):
        script = "{component(text):%s}" % ("a" * (TEXT_LIMIT - 1))
        script += "{component(text):bb}"
        response = self.engine.process(script)
        self.assertIn("MAX COMPONENT TEXT LENGTH REACHED (%d)" % TEXT_LIMIT, response.body)
        # The over-limit block is rejected, the under-limit one is kept.
        self.assertEqual(len(response.actions["components_v2"]["items"]), 1)

    def test_component_limit(self):
        # One slot of the 40 is reserved for folded-in plain output.
        script = "{component(text):x}" * (MAX_COMPONENTS - 1)
        script += "{component(text):overflow}"
        response = self.engine.process(script)
        self.assertIn("MAX COMPONENT COUNT REACHED (%d)" % MAX_COMPONENTS, response.body)
        self.assertEqual(len(response.actions["components_v2"]["items"]), MAX_COMPONENTS - 1)

    def test_media_item_limit(self):
        urls = ";;".join("http://e.com/%d.png" % i for i in range(MAX_MEDIA_ITEMS + 1))
        response = self.engine.process("{component(image):%s}" % urls)
        self.assertIn("MAX MEDIA GALLERY ITEMS REACHED (%d)" % MAX_MEDIA_ITEMS, response.body)
        self.assertEqual(
            len(response.actions["components_v2"]["items"][0]["urls"]), MAX_MEDIA_ITEMS
        )


class TestBuildComponentsV2View(unittest.TestCase):
    def setUp(self):
        self.engine: Interpreter = Interpreter([block.ComponentBlock()])

    def layout(self, script: str) -> Dict[str, Any]:
        return self.engine.process(script).actions["components_v2"]

    def test_child_types(self):
        layout = self.layout(
            "{component(text):hello}"
            "{component(separator):large}"
            "{component(text):section}{component(thumbnail):http://e.com/t.png}"
            "{component(image):http://e.com/1.png}"
        )
        view = build_components_v2_view(layout)
        self.assertIsInstance(view, discord.ui.LayoutView)
        self.assertEqual(
            [type(child) for child in view.children],
            [
                discord.ui.TextDisplay,
                discord.ui.Separator,
                discord.ui.Section,
                discord.ui.MediaGallery,
            ],
        )

    def test_unframed_layout_has_no_container(self):
        view = build_components_v2_view(self.layout("{component(text):plain}"))
        self.assertEqual([type(child) for child in view.children], [discord.ui.TextDisplay])

    def test_framed_layout_wraps_in_container(self):
        view = build_components_v2_view(self.layout("{component(box)}{component(text):x}"))
        self.assertEqual(len(view.children), 1)
        container = view.children[0]
        self.assertIsInstance(container, discord.ui.Container)
        self.assertEqual([type(child) for child in container.children], [discord.ui.TextDisplay])

    def test_accent_colour_applied_to_container(self):
        # Container takes Optional[Union[Colour, int]] and stores it as passed,
        # so the raw int the layout carries comes back out unchanged.
        view = build_components_v2_view(self.layout("{component(color):red}{component(text):x}"))
        container = view.children[0]
        self.assertEqual(container.accent_colour, discord.Colour.red().value)

    def test_leading_content_folded_in_first(self):
        view = build_components_v2_view(self.layout("{component(text):body}"), "leading")
        self.assertEqual([child.content for child in view.children], ["leading", "body"])

    def test_leading_content_trimmed_to_remaining_budget(self):
        layout = self.layout("{component(text):%s}" % ("a" * (TEXT_LIMIT - 10)))
        view = build_components_v2_view(layout, "b" * 100)
        leading = view.children[0].content
        self.assertEqual(len(leading), 10)
        self.assertTrue(leading.endswith("…"))

    def test_leading_content_dropped_when_no_budget(self):
        layout = self.layout("{component(text):%s}" % ("a" * TEXT_LIMIT))
        view = build_components_v2_view(layout, "dropped")
        self.assertEqual([child.content for child in view.children], ["a" * TEXT_LIMIT])

    def test_empty_layout_yields_zero_width_text(self):
        view = build_components_v2_view({"framed": False, "accent_color": None, "items": []})
        self.assertEqual([child.content for child in view.children], ["​"])


if __name__ == "__main__":
    unittest.main()
