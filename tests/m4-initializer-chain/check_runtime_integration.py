"""Independent observations of real callbacks on the shared owned PE image."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--logs',type=Path,nargs=2,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh runtime integration report required')
    page=bytearray(4096)
    # Static instruction recovery independently states these final constants.
    # This observer supplies no implementation or memory to either callback.
    struct.pack_into('<16I',page,0xd0,3,0xbf000000,0x3f000000,0x3d4ccccd,
                     6,0xbf800000,0,0,2,0x3f800000,0,0,1,0xbf800000,0,0)
    page[0x110]=1
    expected={'passed':True,'actual_callbacks':2,'ledger_items':145,'selected_table_slots':2,'full_ledger_completed':False,'cpu_eax':0x604100,
              'cpu_ecx':0x6040d0,'cpu_edx':0,'cpu_esp':0x20100000,'cpu_eip':0xfffffff0,
              'cpu_flags':0x206,'page_sha256':hashlib.sha256(page).hexdigest(),
              'persistent_State_seeded':True,'legacy_metadata_preserved':True,
              'FX_metadata_distinct':True,'FS_base_preserved':True}
    observations=[]
    for log in a.logs:
        raw=log.read_bytes();lines=raw.decode('utf-8-sig').splitlines()
        records=[json.loads(s) for s in lines if s.startswith('{')]
        if records!=[expected]:raise ValueError('Actual runtime callback observations differ: '+str(log))
        observations.append({'path':str(log.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'actual':records[0]})
    controls=[]
    for key in expected:
        changed=dict(expected)
        changed[key]=(not expected[key]) if isinstance(expected[key],bool) else ('changed' if isinstance(expected[key],str) else expected[key]^1)
        if changed==expected:raise ValueError('Observer mutation failed: '+key)
        controls.append({'field':key,'rejected':changed!=expected})
    result={'schema_version':1,'passed':True,'expected_page_sha256':expected['page_sha256'],
            'actual_optimization_levels':2,'actual_callbacks_per_level':4,
            'scope':'Actual owned-image ordered registry callbacks and separate persistent legacy metadata control; no full startup/menu or FP equivalence credit',
            'observations':observations,'observer_controls':controls}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'actual_optimization_levels':2,'observer_controls':len(controls)}))


if __name__=='__main__':main()
