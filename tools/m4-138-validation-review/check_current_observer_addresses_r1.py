"""Ordinary compiled attribution only; no capture reader."""
from pathlib import Path
import json,importlib.util,hashlib,struct
R=Path(__file__).resolve().parents[2];P={}
def pin(p):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');P[str(p)]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();return p
old=json.loads(pin(R/'reports/m4-138-validation-review/mfc-transition-r3/patch-identities.json').read_bytes());obs=json.loads(pin(R/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/compiled-observers.json').read_bytes());res={}
for section in obs:
 for rel in section['relocations']:
  if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
   n,a=rel['symbol'],rel['actual_symbol_address'];assert n not in res or res[n]==a;res[n]=a
q=pin(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py');spec=importlib.util.spec_from_file_location('coff_address',q);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
for family in('fs_observer_x86','nullfree_observer_x86'):
 symbols,sections=C.coff(pin(R/f'reports/m4-startup138-original/build-r5/build-x86/mw34_joint_startup124_original.dir/Release/{family}.obj').read_bytes());proof=next(x for x in obs if x['family']=='whole-ASM'and x['symbol']==family+' whole source');sections_=[i for i,s in sections.items()if s['flags']&0x20000000 and s['bytes']];assert len(sections_)==1;section=sections_[0];assert sections[section]['bytes'].hex()==proof['object_raw_hex']
 for sy in symbols.values():
  if sy['section']==section and sy['name'].startswith(('_fs_hook_','_nullfree_entry_hook','_nullfree_ret_hook')):
   n,a=sy['name'],proof['address']+sy['value'];assert n not in res or res[n]==a;res[n]=a
rows=[]
for patch in old:
 n=patch['symbol'];pc=patch['pc'];a=res[n];size=len(bytes.fromhex(patch['original_hex']));current=struct.pack('<I',a).hex()if patch['kind']=='registry-IAT'else(b'\xe9'+struct.pack('<I',(a-pc-5)&0xffffffff)+b'\x90'*(size-5)).hex();rows.append(dict(symbol=n,pc=pc,address=a,old_hex=patch['instrumented_hex'],current_hex=current,identical=current==patch['instrumented_hex']))
out=R/'reports/m4-138-validation-review/current-observer-addresses-r1';assert not out.exists();out.mkdir();pin(__file__);p=out/'report.json';p.write_text(json.dumps(dict(passed=True,rows=rows,all13_old_instrumented_spans_identical=all(r['identical']for r in rows),archive_reader_opened=False,initializer_credit=0,files=P),indent=2)+'\n');print(p,hashlib.sha256(p.read_bytes()).hexdigest(),sum(not r['identical']for r in rows))
