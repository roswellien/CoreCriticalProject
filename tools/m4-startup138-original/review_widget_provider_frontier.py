"""Bound ordinary-export registrar growth frontier; never a source acceptance gate."""
from pathlib import Path
import hashlib,importlib.util,json,struct
R=Path(__file__).resolve().parents[2];P={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;P[str(p)]=v;return p
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
out=R/'reports/m4-startup138-original/widget-provider-frontier-r1';assert not out.exists();out.mkdir()
vp=R/'reports/m4-startup138-original/original-validation-r2/report.json';vh='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181';validation=json.loads(pin(vp,vh).read_bytes())
ep=R/'tools/m4-startup131-original/export_reader.py';s=importlib.util.spec_from_file_location('ordinary_frontier',pin(ep));E=importlib.util.module_from_spec(s);s.loader.exec_module(E);reader=E.ExportReader(vp,vh,'original',pin);rows=[];growth=[]
try:
 for seq in range(6):
  for phase in(15,16,17,47,134,135,136):
   stem=f'phase/{seq}/{phase}/';ledger=reader.data(stem+'api-ledger.bin');count=u(reader.data(stem+'api-count.bin'))[0];assert len(ledger)==104*count
   words=list(struct.iter_unpack('<26I',ledger));assert all(w[9]==w[19]==0 for w in words)
   row=dict(sequence=seq,phase=phase,ledger_count=count,API_kinds=[w[24]for w in words],all_raw_entry_return_PC_fields_zero=True);rows.append(row)
   if any(w[24]==3 for w in words):
    registry=u(reader.data(stem+'registry-before-meta.bin'),0,4);backing=reader.data(stem+'registry-before-backing.bin');assert len(backing)==registry[2]
    keys=[k for k in reader.entries if k.startswith(stem)and('registry'in k or 'api-initial'in k or 'realloc'in k)]
    growth.append(dict(sequence=seq,phase=phase,registry_BEFORE=registry,reallocations=[dict(arguments=list(w[20:24]),result=w[10],source_return_word=w[25])for w in words if w[24]==3],available_backing_keys=keys,separate_realloc_initial_backing_export_present=any('realloc'in k or 'api-initial'in k for k in keys)))
finally:reader.close()
assert len(rows)==42 and len(growth)==6 and all(not r['separate_realloc_initial_backing_export_present']for r in growth)
lp=vp.parent/'font-resource-lifetimes.json';fonts=json.loads(pin(lp,validation['files'][str(lp.resolve())]).read_bytes());assert len(fonts)==90
for p in [Path(__file__),R/'tools/m4-startup138-original/compare_widget_source_v4.py',R/'reports/m4-startup138-original/widget-provider-source-r2/report.json',R/'reports/m4-startup138-original/widget-provider-source-r2/failure.txt',R/'reports/m4-startup138-original/preparation-r7/reference.cpp']:pin(p)
report=dict(passed=True,readiness_only=True,complete_current_widget_gate=False,initializer_credit=0,source_gate_passed=False,archive_reader_opened=False,ordinary_export_closed=reader.closed,actual_API_PC_observed=False,API_ledger_schema_check=rows,growth_frontiers=growth,source_proof_partial=dict(sequence=0,complete_phases=[15,16,17],whole_CRT_pages=192,whole_source_nonstack_pages=204),next_gates=['Fresh independent source API-seam observation/export of full successful HeapReAlloc backing BEFORE any guest writes, capacity, source frame and named API identity; retain preserved old prefix and derive callback write. Current final registry bytes must remain equality targets.', 'Track each source CreateFontA successful finite response with same source ESI instance, owning field store, sequence and occurrence; compare all90 actual lifetime rows, forbid borrowing StockObject handles as owned creations.', 'Retire source owned font generations only through exact successful source DeleteObject call; join surviving same-instance source handles and reverse manual cleanup identity/BOOL/FP conservation. Manual cleanup is typed resource evidence, not source shutdown execution.', 'Complete all42 root source69/CRT/backing endpoints, exact GDI/FPS/FS causal joins and later no-read-before-source-overwrite stack proof.'],files=P)
q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
