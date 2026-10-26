import struct
import unittest

from zrd_document import decode, encode


class ReaderDocumentTests(unittest.TestCase):
    def test_independent_typed_fixture_and_empty_list(self):
        # List count 5 encodes four children, without a terminator. Preserve the
        # integer and float node types even when both values are numerically 1.
        blob = bytes.fromhex(
            '0400000005000000'
            '03000000030000006d6563'
            '0100000001000000'
            '020000000000803f'
            '0400000001000000')
        self.assertEqual(decode(blob), ['mec', 1, 1.0, None])
        self.assertEqual(encode(['mec', 1, 1.0, None]), blob)
        self.assertIs(type(decode(blob)[1]), int)
        self.assertIs(type(decode(blob)[2]), float)

    def test_signed_boundaries_and_single_byte_text(self):
        doc = [-2147483648, 2147483647, 'caf\xe9', '', [-0.0]]
        self.assertEqual(encode(decode(encode(doc))), encode(doc))

    def test_truncation_and_trailing_bytes(self):
        data = encode(['definition', ['mass', [75.0]]])
        for end in range(len(data)):
            with self.assertRaises(ValueError):
                decode(data[:end])
        with self.assertRaises(ValueError):
            decode(data + b'\0')

    def test_bad_type_and_counts(self):
        for data in (struct.pack('<II', 0, 0), struct.pack('<II', 4, 0),
                     struct.pack('<II', 4, 0xffffffff), struct.pack('<II', 3, 0xffffffff)):
            with self.assertRaises(ValueError):
                decode(data)

    def test_reject_unrepresentable_values(self):
        for value in (True, {}, 2**31, -(2**31)-1, float('nan'), float('inf'), 1e100, 'a\0b', '\u2603'):
            with self.assertRaises(ValueError):
                encode(value)
        with self.assertRaises(ValueError):
            decode(struct.pack('<If', 2, float('nan')))

    def test_depth_bound(self):
        value = None
        for _ in range(66):
            value = [value]
        with self.assertRaises(ValueError):
            encode(value)
        with self.assertRaises(ValueError):
            decode(struct.pack('<II', 4, 2) * 66 + struct.pack('<II', 4, 1))


if __name__ == '__main__':
    unittest.main()
