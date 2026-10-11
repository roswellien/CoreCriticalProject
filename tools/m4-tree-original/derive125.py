"""Fresh125 original build/run commands, preserving accepted tools."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def main():
    base=Path(__file__).resolve().parent
    build=(ROOT/'tools/m4-lockit-original/build_original.ps1').read_text(encoding='utf-8-sig').replace('reports/m4-lockit-original','reports/m4-tree-original').replace('sequences=6;phases=744','sequences=6;phases=750;roots=125').replace('original_executed=$false;','initializer_credit=$false;original_executed=$false;')
    run=(ROOT/'tools/m4-lockit-original/run_original.py').read_text().replace('reports/m4-lockit-original','reports/m4-tree-original').replace('original124','original125')
    for filename,s in [('build125.ps1',build),('run125.py',run)]:
        p=base/filename;assert not p.exists(),'Fresh additive command';p.write_text(s)
    print('Full125 additive build/run commands prepared.')
if __name__=='__main__':main()
