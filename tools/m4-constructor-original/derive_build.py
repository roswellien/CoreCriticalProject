"""Reuse the exact current x86 compiler/controller with bounded metadata."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2]
source=root/'tools/m4-startup131-original/build.ps1'
target=Path(__file__).resolve().with_name('build.ps1')
assert not target.exists()
text=source.read_text()
assert text.count('reports/m4-startup131-original')==1
text=text.replace('reports/m4-startup131-original','reports/m4-constructor-original',1)
assert text.count('phases=786;roots=131')==1
text=text.replace('phases=786;roots=131','phases=222;roots=37',1)
target.write_text(text)
receipt=target.with_name('build-lineage.json')
receipt.write_text(json.dumps(dict(base=str(source),base_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),generated=str(target),generated_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),changes=['Own constructor original namespace','37 selected chronological roots /222 phases metadata'],compiler_and_flags_unchanged=True),indent=2)+'\n')
