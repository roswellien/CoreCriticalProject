"""Correction: 596900 jumps to its real 596B00 prolog; FS read is596B07."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent/'fs_variant_diagnostic.py'
s=p.read_text(encoding='utf-8');assert s.count('(0x596900,0x596907,False)')==1
exec(compile(s.replace('(0x596900,0x596907,False)','(0x596900,0x596b07,False)'),str(p),'exec'),globals())
