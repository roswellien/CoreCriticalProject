"""ROOT-admitted finite original18/native36 structural joins; no capture reader/model."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ORIGINAL_SHA='8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899'
NATIVE_CARRIED_SHA='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'
ROOTS=(0x4103f0,0x410440,0x459b40)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission_path,admission_sha,native36_path,native36_sha,name):
 admission_path=Path(admission_path).resolve();assert sha(admission_path)==admission_sha;admission=json.loads(admission_path.read_bytes());assert admission['passed']is True and admission['independent_review']is True and admission['scope_identity']=='current141_constructor_structural54_pair'and admission['original18_sha256']==ORIGINAL_SHA and admission['native36_sha256']==native36_sha
 admitted={}
 for p,h in admission['files'].items():
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json';assert str(p)not in admitted and sha(p)==h;admitted[str(p)]=h
 admitted[str(admission_path)]=admission_sha
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();files={};cases=[];passed=False;stage={}
 def need(v,m):
  if not v:raise ValueError(m)
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(p.is_relative_to(out)or admitted.get(str(p))==v,'Every current physical external input admitted before use');need(h is None or h==v,'Exact current external identity');need(str(p)not in files or files[str(p)]==v,'Unique consistent input identity');files[str(p)]=v;return p
 def get(p,h=None):return json.loads(pin(p,h).read_bytes())
 def audit(event,args):
  if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0;reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
  if reading:
   if p.suffix.lower()=='.pyc':raise PermissionError('Physical source only; cached bytecode refused')
   need(p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and(p.is_relative_to(out)or str(p)in admitted),'No reader/archive/model or unadmitted indirect input')
 sys.addaudithook(audit)
 try:
  original_path=R/'reports/m4-original141-source/source-r4-constructors/report.json';original=get(original_path,ORIGINAL_SHA);native_path=Path(native36_path).resolve();native=get(native_path,native36_sha)
  # Admission precedes every per-case equality input. A failed aggregate or old
  # native37 endpoint is never an oracle for this current finite gate.
  for label,rec,count in [('original18',original,18),('native36',native,36)]:
   need(rec['passed']is True and rec['ordinary_reader_closed']is True and rec['canonical_reader_opened']is False and rec['source_AFTER_seed']is False and rec['initializer_credit']==0 and len(rec['cases'])==count,'Exact passed/closed current '+label+' source gate')
   for p,h in rec['files'].items():
    path=Path(p).resolve();need(path.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and path.name!='transport.json'and admitted.get(str(path))==h,'Every source gate physical ordinary dependency previously admitted')
  need(native['current_native_source_sha256']==NATIVE_CARRIED_SHA and native['current_original18_sha256']==ORIGINAL_SHA and native['configuration_sha256']=='a5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0','Current fullcarried141/source18 lineage only')
  need(native['owner_export_sha256']==admission['owner_export_sha256'],'Exact ROOT-admitted new genuine owner-cut source input relation')
  main_path=Path(admission['native36_source_main_path']).resolve();need(native['files'].get(str(main_path))==admission['native36_source_main_sha256']==admitted.get(str(main_path)),'Actual source evaluator physical identity bound by ROOT')
  need({(v['sequence'],v['root'])for v in original['cases']}=={(s,r)for s in range(6)for r in ROOTS},'Original18 complete distinct extent')
  need({(v['branch'],v['sequence'],v['root'])for v in native['cases']}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in ROOTS},'Native36 complete distinct extent')
  carried_path=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';carried_gate=get(carried_path,NATIVE_CARRIED_SHA);need(carried_gate['passed']and carried_gate['reader_closed']and carried_gate['paired_export_readers_closed'],'Current independent carried141 source gate')
  jp=carried_path.parent/'Constructor-carried-source-derivations.json';carried=get(jp,carried_gate['files'][str(jp.resolve())]);need(len(carried)==36 and {(v['level'],v['sequence'],v['root'])for v in carried}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in ROOTS},'Every exact current carried constructor row')
  pp=pin(R/'tools/m4-startup141-paired/constructor_relations141_v1.py','9300d8f5982c72a7f7c918a18fe867349d2ec0a02db92ed3761a64291ed6c018')
  spec=importlib.util.spec_from_file_location('current141_constructor_pure_policy',pp);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
  for seq in range(6):
   firsta=get(original_path.parent/f'original-{seq}-{ROOTS[0]}/input.json');earlier={}
   for root in ROOTS:
    a=get(original_path.parent/f'original-{seq}-{root}/source-derivation.json');ain=get(original_path.parent/f'original-{seq}-{root}/input.json');earlier[root]=a;acase=next(v for v in original['cases']if(v['sequence'],v['root'])==(seq,root))
    for level in('O0','O2'):
     stage=dict(sequence=seq,root=root,branch=level);base=native_path.parent/f'{level}-{seq}-{root}';b=get(base/'source-derivation.json');binp=get(base/'input.json');firstb=get(native_path.parent/f'{level}-{seq}-{ROOTS[0]}/input.json');bcase=next(v for v in native['cases']if(v['branch'],v['sequence'],v['root'])==(level,seq,root));row=next(v for v in carried if(v['level'],v['sequence'],v['root'])==(level,seq,root));relation=P.compare(seq,root,level,a,b,ain,binp,firsta,firstb,earlier,acase,bcase,row);need(relation['complete_constructor_acceptance_gate']is False and relation['original_whole_State_claim']is False,'Finite structural scope remains explicit');cases.append(relation)
  need(len(cases)==36 and len({(v['branch'],v['sequence'],v['root'])for v in cases})==36,'All current54 source cases participate in36 distinct structural joins');pin(__file__);pin(admission_path,admission_sha);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p,h in files.items():need(sha(p)==h,'Final physical equality input conservation')
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Finite current original18/native36 literal structural54 pairing only; all inherited24 relation assertions retained in unchanged pure policy',original18_sha256=ORIGINAL_SHA,native36_sha256=native36_sha,cases=cases,frontier=stage,source_case_extent=54,structural_pair_extent=36 if passed else len(cases),source_AFTER_seed=False,canonical_reader_opened=False,ordinary_capture_reader_opened=False,source_model_executed=False,original_whole_State_claim=False,complete_constructor_acceptance_gate=False,native_input_carry_policy_review_pending=True,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
