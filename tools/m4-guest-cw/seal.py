"""Author evidence closure; independent acceptance remains separate."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 out=ROOT/'reports/m4-guest-cw/author-review-r1';assert not out.exists();paths={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();value=sha(p);assert h is None or value==h,(p,h,value);paths[str(p)]=value
 hardware=ROOT/'reports/m4-crt-cw/closure-r1/pins.json';assert sha(hardware)=='ebdef8baffc1d06d999b10c6ed5a30f339c61875c1fe75caf3cc9ce5ddcb3c90'
 hm=load(hardware);hm=hm.get('files',hm)
 for p,h in hm.items():bind(p,h)
 bind(hardware)
 build_path=ROOT/'reports/m4-guest-cw/build-r1/build.json';b=load(build_path);assert b['passed']
 for group in ('source_files','tool_files','artifacts'):
  for p,h in b[group].items():bind(p,h)
 for item in b['literal_source_copies']:bind(item['preserved_path'],item['sha256'])
 r=load(ROOT/'reports/m4-guest-cw/run-r1/report.json');c=load(ROOT/'reports/m4-guest-cw/comparison-r2/report.json');assert r['passed'] and c['passed'] and c['differences']==0 and c['native_records']==131072 and len(c['observer_controls'])==114
 for p,h in load(ROOT/'reports/m4-guest-cw/run-r1/pins.json').items():bind(p,h)
 for p,h in load(ROOT/'reports/m4-guest-cw/comparison-r2/pins.json')['files'].items():bind(p,h)
 for directory in ('build-r1','run-r1','comparison-r1','comparison-r2'):
  for p in (ROOT/'reports/m4-guest-cw'/directory).rglob('*'):
   if p.is_file() and 'compiler-temp' not in p.parts:bind(p)
 out.mkdir(parents=True)
 sources=[]
 for directory in (ROOT/'tools/m4-guest-cw',ROOT/'tests/m4-guest-cw'):
  sources.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 sources.append(ROOT/'docs/m4-guest-cw-contract.md')
 copies=[]
 for p in sources:
  bind(p);target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes());bind(target,sha(p));copies.append({'original_path':str(p),'preserved_path':str(target),'sha256':sha(p)})
 report={'passed':True,'scope':'Author bounded guest CW transfer gate; independent review pending; numerical/provider/full M4 incomplete','build_path':str(build_path),'build_sha256':sha(build_path),'source_tool_artifact_counts':{k:len(b[k]) for k in ('source_files','tool_files','artifacts')},'hardware_records':131072,'native_records':131072,'all_input_words_per_optimization':65536,'optimizations':['O0','O2'],'differences':0,'authored_controls_per_optimization':28,'actual_worker_controls':14,'observer_corruptions':114,'literal_final_sources':copies,'preserved_failed_comparison':'comparison-r1 independent SS offset error; helpers/raws unchanged','physical_bindings_before_report':len(paths),'numerical_host_CW_synchronization_admitted':False,'provider_controlfp_admitted':False,'runtime_r9_mutated':False,'whole_M4_complete':False,'limits':['TOP0/SW0/empty tags/MXCSR1F80 only; occupied/pending states denied','One measured host; no universal CPU or reserved precision arithmetic claim','Compiler adapter must pass a stable nonnull Context and propagate its retained fault','No active numerical lowering, original provider body execution, CRT controlfp/87, full CRT/SEH/startup/menu credit','Sequential fresh ordinary private directories; concurrent writers/reparse/dangling links excluded','Post-build current tool hashes and recorded invocation are distinct; no full host process dependency attestation']}
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');bind(rp);(out/'pins.json').write_text(json.dumps({'files':paths},indent=2)+'\n');print('Author closure:',len(paths),'bindings',sha(rp),sha(out/'pins.json'))
if __name__=='__main__':main()
