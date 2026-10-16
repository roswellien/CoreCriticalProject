"""Asset-free guards for the narrowly pinned codec timing rewrite."""
import unittest

import codec_timing


class CodecTimingGuards(unittest.TestCase):
    def test_unrelated_module_is_unchanged(self):
        text = 'define void @authored_fixture() {\r\n  ret void\r\n}\r\n'
        actual, stats = codec_timing.transform(text)
        self.assertEqual(actual, text)
        self.assertEqual(stats['codec_timing_preserved'], 0)

    def test_declaration_alone_is_not_a_body(self):
        text = 'declare ptr @mw34_attach_m_1103ab10_body(ptr, i32, ptr)\n'
        self.assertEqual(codec_timing.transform(text)[0], text)

    def test_changed_known_body_fails_instead_of_guessing(self):
        text = 'define ptr @mw34_attach_m_1103ab10_body(ptr %s, i32 %pc, ptr %m) {\n  ret ptr %m\n}\n'
        with self.assertRaisesRegex(ValueError, 'complete pinned host IR'):
            codec_timing.transform(text)


if __name__ == '__main__':
    unittest.main()
