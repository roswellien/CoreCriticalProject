"""Source-derived finite widget roles; no measured GDI handle/value output seed."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
    if not v:raise ValueError(s)
def pin(p,h=None):
    p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();need(h is None or h==v,'Frozen source provenance '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,n):
    s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
    out=R/'reports/m4-widget-source'/name;need(not out.exists(),'Fresh additive contract preparation');out.mkdir()
    source=read(R/'reports/m4-widget-source/original-source-r6/report.json','f79f73c3b9862b054f2870f6805a844bf341168ad1e2ca54173a3933fd504c56');need(source['passed']and not source['AFTER_machine_or_memory_seed']and not source['GDI_FP_output_seed'],'Complete original source prefix without output seed')
    derivations=read(R/'reports/m4-widget-source/original-source-r6/source-derivations.json',source['files'][str((R/'reports/m4-widget-source/original-source-r6/source-derivations.json').resolve())]);static=read(R/'reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json','7e1095cb13aef3450991ef577b23de0b6daed874e85e02d2b375543b607e21e7');PE=load(R/'tools/analysis/pe.py','widget_contract_physical');game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());program={v['pc']:v for v in static['instructions']}
    for pc,row in program.items():
        a,_=game.rva_range(pc-game.image_base,row['width']);need(game.data[a:a+row['width']].hex()==row['bytes_hex'],'Entire exact source instruction '+hex(pc))
    actual_boundaries=read(R/'reports/m4-widget-original/validation-r1/actual-GDI-boundaries.json');boundary_map={(v['phase'],v['index']):v for v in actual_boundaries}
    roots=[];reached=set();counts=collections.Counter()
    for d,root in zip(derivations,static['selected_roots']):
        need(d['root']==root['entry'],'Exact root association');reached.update(d['source_PCs']);calls=[];ordinals=collections.Counter()
        for api in d['API_inputs']:
            site=api['source_CALL_pc'];ordinal=ordinals[site];ordinals[site]+=1
            # ESI is the literal same object at each GDI boundary, obtained
            # from the independently source-derived current CALL state. The
            # exact current instance is already joined by the virtual ledger.
            boundary=boundary_map[d['phase'],api['entry_index']];instance=boundary['CPU'][6]
            args=api['arguments'];api_name=api['API'];argument_contract=([dict(kind='source_instance_live_handle',instance_root_offset=instance-root['object'],field_offset=0x258)]if api_name=='DeleteObject'else[dict(kind='literal_constant',value=v)for v in args])
            calls.append(dict(order=len(calls),CALL_pc=site,service=api_name,per_site_ordinal=ordinal,instance_root_offset=instance-root['object'],frame_minus_root_frame=(api['source_frame']-0x20001800),argument_contract=argument_contract,return_pc=site+6,original_target_or_response_seeded=False))
        virtual=[]
        for v in d['virtual_calls']:
            store=v['source_store'];need(store['root']==root['entry']and store['source_access_index']<v['source_access_index'],'Dominating current-root instance vptr store before actual source slot read');virtual.append(dict(order=len(virtual),CALL_pc=v['PC'],instance_root_offset=v['instance']-root['object'],source_store_PC=store['PC'],source_vptr=store['value'],readonly_slot=v['slot'],target=v['target'],source_store_access_index=store['source_access_index'],source_slot_access_index=v['source_access_index'],frame_minus_root_frame=v['ESP']-0x20001800))
        arrays=[]
        for a in d['array_invocations']:
            c=a['contract'];need(len(a['iterations'])==c['count'],'Source-derived successful finite array extent');arrays.append(dict(CALL_pc=a['caller'],frame_minus_root_frame=a['frame']-0x20001800,base_root_offset=a['base']-root['object'],stride=c['stride'],count=c['count'],constructor=c['constructor'],cold_destructor=c['destructor'],constructor_CALL_pc=0x5ac2db,success_return_pc=0x5ac30c,iterations=[dict(ordinal=v['iteration'],instance_root_offset=v['instance']-root['object'],target=v['target'],frame_minus_root_frame=v['ESP']-0x20001800)for v in a['iterations']]))
        fs=[dict(order=v['index'],PC=v['PC'],writing=v['writing'],source_access_index=v['source_access_index'])for v in d['FS_joins']]
        roots.append(dict(root=root['entry'],slot=root['slot'],object=root['object'],registration=root['registration'],GDI_calls=calls,virtual_calls=virtual,array_invocations=arrays,FS_operations=fs,reached_PCs=sorted(set(d['source_PCs']))))
        counts.update(roots=1,GDI_calls=len(calls),virtual_calls=len(virtual),arrays=len(arrays),array_callbacks=sum(a['count']for a in arrays),FS_operations=len(fs))
    need(counts==dict(roots=5,GDI_calls=145,virtual_calls=500,arrays=5,array_callbacks=75,FS_operations=570),'Exact measured normal source role counts')
    negative=[('vptr_instance','Different instance or source store generation'),('vptr_slot','Changed readonly slot target'),('vptr_overwrite','Overlapping write invalidates the current token'),('array_frame','Foreign caller/helper invocation frame'),('array_bounds','Wrong stride,count or callback argument'),('array_order','Repeated,skipped or reordered element'),('font_registry','Nonzero current6384E8 needs separate dormant closure'),('format_argument','Non-null current format argument needs provider closure'),('create_failure','Genuine NULL CreateFont result leaves normal domain'),('handle_generation','Foreign,expired or cross-instance owned font handle'),('stock_alias','Borrowed stock alias never acquired as an owned font'),('duplicate_delete','Owned font released twice or shared native alias'),('FS_predecessor','Changed full predecessor/current source FS frame'),('source_code','Changed exact source bytes or readonly permissions'),('resource_observer','Private full native handle or lifetime witness changed'),('caller_FP','Unrestored complete caller FX512/ENV28')]
    value=dict(schema='mw34-widget-normal-source-contract-v1',roots=roots,reached_game_PCs=sorted(reached),dormant_game_PCs=sorted(set(program)-reached),literal_instructions=static['instructions'],source_indirect_contracts=static['source_indirect_contracts'],source_array_contracts=static['source_array_contracts'],GDI_policy=dict(GetStockObject='Fresh actual native borrowed OEM_FIXED_FONT handle; preserve valid shared aliases.',DeleteObject='Exact current source instance field and resource lifetime; retain actual BOOL, never force result.',CreateFontA='Fresh actual full native owned handle per successful source invocation; NULL error path unadmitted.',guest_handle='Separate typed DWORD identity mapped to actual complete native handle; no original handle seed.',volatile_API_CPU='Fresh actual native volatile/FP effects at the precise source CALL; original volatile equality unclaimed.',manual_cleanup='Only still-live owned CreateFont acquisitions; research cleanup is not a game callback.'),cold_domains=dict(nonzero_font_registry=False,nonnull_format_argument=False,CreateFont_failure=False,vector_unwind=False,source_shutdown=False),required_controls=[dict(id=a,denial=b)for a,b in negative],counts=dict(counts),original_GDI_handles_seeded=False,original_API_volatile_outputs_seeded=False,AFTER_machine_seed=False,initializer_credit=0)
    q=out/'normal-contracts.json';q.write_text(json.dumps(value,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
    report=dict(passed=True,scope='Source-proven finite widget roles/order for native implementation preparation. Literal CALL identities and effects derive from current original BEFORE; exact virtual/vector CALL PCs remain untraced in the normal capture. No native execution or startup credit.',contracts_path=str(q.resolve()),contracts_sha256=PINS[str(q.resolve())],counts=dict(counts),physical_game_rows=len(program),reached_game_PC_count=len(set(program)&reached),dormant_game_PC_count=len(set(program)-reached),original_GDI_handles_seeded=False,original_API_volatile_outputs_seeded=False,AFTER_machine_seed=False,initializer_credit=0,files=PINS);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
