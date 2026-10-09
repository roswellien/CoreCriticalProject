"""Independent read-only wire-offset comparison; does not run original x86."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


def bind(path):
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'size_bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


def decode(data, source_offset):
    nodes = []
    cursor = 0

    def read_word():
        nonlocal cursor
        if cursor + 4 > len(data):
            raise ValueError('Independent reference truncated word')
        result, = struct.unpack_from('<I', data, cursor)
        cursor += 4
        return result

    def token(depth):
        nonlocal cursor
        if depth > 128 or len(nodes) >= 1000000:
            raise ValueError('Independent reference token bounds')
        start = cursor
        kind = read_word()
        value = read_word()
        if kind not in (1, 2, 3, 4):
            raise ValueError('Independent reference unknown token')
        index = len(nodes)
        item = {'index': index, 'type': kind, 'offset': source_offset + start}
        nodes.append(item)
        if kind in (1, 2):
            item['word'] = value
        elif kind == 3:
            if value > 16 * 1024 * 1024 or cursor + value > len(data):
                raise ValueError('Independent reference string bounds')
            item['string_offset'] = source_offset + cursor
            item['string_hex'] = data[cursor:cursor + value].hex()
            cursor += value
        else:
            if value < 1 or value - 1 > (len(data) - cursor) // 8:
                raise ValueError('Independent reference list bounds')
            item['children'] = [token(depth + 1) for _ in range(value - 1)]
        item['end'] = source_offset + cursor
        return index

    token(0)
    if cursor != len(data):
        raise ValueError('Independent reference trailing bytes')
    return nodes


def label_successor(nodes, start, query):
    node = nodes[start]
    if node['type'] != 4:
        return None
    children = node['children']
    for i, child in enumerate(children):
        item = nodes[child]
        if item['type'] == 4:
            result = label_successor(nodes, child, query)
            if result is not None:
                return result
        elif item['type'] == 3 and bytes.fromhex(item['string_hex']).split(b'\0')[0] == query:
            if i + 1 == len(children):
                raise ValueError('Independent reference matching terminal label')
            return children[i + 1]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--entry', action='append', required=True)
    parser.add_argument('--label', default=None)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(exist_ok=False)
    archive = args.archive.resolve()
    host = args.host.resolve()
    before = bind(archive)
    data = archive.read_bytes()
    if len(data) < 8:
        raise ValueError('No archive footer')
    version, count = struct.unpack_from('<II', data, len(data) - 8)
    if version != 1 or count > 65536 or count * 148 + 8 > len(data):
        raise ValueError('Independent reference footer')
    directory = len(data) - count * 148 - 8
    expected_entries = []
    for index in range(count):
        base = directory + index * 148
        offset, size = struct.unpack_from('<II', data, base)
        name_field = data[base + 8:base + 72]
        if b'\0' not in name_field or offset + size > directory:
            raise ValueError('Independent reference directory bounds')
        expected_entries.append({'index': index, 'directory_offset': base,
            'offset': offset, 'bytes': size, 'name': name_field.split(b'\0')[0].decode('latin1'),
            'opaque_word': struct.unpack_from('<I', data, base + 72)[0],
            'metadata_hex': data[base + 76:base + 148].hex()})
    commands = []

    def run(name, arguments, exit_code=0, diagnostic=None):
        command = [str(host), *map(str, arguments)]
        result = subprocess.run(command, capture_output=True, timeout=30)
        stdout, stderr = out / (name + '.stdout'), out / (name + '.stderr')
        stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
        if result.returncode != exit_code:
            raise ValueError('Actual asset command exit mismatch: ' + name)
        if exit_code == 0 and result.stderr:
            raise ValueError('Successful parser produced diagnostics')
        if diagnostic and (result.stdout or diagnostic not in result.stderr.decode()):
            raise ValueError('Wrong explicit rejection: ' + name)
        commands.append({'name': name, 'command': command, 'exit_code': result.returncode,
            'intended_diagnostic': diagnostic, 'stdout': bind(stdout), 'stderr': bind(stderr)})
        return result

    observed = json.loads(run('actual-directory', ['--directory', archive]).stdout)
    if observed['source']['sha256'] != before['sha256'] or observed['source']['size_bytes'] != len(data):
        raise ValueError('Actual owning store identity differs')
    if observed['directory_offset'] != directory or observed['entries'] != expected_entries:
        raise ValueError('Actual native directory metadata differs from reference')
    comparisons = []
    for number, entry_name in enumerate(args.entry):
        record = next((e for e in expected_entries if e['name'].lower() == entry_name.lower()), None)
        if record is None:
            raise ValueError('Requested reference entry missing')
        payload = data[record['offset']:record['offset'] + record['bytes']]
        nodes = decode(payload, record['offset'])
        arguments = ['--document', archive, entry_name]
        label_node = None
        if number == 0 and args.label:
            arguments.append(args.label)
            label_node = label_successor(nodes, 0, args.label.encode('ascii'))
            if label_node is None:
                raise ValueError('Requested reference label missing')
        result = json.loads(run('actual-document-' + str(number), arguments).stdout)
        document = result['document']
        if document['nodes'] != nodes or document['view_offset'] != record['offset'] or document['view_bytes'] != len(payload):
            raise ValueError('Actual native token offsets/types/words/strings/children differ')
        if document['payload_sha256'] != hashlib.sha256(payload).hexdigest():
            raise ValueError('Actual native payload identity differs')
        if document['source'] != observed['source'] or result.get('label_node') != label_node:
            raise ValueError('Actual native source/label successor differs')
        if result['original_x86_executed'] or result['widgets_created']:
            raise ValueError('Unsupported original/widget execution claim')
        reference = out / ('reference-document-' + str(number) + '.json')
        reference.write_text(json.dumps({'entry': record, 'nodes': nodes,
            'label_node': label_node}, indent=2) + '\n', encoding='utf-8')
        comparisons.append({'entry': record, 'payload_sha256': hashlib.sha256(payload).hexdigest(),
            'nodes': len(nodes), 'label_node': label_node, 'full_native_reference_equality': True,
            'independent_reference': bind(reference)})
    run('missing-input', ['--directory', out / 'missing.bin'], 1, 'Missing asset input')
    run('missing-entry', ['--document', archive, '__authored_missing_entry__'], 1, 'Archive entry not found')
    run('missing-label', ['--document', archive, args.entry[0], '__authored_missing_label__'], 1,
        'Document label not found')
    run('wrong-mode', ['--unexpected', archive], 2, 'Usage: mw34_m4_assets')
    altered = bytearray(data); struct.pack_into('<I', altered, len(altered) - 8, 2)
    bad_footer = out / 'authored-invalid-footer.zbd'; bad_footer.write_bytes(altered)
    run('wrong-footer', ['--directory', bad_footer], 1, 'Unsupported reader archive version')
    if bind(archive) != before:
        raise ValueError('Read-only original asset input changed')
    report = {'schema_version': 1, 'passed': True, 'host': bind(host), 'archive_before_after': before,
        'reference_decoder': bind(Path(__file__)), 'directory_records_compared': count,
        'documents_compared': comparisons, 'commands': commands,
        'scope': 'Native host parser versus independent read-only wire model; no original parser oracle',
        'original_x86_executed': False, 'widget_callbacks_executed': False,
        'guest_reader_object_implemented': False, 'native_startup_or_menu_complete': False}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Read-only asset comparisons:', count, 'directory records,',
          sum(c['nodes'] for c in comparisons), 'lossless tokens;', len(commands), 'commands')


if __name__ == '__main__':
    main()
