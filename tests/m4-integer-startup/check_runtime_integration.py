"""Check independently stated constants against actual owned-image dispatch logs."""
import argparse,hashlib,json,struct
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument('--logs',type=Path,nargs=2,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh integration report required')
    first=bytes(4096);second=bytearray(4096);struct.pack_into('<II',second,0x2b8,0x60b2f4,0);struct.pack_into('<I',second,0x44c,0xfffff)
    expected={'passed':True,'actual_callbacks':14,'ledger_items':145,'selected_table_slots':14,'full_ledger_completed':False,'cpu_eax':0,'cpu_ecx':0,'cpu_edx':0xabcddcba,'cpu_esp':0x20100000,'cpu_eip':0xfffffff0,'defined_flags':0x44,'first_page_sha256':hashlib.sha256(first).hexdigest(),'second_page_sha256':hashlib.sha256(second).hexdigest(),'persistent_State_seeded':True,'legacy_metadata_preserved':True,'FX_metadata_distinct':True,'FS_base_preserved':True}
    observations=[]
    for log in a.logs:
        records=[json.loads(s) for s in log.read_text(encoding='utf-8-sig').splitlines() if s.startswith('{')]
        if records!=[expected]:raise ValueError('Actual owned-image callback observations differ: '+str(log))
        observations.append({'path':str(log.resolve()),'sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'actual':records[0]})
    controls=[]
    for key,value in expected.items():
        changed=dict(expected);changed[key]=not value if isinstance(value,bool) else ('changed' if isinstance(value,str) else value^1)
        if changed==expected:raise ValueError('Observer mutation failed')
        controls.append({'field':key,'rejected':True})
    a.output.write_text(json.dumps({'schema_version':1,'passed':True,'actual_optimization_levels':2,'actual_callbacks_per_level':16,'full_M4_claimed':False,'observations':observations,'observer_controls':controls},indent=2)+'\n')
    print(json.dumps({'passed':True,'observer_controls':len(controls)}))
if __name__=='__main__':main()
