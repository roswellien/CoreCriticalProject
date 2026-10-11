"""Physical named-export and finite affine source frame proof, no execution."""
from pathlib import Path
import hashlib,json,re,struct,sys

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-constructor-original'
def main(name):
    out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={}
    def pin(p,h=None):
        p=Path(p).resolve();raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert h is None or h==digest;files[str(p)]=digest;return raw
    sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
    pin(ROOT/'tools/analysis/pe.py')
    images={}
    for name_,digest in [('MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')]:
        images[name_]=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs'/name_,digest))
    game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
    def raw(image,pc,width):offset,_=image.rva_range(pc-image.image_base,width);return image.data[offset:offset+width]
    exports={}
    for ordinal in(823,825):
        rows=[row for row in images['MFC42.DLL'].exports()if row['ordinal']==ordinal]
        assert len(rows)==1 and not rows[0].get('forwarder')
        exports[str(ordinal)]=dict(rows[0],image_base=images['MFC42.DLL'].image_base,target=images['MFC42.DLL'].image_base+rows[0]['rva'])
    named={}
    for name_ in('malloc','free'):
        row=next(row for row in images['MSVCRT.DLL'].exports()if name_ in row['names']);named[name_]=dict(row,target=images['MSVCRT.DLL'].image_base+row['rva'])
    imports={images['MFC42.DLL'].image_base+row['iat_rva']:dict(library=g['library'],**row)for g in images['MFC42.DLL'].imports()for row in g['symbols']}
    assert imports[0x5f49814c]['name']=='malloc'and imports[0x5f498148]['name']=='free'
    assert raw(game,0x5abd26,6)==bytes.fromhex('ff25bcb45b00')and raw(game,0x5abd1a,6)==bytes.fromhex('ff25c8b45b00')
    interface=json.loads(pin(ROOT/'reports/m4-mfc-review/interface-r1/instruction-contracts.json','94fddd9fc34c0d1dff5100ae8a9f5c66b39e66854a1e5a2d07ac81966656dfeb'))
    source={r['pc']:r for r in interface['instructions']}
    for row in source.values():assert raw(images['MFC42.DLL'],row['pc'],row['width']).hex()==row['bytes_hex']
    # Every negative ESP adjustment before the real indirect CALL is a
    # physically pinned PUSH/CALL. Nothing is inferred from a declared PC.
    alloc_sites=[0x5f401ea0,0x5f401ea7,0x5f401eac,0x5f401eb3,0x5f401eb4,0x5f401eb5]
    release_sites=[0x5f401782,0x5f401786]
    ledgers={}
    for role,sites in [('MFC823_to_malloc',alloc_sites),('MFC825_to_free',release_sites)]:
        delta=0;rows=[]
        for pc in sites:
            row=source[pc];assert row['mnemonic']in('push','call');delta-=4
            rows.append(dict(PC=pc,bytes_hex=row['bytes_hex'],mnemonic=row['mnemonic'],operands=row['operands'],ESP_delta_after=delta))
        ledgers[role]=dict(rows=rows,entry_to_callee_delta=delta)
    assert ledgers['MFC823_to_malloc']['entry_to_callee_delta']==-24 and ledgers['MFC825_to_free']['entry_to_callee_delta']==-8
    decode_base=ROOT/'reports/m4-crt-allocation-recovery/recovery-r1'
    decoded={}
    for filename in('malloc-wrapper-decode.stdout','malloc-worker-hot-decode.stdout','malloc-size-decode.stdout','malloc-round-mode1-decode.stdout','free-hot-decode.stdout','free-mode1-cold-decode.stdout'):
        text=pin(decode_base/filename).decode()
        for line in text.splitlines():
            hit=re.match(r'^([0-9a-fA-F]+):\s*((?:[0-9a-fA-F]{2}\s+)+)\s*(\w+)\s*(.*)$',line)
            if hit:
                pc=int(hit[1],16);bytes_=bytes.fromhex(hit[2]);assert raw(images['MSVCRT.DLL'],pc,len(bytes_))==bytes_
                row=dict(PC=pc,bytes_hex=bytes_.hex(),mnemonic=hit[3],operands=hit[4].strip());assert pc not in decoded or decoded[pc]==row;decoded[pc]=row
    # Conditional source path: CRT heap mode1, normal rounded nonzero allocation
    # and nonNULL free. It is a frame derivation, not a new reached-path claim.
    malloc_adjustments=[(0x780012b3,-4),(0x780012b9,-4),(0x780012bd,-4),(0x780012d0,-4),(0x780012d4,-4),(0x780012e3,-4),(0x780012e6,-4),(0x780012e8,-4),(0x780012ed,-4),(0x780012f8,-4),(0x78001300,-12),(0x78001303,-4),(0x78001304,-4),(0x78001305,-4),(0x7800cca6,-4),(0x78001377,-4),(0x78001379,-4),(0x7800137f,-4)]
    free_adjustments=[(0x78001390,-4),(0x78001393,-4),(0x78001395,-4),(0x7800139a,-4),(0x780013a5,-4),(0x780013ad,-24),(0x780013b0,-4),(0x780013b1,-4),(0x780013b2,-4),(0x7800cc39,-4),(0x78001428,-4),(0x7800142a,-4),(0x78001430,-4)]
    for role,sites,total in [('CRT_malloc_to_HeapAlloc',malloc_adjustments,-80),('CRT_free_to_HeapFree',free_adjustments,-72)]:
        delta=0;rows=[]
        for pc,adjust in sites:
            row=decoded[pc]
            if row['mnemonic']in('push','call'):assert adjust==-4
            else:assert row['mnemonic']=='sub'and row['operands']in('esp, 0xc','esp, 0x18')and adjust in(-12,-24)
            delta+=adjust;rows.append(dict(row,ESP_adjustment=adjust,ESP_delta_after=delta))
        assert delta==total;ledgers[role]=dict(rows=rows,entry_to_API_delta=delta)
    assert decoded[0x7800137f]['bytes_hex']=='ff1594e00278'and decoded[0x78001430]['bytes_hex']=='ff1590e00278'
    assert exports['823']['target']==alloc_sites[0]and exports['825']['target']==release_sites[0]
    report=dict(passed=True,scope='Physical source-only named export/owning IAT chain and finite affine frames; no original writer or numerical/AFTER inputs',MFC_exports=exports,CRT_named_exports=named,game_MFC_IAT=dict(ordinal823=dict(trampoline=0x5abd26,cell=0x5bb4bc,raw_bytes='ff25bcb45b00'),ordinal825=dict(trampoline=0x5abd1a,cell=0x5bb4c8,raw_bytes='ff25c8b45b00')),MFC_CRT_IAT={str(cell):imports[cell]for cell in(0x5f49814c,0x5f498148)},source_frames=ledgers,MFC823_entry_to_HeapAlloc_before_delta=-104,MFC825_entry_to_HeapFree_before_delta=-80,HeapAlloc_source_saved_return=0x78001385,HeapFree_source_saved_return=0x78001436,normal_game_CALL_return_frame_delta=4,finite_path_predicates=['CRT heap mode1','Normal request rounding/no allocation failure','NonNULL free pointer'],new_constructor_reached_path_observed=False,allocation_getter_counts_unmeasured=True,source_AFTER_seed=False,files=files)
    pin(__file__);report['files']=files
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),ordinal823=hex(exports['823']['target']),ordinal825=hex(exports['825']['target']),MFC823_HeapAlloc_delta=-104)))

if __name__=='__main__':main(sys.argv[1])
