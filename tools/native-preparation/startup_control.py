"""Regenerate control and FDIV startup objects from original executable spans."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

from translate import need, resolve, sha, source_span


def prepare(tools, game, provider, recipe, output):
    need(recipe['contract'] == 'mw3-control-startup-v1', 'Unsupported control startup recipe')
    need(not output.exists(), 'Use a fresh control startup directory')
    manifest = json.loads((tools / 'tools.json').read_text())
    for name, pin in manifest['files'].items():
        path = resolve(tools, name)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'Control tool changed: '+name)
    need(sha(game) == recipe['game_sha256'] and sha(provider) == recipe['provider_sha256'], 'Original startup input changed')
    images = dict(game=game.read_bytes(), provider=provider.read_bytes())
    output.mkdir(parents=True)
    llvm = tools / 'llvm'

    def run(tool, arguments, folder, name):
        result = subprocess.run([str(tool), *map(str, arguments)], capture_output=True, timeout=120)
        (folder / (name+'.stderr')).write_bytes(result.stderr[-1024*1024:])
        need(result.returncode == 0, 'Control tool failed: '+name)

    def lift(name):
        item = recipe[name]
        folder = output / name
        folder.mkdir()
        spans = item['spans']
        base = min(s['start'] for s in spans)
        end = max(s['end'] for s in spans)
        need(0 < end-base < 262144, 'Bounded startup source spans')
        dense = bytearray(b'\xcc' * (end-base))
        for span in spans:
            code = source_span(images[item['image']], span['start'], span['end'])
            need(hashlib.sha256(code).hexdigest() == span['sha256'], 'Original startup span changed')
            dense[span['start']-base:span['end']-base] = code
        guests = []
        for entry in item['entries']:
            need(any(s['start'] <= entry < s['end'] for s in spans), 'Entry outside original source')
            guest = folder / f'guest-{entry:x}.ll'
            flags = ['--arch=x86', '--os=windows', '--address='+str(base), '--entry_address='+str(entry),
                '--bytes='+dense.hex(), '--semantics_dir='+str(tools / 'semantics/control'), '--ir_out='+str(guest)]
            need(all('\n' not in f and '\r' not in f for f in flags), 'Invalid lifter flag path')
            flagfile = folder / f'flags-{entry:x}.txt'
            flagfile.write_text('\n'.join(flags)+'\n')
            run(tools / 'lifter/remill-lift-control-21.exe', ['--flagfile='+str(flagfile)], folder, f'lift-{entry:x}')
            guests.append(guest)
        run(llvm / 'llvm-link.exe', [*guests, '-S', '-o', folder / 'guest.ll'], folder, 'link')
        text = (folder / 'guest.ll').read_text()
        need('__remill_missing_block' not in text, 'Incomplete startup CFG')
        need(set(re.findall(r'^define ptr @([^ (]+)', text, re.M)) == {f'sub_{e:x}' for e in item['entries']}, 'Startup definition mismatch')
        return folder

    sys.path.insert(0, str(tools / 'sources'))
    import startup_adapt
    control = lift('provider')
    startup_adapt.adapt_provider(control, llvm / 'LLVM-C.dll', recipe['provider']['entries'], recipe['provider']['instruction_pcs'])
    game_folder = lift('game')
    (game_folder / 'game-guest.ll').write_bytes((game_folder / 'guest.ll').read_bytes())
    startup_adapt.adapt_game(game_folder, llvm / 'LLVM-C.dll')
    combined = output / 'control.ll'
    run(llvm / 'llvm-link.exe', [game_folder / 'game-host.ll', control / 'host.ll', '-S', '-o', combined], output, 'control-link')
    original = combined.read_text()
    text = original
    mappings = recipe['control_object']['symbol_renames']
    for old, new in mappings.items():
        text, count = re.subn(r'(?<![A-Za-z0-9_.])'+re.escape(old)+r'(?![A-Za-z0-9_.])', new, text)
        need(count > 0, 'Missing control symbol: '+old)
    reverse = text
    for old, new in mappings.items():
        reverse = reverse.replace(new, old)
    need(reverse == original, 'Non-reversible control symbol mapping')
    combined.write_text(text)

    def compile_object(name, source, optimize=False):
        if optimize:
            optimized = output / (name+'-O2.ll')
            run(llvm / 'opt.exe', ['-passes=default<O2>', '-S', source, '-o', optimized], output, name+'-opt')
            source = optimized
        target = output / (name+'-O2.obj')
        run(llvm / 'llc.exe', ['-filetype=obj', '-O2', source, '-o', target], output, name+'-compile')
        pin = recipe[name+'_object']
        with target.open('r+b') as stream:
            stream.seek(4)
            stream.write(struct.pack('<I', pin['coff_timestamp']))
        need(sha(target) == pin['expected_object_sha256'], 'Generated '+name+' object differs from selected host')
        return sha(target)

    objects = dict(control=compile_object('control', combined))
    writer = lift('writer')
    startup_adapt.adapt_writer(writer, llvm / 'LLVM-C.dll', control / 'host.ll')
    objects['writer'] = compile_object('writer', writer / 'host.ll', optimize=True)
    (output / 'generation.json').write_text(json.dumps(dict(contract=recipe['contract'], objects=objects,
        captured_state_used=False, original_code_executed=False), indent=2)+'\n')
    return objects


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('tools', 'game', 'provider', 'recipe', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.tools.resolve(), args.game.resolve(), args.provider.resolve(),
        json.loads(args.recipe.read_text()), args.output.resolve()))
