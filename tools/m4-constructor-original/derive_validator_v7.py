"""Repair only the cleanup producer-key lookup, keeping every ownership guard."""
from pathlib import Path
import ast,hashlib
h=Path(__file__).resolve().parent;t=(h/'validate_v6.py').read_text();out=h/'validate_v7.py'
if out.exists():raise ValueError('Fresh additive validator required')
a="cleanup_prefix=f'constructor-prerequisites/cleanup/{sequence}/constructor-owner-'";b="cleanup_prefix=f'cleanup/{sequence}/constructor-owner-'"
if t.count(a)!=1:raise ValueError('Exact sole cleanup-key correction')
t=t.replace(a,b,1)
a="        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)"
digest=hashlib.sha256((h.parents[1]/'reports/m4-constructor-original/cleanup-diagnostic-r1/report.json').read_bytes()).hexdigest()
b="        cleanup_evidence=read(BASE/'cleanup-diagnostic-r1/report.json',"+repr(digest)+");need(cleanup_evidence['passed']and cleanup_evidence['producer_prefix']=='cleanup/<sequence>/constructor-owner-','Exact current producer cleanup-key evidence')\n        for path,digest in cleanup_evidence['files'].items():pin(path,digest)\n"+a
if t.count(a)!=1:raise ValueError('Exact evidence binding')
t=t.replace(a,b,1)
a="pin(Path(__file__).with_name('derive_validator_v6.py'));pin(sys.executable);passed=True";b="pin(Path(__file__).with_name('derive_validator_v6.py'));pin(Path(__file__).with_name('validate_v6.py'));pin(Path(__file__).with_name('derive_validator_v7.py'));pin(sys.executable);passed=True"
if t.count(a)!=1:raise ValueError('Exact checker lineage')
t=t.replace(a,b,1);ast.parse(t);out.write_text(t)
