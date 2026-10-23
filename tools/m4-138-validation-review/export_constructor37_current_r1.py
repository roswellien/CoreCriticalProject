"""Root-admitted future reader: exact native37 full raw exports, no model or writer."""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
EH='a3945f68857cced5af2b946302ddf92992b2ba4d1440e3fad0e266ab4e9801e6';VH='ef10a083df6db99eaea0bf3fa03332970cb4f7b3d4ff329f9f12ae1e946b7861'
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();files={};exports=[];reader=None;export=None;passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  ep=R/'reports/m4-constructor-native/fixture-execution-r4/report.json';vp=R/'reports/m4-constructor-native/fixture-validation-r4/report.json';e=json.loads(pin(ep,EH).read_bytes());v=json.loads(pin(vp,VH).read_bytes())
  assert e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==2 and v['passed']and v['reader_closed']and v['execution_sha256']==EH and v['initializer_credit']==0
  assert e['build_sha256']==v['build_sha256']=='0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18'and e['preparation_sha256']==v['preparation_sha256']=='f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0'
  assert len(v['cases'])==12 and all(c['phases']==37 and c['new_allocator_calls']==6 and c['genuine_NULL_calls']==2 and c['getter_calls']==2 and c['whole_new_owner_cleanup']==6 for c in v['cases'])
  D=load(R/'tools/m4-crt-allocation-root/run_v2.py','current_constructor37_direct');EX=load(R/'tools/m4-joint-startup131/paired_exports.py','current_constructor37_raw')
  for level in('O0','O2'):
   reader=D.DirectSet(Path(e['runs'][level]['capture']),pin);export=EX.Export(out/'raw-export',level,reader.path,pin)
   # Explicit all-key equality transport, no selected-subset policy override.
   for key in sorted(reader.entries):export.write(key,reader.data(key))
   assert set(export.entries)==set(reader.entries);row=export.finish();export=None;assert row['logical_files']==len(reader.entries);exports.append(row);reader.close();reader=None
  pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if export is not None:export.close()
  if reader is not None:reader.close()
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Current strict native37 O0/O2 complete authentic raw equality transport for independent own-BEFORE literal evaluator/original pair. This export executes no source/native model.',execution_sha256=EH,strict_validation_sha256=VH,paired_exports=exports,reader_closed=True,paired_export_readers_closed=True,exact_all_logical_files_copied=True,canonical_reader_sessions=2 if passed else None,worker_launched=False,source_AFTER_seed=False,initializer_credit=0,files=files),indent=2)+'\n');print(q,hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
