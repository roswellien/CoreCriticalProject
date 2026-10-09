"""Reject modified private extraction and IR before native adapter output."""
import argparse
import json
from pathlib import Path
import tempfile
from adapt_slice import adapt,admit_slice_record,digest
def main():
    p=argparse.ArgumentParser()
    for name in ('llvm-dll','guest','host','record','slice-record'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();controls=[]
    with tempfile.TemporaryDirectory(dir=a.guest.parent,prefix='adapter-controls-') as folder:
        root=Path(folder)
        original=json.loads(a.slice_record.read_text())
        for key in ('image_sha256','code_sha256','entry_va','end_va','code_bytes','code_file_offset'):
            x=dict(original);x[key]=0 if isinstance(x[key],int) else '0'*64
            path=root/(key+'.json');path.write_text(json.dumps(x))
            try:admit_slice_record(path)
            except ValueError as e:controls.append({'name':key,'rejected':True,'reason':str(e)});continue
            raise ValueError('Bad extraction metadata admitted '+key)
        changed=root/'changed.ll';changed.write_bytes(a.guest.read_bytes()+b'\n; authored identity mutation\n')
        out=root/'host.ll';record=root/'layout.json'
        try:adapt(a.llvm_dll,changed,out,record,a.slice_record)
        except ValueError as e:
            if out.exists() or record.exists():raise ValueError('Rejected adapter published output')
            controls.append({'name':'guest-IR-byte-identity','rejected':True,'reason':str(e)})
        else:raise ValueError('Changed generated IR admitted')
    a.record.write_text(json.dumps({'schema_version':1,'passed':True,'controls':controls,
                                   'source_sha256':digest(Path(__file__))},indent=2)+'\n')
    print('Adapter admission controls:',len(controls))
if __name__=='__main__':main()
