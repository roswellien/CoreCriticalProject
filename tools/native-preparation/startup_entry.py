"""Regenerate the selected translated retail entry object from the player's PE.

The input recipe contains only original-image spans/entries, object hashes and
non-executable timestamp metadata. No reports, prebuilt objects or saved state.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from translate import need, resolve, sha, source_span


def prepare(tools, game, recipe, output):
    need(not output.exists(), 'Use a fresh startup entry directory')
    manifest = json.loads((tools / 'tools.json').read_text())
    for name, pin in manifest['files'].items():
        path = resolve(tools, name)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Startup tool changed: ' + name)
    need(sha(game) == recipe['image_sha256'], 'Original game input changed')
    source = game.read_bytes()
    spans, entries = recipe['spans'], recipe['entries']
    base = min(start for start, end in spans)
    end = max(end for start, end in spans)
    need(0 < end-base < 16384, 'Bounded original startup spans')
    code = bytearray(b'\xcc' * (end-base))
    for start, end in spans:
        code[start-base:end-base] = source_span(source, start, end)
    output.mkdir(parents=True)
    llvm = tools / 'llvm'

    def run(tool, arguments, name):
        result = subprocess.run([str(tool), *map(str, arguments)], capture_output=True, timeout=120)
        (output / (name + '.stderr')).write_bytes(result.stderr[-1024*1024:])
        need(result.returncode == 0, 'Startup tool failed: ' + name)

    guests = []
    for entry in entries:
        guest = output / f'guest-{entry:x}.ll'
        run(tools / 'lifter/remill-lift-control-21.exe', ['--arch=x86', '--os=windows', '--address='+str(base),
            '--entry_address='+str(entry), '--bytes='+code.hex(), '--semantics_dir='+str(tools / 'semantics/control'),
            '--ir_out='+str(guest)], f'lift-{entry:x}')
        guests.append(guest)
    guest = output / 'guest.ll'
    run(llvm / 'llvm-link.exe', ['-S', *guests, '-o', guest], 'link')
    original = guest.read_text()
    need('__remill_missing_block' not in original, 'Incomplete original entry block')
    need(set(re.findall(r'^define ptr @([^ (]+)', original, re.M)) == {f'sub_{entry:x}' for entry in entries}, 'Exact original startup entries')
    sys.path.insert(0, str(tools / 'sources'))
    import host_adapter
    import entry_adapt
    candidate = entry_adapt.adapt_entry(original, output, host_adapter, llvm / 'LLVM-C.dll', entries)
    text = candidate.read_text()
    need(text.count('__remill_undefined_8') == 5, 'Exact game-only undefined-helper namespace boundary')
    candidate.write_text(text.replace('__remill_undefined_8', 'mw34_fdiv_entry_undefined_8'))
    target = output / 'candidate-O2.obj'
    run(llvm / 'clang.exe', ['--target=x86_64-pc-windows-msvc', '-O2', '-c', candidate, '-o', target], 'compile')
    with target.open('r+b') as stream:
        stream.seek(4)
        stream.write(struct.pack('<I', recipe['coff_timestamp']))
    need(sha(target) == recipe['expected_object_sha256'], 'Generated retail startup object differs from selected host')
    (output / 'generation.json').write_text(json.dumps(dict(contract='mw3-retail-entry-v1',
        object_sha256=sha(target), source_image_sha256=sha(game), original_entries=entries,
        captured_state_used=False, original_code_executed=False), indent=2) + '\n')
    return sha(target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    recipe = json.loads(args.recipe.read_text())
    need(recipe['contract'] == 'mw3-retail-entry-v1', 'Unsupported startup contract')
    print(prepare(args.tools.resolve(), args.game.resolve(), recipe, args.output.resolve()))
