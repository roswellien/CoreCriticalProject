"""Adversarial inventory/path/aggregate cases using the normal strict reader."""
import copy
import hashlib
import json
from transport import CaptureBundle, need, sha_file, validate_inventory
from capture_bundle import FORMAT, HEADER, MAGIC, _json
from paths import publish_bytes


def encoded(index, payload, *, index_sha=None):
    raw = _json(index)
    return HEADER.pack(MAGIC, len(raw), hashlib.sha256(raw).digest() if index_sha is None else index_sha) + raw + payload


def run_controls(out, before, after):
    directory = out / 'reader-controls'
    directory.mkdir()
    data = {'after.bin': after, 'before.bin': before}
    expected = {name: {'size_bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
                for name, value in data.items()}
    entries = []
    offset = 0
    for name, value in data.items():
        entries.append({'path': name, 'offset': offset, 'size': len(value), 'sha256': expected[name]['sha256']})
        offset += len(value)
    index = {'format': FORMAT, 'files': entries, 'total_bytes': offset}
    payload = b''.join(data.values())
    original = encoded(index, payload)
    valid_path = directory / 'valid.mwb'
    publish_bytes(valid_path, original)
    with CaptureBundle(valid_path, sha_file(valid_path)) as reader:
        validate_inventory(reader, expected)
    cases = []

    def rejected(label, content, expected_map=None, external_sha=None):
        path = directory / (str(len(cases)) + '.mwb')
        publish_bytes(path, content)
        try:
            with CaptureBundle(path, sha_file(path) if external_sha is None else external_sha) as reader:
                validate_inventory(reader, expected if expected_map is None else expected_map)
        except ValueError as error:
            reason = str(error)
        else:
            raise ValueError('Normal reader accepted adversarial aggregate: ' + label)
        cases.append({'label': label, 'denied': True, 'reason': reason,
            'path': str(path), 'sha256': sha_file(path)})

    external = hashlib.sha256(original).hexdigest()
    changed = bytearray(original)
    changed[-1] ^= 1
    rejected('aggregate_changed_original_external_pin', bytes(changed), external_sha=external)
    rejected('aggregate_wrong_external_pin', original, external_sha='0' * 64)
    rejected('aggregate_truncated_original_external_pin', original[:-1], external_sha=external)
    rejected('aggregate_trailing_original_external_pin', original + b'\0', external_sha=external)
    rejected('payload_entry_changed_even_with_new_external_pin', encoded(index, bytes(bytearray(payload[:-1]) + bytes([payload[-1] ^ 1]))))
    rejected('index_digest_changed_even_with_new_external_pin', encoded(index, payload, index_sha=b'\0' * 32))
    rejected('trailing_payload_even_with_new_external_pin', original + b'\0')
    bad = copy.deepcopy(index)
    bad['files'][0]['sha256'] = '0' * 64
    rejected('entry_digest_wrong', encoded(bad, payload))
    bad['files'][0]['sha256'] = bad['files'][0]['sha256'].upper().replace('0', 'A')
    rejected('entry_digest_noncanonical', encoded(bad, payload))
    for label, name in (('traversal', '../before.bin'), ('absolute', '/before.bin'),
        ('drive', 'C:/before.bin'), ('ads', 'before.bin:x'), ('backslash', 'a\\before.bin'),
        ('empty_component', 'a//b'), ('dot_component', 'a/./b'), ('parent_component', 'a/../b'),
        ('reserved_device', 'CON.bin'), ('trailing_dot', 'a.'), ('trailing_space', 'a '),
        ('non_NFC', 'e\u0301.bin'), ('control_character', 'a\x01.bin')):
        bad = copy.deepcopy(index)
        bad['files'][0]['path'] = name
        rejected('unsafe_path_' + label, encoded(bad, payload))
    for label, name in (('duplicate_path', 'after.bin'), ('case_alias', 'AFTER.BIN')):
        bad = copy.deepcopy(index)
        bad['files'][1]['path'] = name
        rejected(label, encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['files'] = bad['files'][:1]
    bad['total_bytes'] = len(after)
    rejected('valid_aggregate_missing_external_entry', encoded(bad, after))
    bad = copy.deepcopy(index)
    extra = b'x'
    bad['files'].append({'path': 'zz-extra.bin', 'offset': offset, 'size': 1,
                         'sha256': hashlib.sha256(extra).hexdigest()})
    bad['total_bytes'] += 1
    rejected('valid_aggregate_extra_external_entry', encoded(bad, payload + extra))
    bad = copy.deepcopy(index)
    bad['files'][0]['path'] = 'unknown.bin'
    bad['files'][1]['path'] = 'zz.bin'
    rejected('valid_aggregate_renamed_external_inventory', encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['files'][1]['offset'] += 1
    rejected('noncontiguous_extent', encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['files'][0]['size'] = True
    rejected('bool_extent', encoded(bad, payload))
    bad['files'][0]['size'] = -1
    rejected('negative_extent', encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['total_bytes'] += 1
    rejected('total_extent_mismatch', encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['files'][0]['extra'] = 1
    rejected('entry_extra_field', encoded(bad, payload))
    bad = copy.deepcopy(index)
    bad['extra'] = 1
    rejected('index_extra_field', encoded(bad, payload))
    bad_expected = copy.deepcopy(expected)
    bad_expected['before.bin']['size_bytes'] += 1
    rejected('external_expected_size_changed', original, bad_expected)
    bad_expected = copy.deepcopy(expected)
    bad_expected['before.bin']['sha256'] = '0' * 64
    rejected('external_expected_digest_changed', original, bad_expected)
    bad_expected = copy.deepcopy(expected)
    bad_expected['before.bin']['size_bytes'] = True
    rejected('external_expected_bool_size', original, bad_expected)
    bad_expected = copy.deepcopy(expected)
    bad_expected['before.bin']['extra'] = 1
    rejected('external_expected_schema_extra', original, bad_expected)
    need(len(cases) >= 35, 'Meaningful aggregate/path/inventory control domain')
    return {'passed': True, 'normal_reader_class': 'frozen CaptureBundle + validate_inventory',
        'positive_small_inventory': 2, 'denials': len(cases), 'tests': cases,
        'synthetic_transport_controls_only': True}
