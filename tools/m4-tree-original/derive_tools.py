"""Derive bounded tree build/run commands without changing accepted tools."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def main():
    target = Path(__file__).resolve().parent
    build = (ROOT / 'tools/m4-lockit-original/build_original.ps1').read_text(encoding='utf-8-sig')
    build = build.replace('reports/m4-lockit-original', 'reports/m4-tree-original')
    build = build.replace('sequences=6;phases=744', 'sequences=1;phases=1')
    build = build.replace('original_executed=$false;', 'prefix_only=$true;initializer_credit=$false;original_executed=$false;')
    run = (ROOT / 'tools/m4-lockit-original/run_original.py').read_text(encoding='utf-8-sig')
    run = run.replace('reports/m4-lockit-original', 'reports/m4-tree-original').replace('original124', 'one-root tree prefix')
    run = run.replace('per_phase_reseed=False,validation_pending=True', 'per_phase_reseed=False,validation_pending=True,initializer_credit=False,prefix_only=True')
    for name, text in [('build_prefix.ps1', build), ('run_prefix.py', run)]:
        path = target / name
        assert not path.exists(), 'Fresh derived command'
        path.write_text(text)
    print('Bounded additive build/run commands prepared.')

if __name__ == '__main__':
    main()
