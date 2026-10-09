"""Causally execute the real adapter with altered private bindings."""
import argparse,copy,json
from pathlib import Path
from adapt_slice import adapt,sha
def main():
    p=argparse.ArgumentParser()
    for n in ('llvm-dll','guest','host','record','recovery'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();folder=a.guest.parent/'adapter-controls'
    if folder.exists() or a.record.exists():raise ValueError('Fresh adapter controls required')
    folder.mkdir();original=json.loads(a.recovery.read_text());mutations=[];controls=[]
    for key in ('image_sha256','code_sha256','code_bytes','profile'):
        changed=copy.deepcopy(original);changed[key]=0 if isinstance(changed[key],int) else '0'*64;mutations.append((key,changed))
    for key in ('entry','entry_va','end_va','size_bytes','file_offset','bundle_offset','guest_ir_sha256'):
        changed=copy.deepcopy(original);old=changed['functions'][0][key];changed['functions'][0][key]=old^1 if isinstance(old,int) else '0'*64;mutations.append(('function-'+key,changed))
    changed=copy.deepcopy(original);changed['functions'].pop();mutations.append(('missing-shared-tail',changed))
    changed=copy.deepcopy(original);changed['global_pages'][1]+=4096;mutations.append(('global-page',changed))
    for name,data in mutations:
        recovery=folder/(name+'.json');recovery.write_text(json.dumps(data));host=folder/(name+'.ll');record=folder/(name+'-layout.json')
        try:adapt(a.llvm_dll,a.guest,host,record,recovery)
        except ValueError as e:
            if host.exists() or record.exists():raise ValueError('Rejected adapter published an artifact')
            controls.append({'name':name,'rejected':True,'diagnostic':str(e)});continue
        raise ValueError('Changed adapter binding admitted: '+name)
    changed=folder/'changed-IR.ll';changed.write_bytes(a.guest.read_bytes()+b'\n; authored identity control\n')
    try:adapt(a.llvm_dll,changed,folder/'changed-host.ll',folder/'changed-layout.json',a.recovery)
    except ValueError as e:controls.append({'name':'linked-IR-byte-identity','rejected':True,'diagnostic':str(e)})
    else:raise ValueError('Changed IR admitted')
    a.record.write_text(json.dumps({'schema_version':1,'passed':True,'controls':controls,'source_sha256':sha(__file__)},indent=2)+'\n');print('Adapter admission controls:',len(controls))
if __name__=='__main__':main()
