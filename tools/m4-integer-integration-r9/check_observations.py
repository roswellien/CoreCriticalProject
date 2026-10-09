"""Observe combined real callbacks; no executable implementation in this model."""
import argparse,hashlib,json,struct
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--logs',type=Path,nargs=2,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh combined observer report required')
    first=bytearray(4096);second=bytes(4096);third=bytearray(4096)
    struct.pack_into('<16I',first,0xd0,3,0xbf000000,0x3f000000,0x3d4ccccd,6,0xbf800000,0,0,2,0x3f800000,0,0,1,0xbf800000,0,0);first[0x110]=1
    struct.pack_into('<I',third,0x2b8,0x60b2f4);struct.pack_into('<I',third,0x44c,0xfffff)
    expected={'passed':True,'registered_roots':16,'actual_callbacks':16,'ledger_items':145,'selected_table_slots':16,'full_ledger_completed':False,'cpu_eax':0,'cpu_ecx':0,'cpu_edx':0,'cpu_esp':0x20100000,'cpu_eip':0xfffffff0,'defined_flags':0x44,'604000_page_sha256':hashlib.sha256(first).hexdigest(),'605000_page_sha256':hashlib.sha256(second).hexdigest(),'60b000_page_sha256':hashlib.sha256(third).hexdigest(),'persistent_State_seeded':True}
    observations=[]
    for log in a.logs:
        records=[json.loads(line) for line in log.read_text(encoding='utf-8-sig').splitlines() if line.startswith('{')]
        if records!=[expected]:raise ValueError('Actual combined observations differ: '+str(log))
        observations.append({'path':str(log.resolve()),'sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'actual':records[0]})
    controls=[]
    for key,value in expected.items():
        changed=dict(expected);changed[key]=not value if isinstance(value,bool) else ('changed' if isinstance(value,str) else value^1)
        if changed==expected:raise ValueError('Observer fixture failed')
        controls.append({'field':key,'rejected':True})
    a.output.write_text(json.dumps({'schema_version':1,'passed':True,'scope':'Actual compiled16selectedtabletargets on one owned image/stack/persistentState; no full CRT ledger or menus','observations':observations,'observer_controls':controls},indent=2)+'\n');print(json.dumps({'passed':True,'optimization_levels':2,'observer_controls':len(controls)}))
if __name__=='__main__':main()
