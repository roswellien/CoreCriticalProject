"""Additive exact source composition. Frozen ancestors are never modified."""
import hashlib,json,pathlib,shutil,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-matherr'
OLD=ROOT/'reports/m4-crt-entry-data/preparation-r4'
HERE=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 for name in ('seed.hpp','main_v2.inc','observations.hpp','composition.cpp'):
  shutil.copyfile(OLD/name,out/(name+'.ancestor'))
  shutil.copyfile(HERE/name,out/name) if (HERE/name).exists() else shutil.copyfile(OLD/name,out/name)
 ancestor=ROOT/'tools/m4-crt-matherr/paired/paired_context.hpp'
 text=ancestor.read_text();tail='extern "C" unsigned __remill_read_memory_32(void *p,unsigned a) {'
 assert text.count(tail)==1
 derived=text.split(tail)[0]
 needle='void (*test_after_event)(Context &, unsigned){};'
 assert derived.count(needle)==1
 derived=derived.replace(needle,needle+'\n    void (*test_before_execute)(Context &){};')
 needle='try { token=sub_7800b38f(&state,entry,this); }'
 assert derived.count(needle)==1
 derived=derived.replace(needle,'try { if(test_before_execute)test_before_execute(*this); token=sub_7800b38f(&state,entry,this); }')
 (out/'matherr_context.hpp').write_text(derived)
 shutil.copyfile(ancestor,out/'matherr_context.hpp.ancestor')
 files={str(p):sha(p)for p in [*out.iterdir(),pathlib.Path(__file__).resolve(),OLD/'pins.json',ROOT/'reports/m4-crt-entry-data/build-r6/build.json',ancestor]}
 for name in ('O0','O2'):
  p=ROOT/f'reports/m4-crt-matherr/paired-native-build-r7/native-{name}.obj';files[str(p)]=sha(p)
 report=dict(passed=True,scope='Additive exact typed-dispatch matherr composition preparation only',State_reseed_after_writer=False,State_reseed_after_matherr=False,callback_invoked=False,matherr_Context_derivative='Remove standalone global bridge tail; add before-execute observation callback only; retain BridgeAbort',native_component_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
