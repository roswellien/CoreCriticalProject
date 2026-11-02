import struct
import unittest

from chassis_catalog import encode_catalog
from reader_archive import add_definitions, _directory
from zrd_document import encode


class ChassisCatalogTests(unittest.TestCase):
    def record(self, ident='community.example:marauder', resource='maraud'):
        return dict(id=ident, name='Marauder MAD-3R', resource=resource, metadata_template='orion')

    def test_golden_wire_and_order(self):
        records = [self.record('z:one', 'one'), self.record('a:two', 'two')]
        self.assertEqual(encode_catalog(records), encode_catalog(list(reversed(records))))
        record = dict(id='a:b', name='B', resource='b', metadata_template='orion')
        self.assertEqual(encode_catalog([record]), b'MWCHAS1\0' + struct.pack('<I', 1)
                         + struct.pack('<I', 3) + b'a:b' + struct.pack('<I', 1) + b'B'
                         + struct.pack('<I', 1) + b'b' + struct.pack('<I', 10))

    def test_headlight_wire_validation_and_legacy_output(self):
        from chassis_catalog import validate_headlights
        light = dict(id='left', space='guest_node', attachment='torso', position=[1, 2, -2],
                     direction=[0, 0, -2], color=[1, .9, .8], intensity=2, range=50,
                     inner_angle=15, outer_angle=30)
        row = self.record()
        self.assertEqual(encode_catalog([row]), encode_catalog([dict(row, headlights=[])]))
        data = encode_catalog([dict(row, headlights=[light])])
        self.assertEqual(data[:8], b'MWCHAS5\0')
        self.assertEqual(struct.unpack('<13f', data[-52:])[3:6], (0, 0, -1))
        self.assertEqual(light['direction'], [0, 0, -2])
        maximum = [dict(light, id=str(i)) for i in range(8)]
        self.assertEqual(len(validate_headlights(maximum)), 8)
        invalid = [[light, light], maximum + [dict(light, id='extra')],
                   [dict(light, unknown=1)], [dict(light, space='donor_bone')]]
        for field, value in [('position', [101, 0, 0]), ('direction', [0, 0, 0]),
                             ('color', [1, -1, 0]), ('range', True), ('intensity', float('nan')),
                             ('outer_angle', 15), ('range', 10 ** 400), ('id', 'A'), ('attachment', '../torso/')]:
            invalid.append([dict(light, **{field: value})])
        for lights in invalid:
            with self.subTest(lights=lights), self.assertRaises(ValueError):
                encode_catalog([dict(row, headlights=lights)])

    def test_authored_socket_wire_and_invalid_bindings(self):
        from chassis_catalog import validate_sockets
        visual=dict(controller='madcat',close=dict(mesh='a',textures='b'),distance=dict(mesh='c',textures='d'))
        socket=dict(node='firepoint01',bone='Forearm_Right',position=[4.0,-0.01,-1.13])
        row={**self.record(), 'visuals':visual, 'sockets':[socket]}
        data=encode_catalog([row])
        self.assertEqual(data[:8],b'MWCHAS4\0')
        self.assertTrue(data.endswith(struct.pack('<3d',*socket['position'])))
        for sockets in ([],[socket,socket],[{**socket,'position':[float('nan'),0,0]}],
                        [{**socket,'bone':'bad\0bone'}],[{**socket,'node':'camera'}]):
            with self.subTest(sockets=sockets),self.assertRaises(ValueError):validate_sockets(sockets)

    def test_optional_base_skin_wire_and_bounds(self):
        old = encode_catalog([self.record()])
        actual = encode_catalog([{**self.record(), 'base_skin_name': 'Olive Drab'}])
        self.assertEqual(actual, b'MWCHAS3\0' + old[8:] + struct.pack('<II', 0, 10) + b'Olive Drab')
        for label in ('', 'x' * 65, 'bad\n', '\u754c', None):
            with self.subTest(label=label), self.assertRaises(ValueError):
                encode_catalog([{**self.record(), 'base_skin_name': label}])
        maximum = encode_catalog([{**self.record(), 'base_skin_name': 'x' * 64}])
        self.assertTrue(maximum.endswith(struct.pack('<I', 64) + b'x' * 64))
        mixed = encode_catalog([self.record(), {**self.record('z:mech', 'second'), 'base_skin_name': 'B'}])
        self.assertIn(struct.pack('<III', 10, 0, 0), mixed)

    def test_reject_collisions_and_executable_fields(self):
        for records in ([self.record(), self.record()],
                        [self.record(), self.record('other:mech')],
                        [self.record(resource='madcat')],
                        [self.record(resource='notmech')],
                        [{**self.record(), 'command': 'run.exe'}]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                encode_catalog(records)

    def test_reject_unsafe_and_unsupported_values(self):
        for field, value in [('id', 'unnamespaced'), ('resource', '../mech'),
                             ('name', 'A\nB'), ('metadata_template', 'invented'),
                             ('metadata_template', 'elemental'), ('name', '\u754c')]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                encode_catalog([{**self.record(), field: value}])

    def test_visual_wire_keeps_controller_separate_from_metadata(self):
        visual = dict(controller='madcat', close=dict(mesh='close.bin', textures='close.tex'),
                      distance=dict(mesh='far.bin', textures='far.tex'))
        old = encode_catalog([self.record()])
        actual = encode_catalog([{**self.record(), 'visuals': visual}])
        expected = b'MWCHAS2\0' + old[8:] + struct.pack('<I', 1)
        for value in ('madcat', 'close.bin', 'close.tex', 'far.bin', 'far.tex'):
            raw = value.encode()
            expected += struct.pack('<I', len(raw)) + raw
        self.assertEqual(actual, expected)
        for invalid in ({**visual, 'controller': 'unknown'},
                        {**visual, 'command': 'run.exe'},
                        {**visual, 'close': {'mesh': 'only.bin'}},
                        {**visual, 'distance': dict(mesh='bad\0path', textures='far.tex')}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                encode_catalog([{**self.record(), 'visuals': invalid}])


class ReaderOverlayTests(unittest.TestCase):
    def archive(self):
        payload = encode([['version', 2]])
        record = struct.pack('<II', 0, len(payload)) + b'dfn_madcat.zrd'.ljust(64, b'\0') + bytes(range(76))
        return payload + record + struct.pack('<II', 1, 1)

    def test_preserves_original_payload_and_record(self):
        original = self.archive()
        payload = encode([['version', 2], ['max_mass', 75.0]])
        merged = add_definitions(original, {'dfn_maraud.zrd': payload})
        old_start, old_records = _directory(original)
        _, new_records = _directory(merged)
        self.assertEqual(merged[:old_start], original[:old_start])
        self.assertEqual(new_records[0], old_records[0])
        name, offset, size, record = new_records[1]
        self.assertEqual((name, merged[offset:offset + size]), ('dfn_maraud.zrd', payload))
        self.assertEqual(record[72:], old_records[0][3][72:])

    def test_refuses_replacement_or_malformed_definition(self):
        for definitions in ({'dfn_madcat.zrd': encode(None)},
                            {'../x': encode(None)}, {'dfn_new.zrd': b'bad'}):
            with self.subTest(definitions=definitions), self.assertRaises(ValueError):
                add_definitions(self.archive(), definitions)

    def test_rejects_out_of_range_directory(self):
        original = bytearray(self.archive())
        start, _ = _directory(original)
        struct.pack_into('<I', original, start, len(original))
        with self.assertRaises(ValueError):
            add_definitions(original, {'dfn_new.zrd': encode(None)})


if __name__ == '__main__':
    unittest.main()
