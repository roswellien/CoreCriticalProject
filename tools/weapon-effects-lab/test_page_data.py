"""Asset-free regressions for the lab's HTML/JSON transport boundary."""

import unittest

from page_data import append_page_script, fill_page_data, read_page_data


class PageDataTests(unittest.TestCase):
    def test_formatted_blocks_round_trip_and_keep_bridge_out_of_json(self):
        payload = {"text": '</script><script>alert("&amp;")</script>', "nested": [None, 3]}
        for opening in (
            '<script type="application/json" id="lab-data">',
            "<script\n id = 'lab-data'\n type = 'application/json'\n>",
        ):
            with self.subTest(opening=opening):
                template = (
                    opening
                    + '\n null\n</script>\n<script id="lab-script">\nconst x = 1;\n</script>'
                )
                built = fill_page_data(template, payload)
                self.assertIn(r"\u003c/script>", built)
                self.assertEqual(read_page_data(built), payload)
                bridged = append_page_script(built, "\nwindow.bridge = true;\n")
                self.assertEqual(read_page_data(bridged), payload)
                self.assertIn("const x = 1;\n\nwindow.bridge = true;\n</script>", bridged)

    def test_reject_missing_duplicate_unclosed_or_wrong_type_blocks(self):
        block = '<script id="lab-data" type="application/json">null</script>'
        for html in (
            "<html></html>",
            block + block,
            block + '<script id="lab-data" type="application/json">null',
            '<script id="lab-data">null</script>',
            '<div id="lab-data">null</div>',
        ):
            for operation in (read_page_data, lambda html: fill_page_data(html, {})):
                with self.subTest(html=html, operation=operation), self.assertRaises(ValueError):
                    operation(html)
        with self.assertRaises(ValueError):
            fill_page_data(block, {"invalid": float("nan")})


if __name__ == "__main__":
    unittest.main()
