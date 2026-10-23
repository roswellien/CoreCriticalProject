"""Finite current141 whole 5F2000 page relation probe; ordinary exports only.

Measures, for every sequence/phase/side, the whole 4096-byte original141
constructor-global endpoint against native141 source6 O0/O2, plus each branch's
own consecutive carry (AFTER p == BEFORE p+1) and own per-phase change set.
Differences are recorded as exact DWORD offsets/values; no pointer alias,
mask, source no-write or input-provenance claim is made. Hashes whole index and
payload before/after. Grants no paired141 or accepted credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ORIGINAL_VALIDATION=('reports/m4-original141/root-capture-validation-r3/report.json','e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c')
NATIVE_SOURCE='reports/m4-startup141-source/combined-source-provider-r6/report.json'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dword_diff(a,b):
 return[(o,x,y)for o,(x,y)in enumerate(zip(struct.iter_unpack('<I',a),struct.iter_unpack('<I',b)))if x!=y]
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);helper=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');spec=importlib.util.spec_from_file_location('ordinary_entries',helper);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 V=json.loads(pin(R/ORIGINAL_VALIDATION[0],ORIGINAL_VALIDATION[1]).read_bytes());assert V['passed']and V['reader_closed']
 N=json.loads(pin(R/NATIVE_SOURCE).read_bytes());assert N['passed']is True and N['reader_closed']is True and N['paired_export_readers_closed']is True
 bundles={}
 for branch,row,pattern in [('original',next(e for e in V['paired_exports']if e['branch']=='original'),re.compile(r'phase/[0-5]/\d+/constructor-global-(?:before|after)\.bin')),
                            *[(lv,next(e for e in N['paired_exports']if e['branch']==lv),re.compile(r'sequence-[0-5]/phase-\d+-(?:before|after)-constructor-global5F2000\.bin'))for lv in('O0','O2')]]:
  i=pin(row['index_path'],row['index_sha256']);p=pin(row['payload_path'],row['payload_sha256']);es=D.entries(i,pattern);assert len(es)==1692,(branch,len(es));bundles[branch]=(i,p,es)
 def page(branch,seq,phase,side):
  i,p,es=bundles[branch];k=f'phase/{seq}/{phase}/constructor-global-{side}.bin'if branch=='original'else f'sequence-{seq}/phase-{phase}-{side}-constructor-global5F2000.bin'
  z=es[k];assert z['bytes']==4096,(k,z['bytes']);f=handles[branch];f.seek(z['offset']);b=f.read(4096);assert len(b)==4096 and hashlib.sha256(b).hexdigest()==z['sha256'],k;return b
 handles={b:v[1].open('rb')for b,v in bundles.items()}
 try:
  pages={(b,s,ph,sd):page(b,s,ph,sd)for b in bundles for s in range(6)for ph in range(141)for sd in('before','after')}
 finally:
  for f in handles.values():f.close()
 carry={b:sum(pages[(b,s,ph,'after')]==pages[(b,s,ph+1,'before')]for s in range(6)for ph in range(140))for b in bundles}
 change={b:{s:[ph for ph in range(141)if pages[(b,s,ph,'before')]!=pages[(b,s,ph,'after')]]for s in range(6)}for b in bundles}
 change_offsets={b:{s:{ph:[o for o,_,_ in dword_diff(pages[(b,s,ph,'before')],pages[(b,s,ph,'after')])]for ph in change[b][s]}for s in range(6)}for b in bundles}
 paired=[];diff_offsets=collections.Counter();equal=0
 for lv in('O0','O2'):
  for s in range(6):
   for ph in range(141):
    for sd in('before','after'):
     d=dword_diff(pages[('original',s,ph,sd)],pages[(lv,s,ph,sd)])
     if not d:equal+=1
     else:
      diff_offsets.update(o*4 for o,_,_ in d);paired.append(dict(level=lv,sequence=s,phase=ph,side=sd,dwords=[dict(offset=o*4,original=x,native=y)for o,x,y in d]))
 same_change_set={lv:all(change['original'][s]==change[lv][s]and all(change_offsets['original'][s][ph]==change_offsets[lv][s][ph]for ph in change['original'][s])for s in range(6))for lv in('O0','O2')}
 for i,p,es in bundles.values():assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)],'Whole index/payload unchanged after reads'
 rp=out/'global5F2000-relations.json';rp.write_text(json.dumps(dict(unequal_paired_endpoints=paired,own_change_phases=change,own_change_dword_offsets=change_offsets),indent=1)+'\n');pin(rp);pin(sys.executable)
 report=dict(passed=True,scope='Measured whole5F2000 original141 vs native141 source6 endpoint equality, own consecutive carry and own change sets; measurement only, no alias/mask/source no-write/provenance or paired141 claim',
  paired_endpoints=3384,paired_whole_page_equal=equal,paired_whole_page_unequal=len(paired),distinct_unequal_byte_offsets=sorted(diff_offsets),own_consecutive_carry_equal={b:dict(equal=v,of=840)for b,v in carry.items()},
  own_change_phase_counts={b:{str(s):len(v)for s,v in d.items()}for b,d in change.items()},original_native_same_change_phases_and_offsets=same_change_set,
  output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),source_no_write_claim=False,pointer_alias_claim=False,capture_archive_opened=False,canonical_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('paired_whole_page_equal','paired_whole_page_unequal','distinct_unequal_byte_offsets','own_consecutive_carry_equal','own_change_phase_counts','original_native_same_change_phases_and_offsets')}))
if __name__=='__main__':main(sys.argv[1])
