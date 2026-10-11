"""Independent literal four-root FS, scratch-frame and size-specific interface."""
from collections import Counter
import hashlib, importlib.util, json, re, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=R/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh additive review');out.mkdir(parents=True)
    pins={};counts=Counter();rows=[]
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact source interface input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Immutable input');pins[str(p)]=v;return p
    def read(p):return json.loads(pin(p).read_bytes())
    source=read(R/'reports/m4-lockit-source/recovery-r1/report.json');iface=read(R/'reports/m4-lockit-source/provider-interface-r1/report.json');static=read(R/'reports/m4-lockit-review/static-r1/report.json');probe=read(R/'reports/m4-lockit-review/probe-r1/report.json')
    need(all(x['passed']for x in(source,iface,static,probe)),'Passed exact source and independent physical/runtime prerequisites')
    for x in(source,iface):
        for p,h in x['files'].items():pin(p,h)
    instruction=read(R/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json')
    provider=json.loads(pin(iface['instruction_contracts'],iface['instruction_contracts_sha256']).read_bytes())
    graphs=read(R/'reports/m4-lockit-source/recovery-r1/game-normal-graphs.json')
    spec=importlib.util.spec_from_file_location('fourroot_independent_interface_PE',pin(R/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
    game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    for r in instruction['instructions']:
        raw=bytes.fromhex(r['bytes_hex']);off,_=game.rva_range(r['pc']-game.image_base,len(raw));need(game.read(off,len(raw))==raw,'Physical game interface instruction')
    bypc={r['pc']:r for g in graphs.values() for r in g['instructions']}
    for f in instruction['FS_frame_contracts']:
        containing=[g for g in graphs.values() if any(r['pc']==f['entry'] for r in g['instructions'])]
        need(len(containing)==1,'One normal containing game body for actual FS prolog PC')
        body=containing[0]['instructions'];bodypc={r['pc']:r for r in body}
        need(bypc[f['read']]['bytes']=='64a100000000','Literal FS0 read before publication')
        need(bypc[f['install']]['bytes']=='64892500000000','Literal FS0 publication of current ESP')
        need(bypc[f['restore']]['bytes']=='64890d00000000','Literal FS0 restore of loaded predecessor ECX')
        saved=bypc[f['saved']];need(saved['mnemonic']=='mov' and saved['operands']==f'ecx, dword ptr [esp + 0x{f["saved_operand"]["displacement"]:x}]','Exact saved FS predecessor load operand')
        prior=[r for r in body if f['entry']<=r['pc']<f['install']]
        handler=next(r for r in prior if r['mnemonic']=='push' and r['operands']==hex(f['handler']))
        marker=next(r for r in prior if r['mnemonic']=='push' and r['operands']=='-0x1')
        predecessor=next(r for r in prior if r['mnemonic']=='push' and r['operands']=='eax')
        need(marker['pc']<handler['pc']<predecessor['pc']<f['install'] and f['bytes']==12,'Complete genuine12B FS frame marker/handler/previous order')
        ret=bypc[f['ret']];raw=bytes.fromhex(ret['bytes']);need(raw==(bytes.fromhex('c20800') if f['ret_cleanup']==8 else bytes.fromhex('c3')),'Exact complete source RET cleanup')
        offsets={}
        for call in instruction['Lockit_calls']:
            if call['root']!=f['root']:continue
            pc=call['CALL_pc'];prior=[r for r in body if r['pc']<pc];lea=next(r for r in reversed(prior) if r['mnemonic']=='lea' and r['operands'].startswith('ecx, [esp + '))
            shown=re.fullmatch(r'ecx, \[esp \+ 0x([0-9a-f]+)\]',lea['operands']);need(shown,'Literal direct scratch ESP address')
            intervening=[r for r in prior if r['pc']>lea['pc']]
            need(not any((r['mnemonic'] in ('push','pop','call') or (r['mnemonic'] in ('add','sub','mov','lea') and r['operands'].split(',')[0]=='esp'))for r in intervening),'No hidden scratch-address stack displacement before CALL')
            delta=int(shown[1],16)+4;kind=call['kind'];offsets[kind]=delta
            need(provider['game_scratch_offsets'][str(f['root'])][kind]==delta,'Independent literal ECX offset from genuine CALL-pushed frame')
            need(call['return_pc']==pc+bypc[pc]['size'] and call['argument_bytes']==call['RET_cleanup']==0 and not call['pointee_write_claimed'],'Zero-argument thiscall source/return contract without invented pointee writes')
            counts['literal_scratch_CALL_frame_relations']+=1
        allocs=[a for a in instruction['allocations']if a['root']==f['root']]
        expected=20 if f['root']==0x500660 else 24
        need(len(allocs)==2 and all(a['requested']==expected for a in allocs),'Exact distinct20B/24B allocation geometry')
        rows.append(dict(root=f['root'],source_FS_entry=f['entry'],FS_bytes=12,handler=f['handler'],FS_return_cleanup=f['ret_cleanup'],scratch_frame_offsets=offsets,actual_allocations_not_inferred=True,syntactic_allocation_requested=expected))
        counts['complete_FS_frame_contracts']+=1
    need(len(provider['instructions'])==17 and sum(x['width']for x in provider['instructions'])==51,'Exact conditional initialized provider17 rows51B')
    need(provider['CS_guest_bytes']==24 and provider['CS_native_bytes']==40 and provider['constructor_frame_delta']==-16 and provider['destructor_frame_delta']==-8,'Distinct typed resource and exact provider frame ABI')
    need(provider['constructor_and_destructor_source_pointee_writes']==0 and provider['unadmitted_state0'] and provider['unadmitted_state1'],'Bounded initialized state2 domain only')
    need(not provider['AFTER_machine_seed'],'No synthetic AFTER CPU/source state')
    pin(__file__);p=out/'root-interface-relations.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p)
    report=dict(passed=True,scope='Independent physical FS12,20B/24B geometry and ECX scratch CALL frame contracts; distinct initialized MSVCP provider ABI only',counts=dict(counts),source_sha256=sha(R/'reports/m4-lockit-source/recovery-r1/report.json'),provider_interface_sha256=sha(R/'reports/m4-lockit-source/provider-interface-r1/report.json'),independent_probe_sha256=sha(R/'reports/m4-lockit-review/probe-r1/report.json'),new_game_initializers_executed=False,native_resource_executed=False,initializer_credit=0,files=pins)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
