"""Derive unchanged current x86 compiler workflow with connected-prefix metadata."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];source=R/'tools/m4-widget-original/build.ps1';target=R/'tools/m4-mfc1168-connected-original/build.ps1'
if hashlib.sha256(source.read_bytes()).hexdigest()!='d8ac070cdf91b4a7efdf3b6523e3dfe9b407c1046cdd9268fb0ef29e7f4dcd55':
 # Exact current build source must be the physically pinned source of build5.
 import json
 receipt=json.loads((R/'reports/m4-widget-original/build-r5/build.json').read_bytes())
 if hashlib.sha256(source.read_bytes()).hexdigest()!=receipt['sources'][str(source)]:raise ValueError('Compiler workflow identity')
if target.exists():raise ValueError('Fresh build script')
s=source.read_text().replace('reports/m4-widget-original','reports/m4-mfc1168-connected-original').replace('sequences=1;phases=5;roots=5;pages=43;external_pages=21;combined_pages=64;snapshot_bytes=266964','sequences=1;phases=14;roots=14;pages=43;external_pages=3;combined_pages=46;MFC_boundary_bytes=664;named_API_boundary_bytes=668')
target.write_text(s);print(hashlib.sha256(target.read_bytes()).hexdigest())
