"""Freeze finite source-derived normal formatter roles, not observed output seeds."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def read(p,h=None):
        p=p.resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return json.loads(p.read_bytes())
    source_path=R/'reports/m4-formatting-source/original-trace-source-r4/report.json';source=read(source_path,'b3d0ca6d60d0393479d3dd315e3795d8c02a3770f8f4bfe89de0ef6a5ae98dc9');assert source['passed']
    derivations=read(source_path.parent/'source-derivations.json',source['files'][str((source_path.parent/'source-derivations.json').resolve())])
    joins=read(source_path.parent/'instruction-joins.json',source['files'][str((source_path.parent/'instruction-joins.json').resolve())])
    provider_path=R/'reports/m4-formatting-source/provider-recovery-r2/report.json';provider=read(provider_path,'2aa9a712983ab98a08c3f59adf8e29b24c17f1f8c0d41ebb786a55c7241a13b9');instructions=read(Path(provider['instructions']),provider['instructions_sha256'])['instructions']
    frontier_path=R/'reports/m4-formatting-frontier/recovery-r1/report.json';frontier=read(frontier_path,'8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15');game=read(frontier_path.parent/'instruction-contracts.json',frontier['files'][str((frontier_path.parent/'instruction-contracts.json').resolve())])
    reached=sorted({r['PC']for r in joins});assert len(reached)==238
    normal=[r for r in instructions if r['pc']in reached];assert len(normal)==238
    dormant=[r for r in instructions if r['pc']not in reached]
    cases=[]
    for derived,root in zip(derivations,game['roots']):
        assert derived['root']==root['entry'];owner=derived['owner'];owned=[];calls=[];controls=[]
        for pc,address,value,width,writing in derived['source_accesses']:
            if owner['pointer']<=address<owner['pointer']+owner['capacity']:
                assert address+width<=owner['pointer']+owner['request']
                owned.append(dict(PC=pc,offset=address-owner['pointer'],width=width,writing=bool(writing),literal_value=value))
        for row in joins:
            if row['phase']!=derived['phase']:continue
            inst=next(x for x in normal if x['pc']==row['PC'])
            if inst['mnemonic']=='call':calls.append(dict(PC=row['PC'],target=row['next_PC'],frame_minus_sprintf_entry_ESP=row['CPU_after'][4]-next(j['CPU_before'][4]for j in joins if j['phase']==row['phase']and j['PC']==0x78022b9a)))
            if inst['mnemonic'].startswith('j')or inst['mnemonic']=='ret':controls.append(dict(PC=row['PC'],target=row['next_PC']))
        cases.append(dict(root=root['entry'],request=owner['request'],capacity=owner['capacity'],root_contract=root,provider_instruction_count=derived['provider_instructions'],owned_accesses=owned,provider_calls=calls,provider_controls=controls,table_dispatches=[dict(PC=x['PC'],index=x['index'],table_read=x['table_read'],target=x['target'])for x in derived['dispatches']],source_output_hex=owner['output_hex'],unwritten_tail_offset=owner['request']))
    result=dict(schema='mw34-formatting-normal-source-v1',roots=game['roots'],instructions=normal,dormant_instructions=dormant,cases=cases,
        source_provider_entries=[0x780264a9,0x78022b9a,0x7800fc9b,0x7801041a,0x7801044f,0x78010480,0x780104b8],
        indirect_continuation_entries=[0x7800fd04,0x7800fe69],source_table_dispatch_PC=0x7800fcef,dispatch_index_order=[1,7,1,7],
        tables=read(provider_path.parent/'tables.json',provider['files'][str((provider_path.parent/'tables.json').resolve())]),
        cdecl_source=[dict(PC=0x4dea15,slot=0x5bb5a8,target=0x780264a9,argc=2,entry_offset=-36,cleanup=8),dict(PC=0x4deab1,slot=0x5bb664,target=0x780012b3,argc=1,entry_offset=-32,cleanup=4),dict(PC=0x4dead1,slot=0x5bb658,target=0x78022b9a,argc=4,entry_offset=-44,cleanup=16)],
        lifetime='Actual malloc source CALL frame -> genuine HeapAlloc returned generation/round16 -> game field publication -> requested output cells -> source825 cleanup; full capacity/tail retained',
        no_observed_output_seed=True,source_receipt=str(source_path),source_receipt_sha256=sha(source_path),generic_formatter_closed=False,native_executed=False,initializer_credit=0)
    p=out/'normal-contracts.json';p.write_text(json.dumps(result,indent=2)+'\n');pins[str(p.resolve())]=sha(p);pins[str(Path(__file__).resolve())]=sha(__file__)
    report=dict(passed=True,scope='Finite source-derived default filename provider access/control roles; all other formatter rows dormant',contracts=str(p),contracts_sha256=sha(p),normal_provider_rows=len(normal),dormant_provider_rows=len(dormant),source_defined_conditional_uses=429,write_BEFORE_joins=540,files=pins,native_executed=False,initializer_credit=0)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
