"""Preserve old execution tools and write scoped original116 derivatives."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for name in ('build_original.ps1','run_original.py'):
 p=ROOT/'tools/m4-container-source'/name
 assert not p.exists()
 s=(ROOT/'tools/m4-fs-source'/name).read_text(encoding='utf-8-sig').replace('m4-fs-source','m4-container-source').replace('original109','original116').replace('startup109','startup116').replace('record_bytes=291456','record_bytes=307840').replace('phases=654','phases=696').replace('pages=35','pages=37')
 p.write_text(s,encoding='utf-8')
