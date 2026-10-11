"""Independent ordinary-file warm-provider derivative audit; no payload or archive reader."""
from pathlib import Path
import hashlib,json,re,importlib.util
R=Path(__file__).resolve().parents[2];P={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or v==h;P[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
base=R/'reports/m4-startup138-original';out=R/'reports/m4-138-validation-review/warm-widget-source-review-r1';assert not out.exists();out.mkdir()
for n in(1,2,3):
 prep=read(base/f'widget-provider-preparation-r{n}/report.json')
 assert prep['passed']and prep['exact_reverse_delta']
 for p,h in prep['files'].items():pin(p,h)
 if n in(1,3):
  source=R/f'tools/m4-startup138-original/compare_widget_source_v{2 if n==1 else 4}.py';previous=source.with_name('compare_widget_source.py'if n==1 else 'compare_widget_source_v3.py');t=source.read_text()
  for d in reversed(prep['changes']):
   pos=d['position'];assert t[pos:pos+len(d['new'])]==d['new'];t=t[:pos]+d['old']+t[pos+len(d['new']):]
  assert t==previous.read_text()
 else:
  assert (R/'tools/m4-startup138-original/compare_widget_source_v3.py').read_text().replace('0x7800106f','0x78001091')==(R/'tools/m4-startup138-original/compare_widget_source_v2.py').read_text()
contract=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
spec=importlib.util.spec_from_file_location('physical',pin(R/'tools/analysis/pe.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
image=m.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());calls=[]
for pc,slot in((0x7800106f,0x7802e044),(0x780015b5,0x7802e1dc),(0x780012ab,0x7802e048)):
 row=next(r for r in contract['instructions']if r['pc']==pc);assert row['mnemonic']=='call'and hex(slot)[2:]in row['operands'];offset,_=image.rva_range(pc-image.image_base,6);raw=image.data[offset:offset+6];assert raw==b'\xff\x15'+slot.to_bytes(4,'little');calls.append(dict(PC=pc,IAT=slot,physical_bytes=raw.hex()))
asm=pin(base/'preparation-r7/reference_x86.asm').read_text();assert not re.search(r'(?:mov|pop)\s+DWORD PTR registry_API_(?:before|after)\[36\]',asm)
for side in('before','after'):
 for off in range(0,36,4):assert f'registry_API_{side}[{off}]'in asm
cpp=pin(base/'preparation-r7/reference.cpp').read_text();assert 'Cpu registry_API_before{},registry_API_after{};'in cpp
t=pin(R/'tools/m4-startup138-original/compare_widget_source_v4.py').read_text();assert "need(w[9]==0"in t and "need(w[19]==0 and model.cursor==w[25]"in t;assert "kind in(2,5,6)"in t
assert "model.api_return(site,n,w[10])"in t and "memory_output_seed=False"in t and "Whole source-derived own registry backing AFTER"in t
source=read(base/'widget-provider-source-r2/report.json','f8b09d7af01c4fb2f902faca8019af880f5ed81ac8895955adc600407909b0cb');assert not source['passed']and source['initializer_credit']==0 and source['counts']['literal_complete_registrar_root_endpoints']==3
frontier=read(base/'widget-provider-frontier-r2/report.json','16d00f5e8779ca17604d9477758906bd73bfb851c8e08bebd57ca09ffb786ddf');assert len(frontier['API_ledger_schema_check'])==42 and all(r['all_raw_entry_return_PC_fields_zero']for r in frontier['API_ledger_schema_check'])
pin(base/'widget-provider-source-r2/failure.txt');pin(__file__)
report=dict(passed=True,scope='Independent derivative/source/physical/API-schema audit. Existing bounded source execution remains a failed gate, with three complete warm endpoints only.',physical_CALL_IAT_bindings=calls,exact_inverse_preserves_inherited_source_gates=True,actual_API_CPU_populated_DWORDs=9,raw_API_PC_words_zero=True,API_PC_directly_observed=False,source_PC_bound_by_literal_CALL_IAT_kind_frame=True,registry_writes_source_driven=True,AFTER_memory_seed=False,growth_deliberately_unadmitted=True,warm_complete_root_endpoints=3,complete_widget_source_gate=False,font_lifetime_source_gate_pending=True,initializer_credit=0,archive_reader_opened=False,payload_reader_opened=False,files=P)
q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
