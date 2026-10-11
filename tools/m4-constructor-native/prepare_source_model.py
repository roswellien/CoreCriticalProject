"""Small archive-free constructor descriptor/callback/model preparation."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v: raise ValueError(m)
def main(name):
    out=R/'reports/m4-constructor-native'/name; need(not out.exists(),'Fresh source model preparation'); files={}
    def pin(p,h=None):
        p=Path(p).resolve(); need(p.suffix.lower() not in ('.mwb','.zip'),'No capture/archive reader'); d=sha(p); need(h is None or h==d,'Exact physical constructor source input '+str(p)); files[str(p)]=d; return p
    def read(p,h=None): return json.loads(pin(p,h).read_bytes())
    def module(p,n):
        spec=importlib.util.spec_from_file_location(n,pin(p)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    source=R/'reports/m4-constructor-source/preparation-r1/report.json'; receipt=read(source,'0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf')
    raw=read(source.parent/'source-instructions.json',receipt['files'][str((source.parent/'source-instructions.json').resolve())]); need(len(raw)==1401,'Full physical constructor source union')
    D=module(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','constructor_literal_descriptor_decoder')
    sys.path.insert(0,str(R/'tools/analysis')); from pe import PEImage
    pin(R/'tools/analysis/pe.py'); image=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    rows={}
    for row in raw:
        code=bytes.fromhex(row['bytes']); off,_=image.rva_range(row['pc']-image.image_base,len(code)); need(image.data[off:off+len(code)]==code,'Whole physical source instruction')
        normalized=dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0]); rows[row['pc']]=D.instruction_contract(normalized)
    C=module(R/'tools/m4-crt-locale-batch-recovery/callbacks.py','constructor_literal_callback_decoder')
    component=read(R/'reports/m4-constructor-native/preparation-r7/report.json','d291ae395b5ee16243f160daba61d360a08142188c84291f4c7458bc86693384')
    sites={}; bodies={}
    for item in component['namespace_relations']:
        entry=item['entry']; host=pin(item['original_IR'],item['original_sha256']); stem=host.name.removesuffix('-host.ll')
        pre=pin(host.parent/(stem+'-pre.ll')); guest=pin(host.parent/(stem+'-baseline.ll'))
        if entry not in rows:
            # Reused registration/MFC thunks have a retained physical parent
            # descriptor; no constructor source bytes are invented here.
            continue
        calls,mapping=C.recover(C.function(pre.read_text(),entry),C.function(guest.read_text(),entry),entry,rows)
        for call in calls:
            pc=call['pc']; offsets=call['State_offsets']; need(pc not in sites or sites[pc]==offsets,'Exact same shared undefined callback order'); sites[pc]=offsets
        bodies[str(entry)]=dict(entry=entry,callback_sites=calls,source_marker_map=mapping)
    out.mkdir(parents=True)
    inst=out/'instruction-contracts.json'; inst.write_text(json.dumps(dict(instructions=[rows[p] for p in sorted(rows)],AFTER_machine_seed=False),indent=2)+'\n')
    cb=out/'callbacks.json'; cb.write_text(json.dumps(dict(State_offsets_by_original_PC={str(p):v for p,v in sorted(sites.items())},bodies=bodies,AFTER_machine_seed=False),indent=2)+'\n')
    pin(inst);pin(cb);pin(__file__);pin(R/'tools/m4-constructor-native/game_model.py')
    report=dict(passed=True,scope='Physical decoded source/callback/model preparation only, no source/candidate execution or endpoint equality claim',instructions=str(inst),instructions_sha256=sha(inst),callbacks=str(cb),callbacks_sha256=sha(cb),physical_rows=len(rows),physical_bytes=sum(v['width'] for v in rows.values()),callback_bodies=len(bodies),undefined_callback_sites=len(sites),whole_flag_consumer_audit_executed=False,cold_recursive_entry=0x56fea0,native_executed=False,original_executed=False,archive_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,files=files)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),physical_rows=len(rows),callback_bodies=len(bodies))))
if __name__=='__main__': main(sys.argv[1])
