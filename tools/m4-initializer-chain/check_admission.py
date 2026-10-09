"""Actual adapter rejections before native artifact publication."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from adapt_slice import adapt,admit_slice_record,sha
def main():
 p=argparse.ArgumentParser()
 for n in ('llvm-dll','guest','host','record','slice-record'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();controls=[]
 with tempfile.TemporaryDirectory(dir=a.guest.parent,prefix='adapter-controls-') as folder:
  root=Path(folder);original=json.loads(a.slice_record.read_text())
  mutations=[]
  for key in ('image_sha256','code_sha256','code_bytes','profile'):
   x=copy.deepcopy(original);x[key]=0 if isinstance(x[key],int) else '0'*64;mutations.append((key,x))
  for key in ('entry_va','end_va','size_bytes','file_offset','bundle_offset','guest_ir_sha256'):
   x=copy.deepcopy(original);v=x['functions'][1][key];x['functions'][1][key]=0 if isinstance(v,int) else '0'*64;mutations.append(('function-'+key,x))
  x=copy.deepcopy(original);x['functions'].pop();mutations.append(('missing-complete-callee',x))
  x=copy.deepcopy(original);x['stack_page']['required_relative_span']=[0,4];mutations.append(('missing-callee-stack-span',x))
  x=copy.deepcopy(original);x['global_page']['base']+=4096;mutations.append(('shared-global-page',x))
  for name,x in mutations:
   path=root/(name+'.json');path.write_text(json.dumps(x))
   try:admit_slice_record(path)
   except ValueError as e:controls.append({'name':name,'rejected':True,'reason':str(e)});continue
   raise ValueError('Changed metadata admitted: '+name)
  changed=root/'changed.ll';changed.write_bytes(a.guest.read_bytes()+b'\n; authored identity mutation\n');host=root/'host.ll';record=root/'layout.json'
  try:adapt(a.llvm_dll,changed,host,record,a.slice_record)
  except ValueError as e:
   if host.exists() or record.exists():raise ValueError('Rejected adapter published output')
   controls.append({'name':'linked-IR-byte-identity','rejected':True,'reason':str(e)})
  else:raise ValueError('Changed linked IR admitted')
 a.record.write_text(json.dumps({'schema_version':1,'passed':True,'controls':controls,'source_sha256':sha(Path(__file__))},indent=2)+'\n')
 print('Adapter admission controls:',len(controls))
if __name__=='__main__':main()
