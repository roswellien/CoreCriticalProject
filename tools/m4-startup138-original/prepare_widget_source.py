"""Adapt frozen widget prefix proof to six current138 ordinary raw exports.

All endpoint checks remain strict; registration provider source is a frontier.
"""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
VALIDATION='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'tools/m4-fps-original/compare_source_v3.py';text=base.read_text();changes=[]
 def one(old,new,count=1):
  nonlocal text
  assert text.count(old)==count,(old[:80],text.count(old));position=text.index(old);text=text.replace(old,new);changes.append(dict(old=old,new=new,count=count,position=position))
 one("out=R/'reports/m4-fps-original'/name", "out=R/'reports/m4-startup138-original'/name")
 one('results=[];API_inputs=[];memory_joins=[];FPS_joins=[]','results=[];API_inputs=[];memory_joins=[];FPS_joins=[];reader=None;source_fonts=[];source_stock={};cleanup_rows=[]')
 one("p=Path(p).resolve();v=sha(p);", "p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.mwi')and p.name not in('transport.json','manifest.json','bundle.json'),'No canonical capture input');v=sha(p);")
 start=text.index("        exports=R/'reports/m4-fps-original/validation-r1'")
 end=text.index('        source_prep=read(',start)
 old=text[start:end]
 new="""        exports=R/'reports/m4-startup138-original/original-validation-r2';validation_path=exports/'report.json';validation=read(validation_path,'@VALIDATION@');need(validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['counts']['phases']==828 and validation['callbacks']==108 and validation['combined_pages']==69,'Exact complete closed original138 observations')
        execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prepdir=Path(build['preparation']);prep=read(prepdir/'report.json',build['preparation_sha256']);contract=read(prep['contracts'])
        import re
        compiled=raw(prepdir/'spec.hpp').decode();match=re.search(r'std::array<unsigned,69> widget_whole_pages\\{([^}]+)\\};',compiled);need(match is not None,'Exact compiled original69 snapshot page order');whole=[int(v.strip(),16)for v in match[1].split(',')];need(whole[:43]==prep['observed_pages']and len(set(whole))==69 and set(whole[43:])==set(prep['extra_whole_source_pages']),'Complete physical source69 snapshot inventory')
        E=load(R/'tools/m4-startup131-original/export_reader.py','current138_original_raw_export');reader=E.ExportReader(validation_path,'@VALIDATION@','original',pin)
        def capture(logical):return reader.data(logical)
        def actual_pages(record,stem,side):
            offset=2276 if side=='before'else 178404
            return {p:record[offset+i*4096:offset+(i+1)*4096]if i<43 else capture(stem+f'extra-{side}/{p}.bin')for i,p in enumerate(whole)}
        def sealed(name):return read(exports/name,validation['files'][str((exports/name).resolve())])
""".replace('@VALIDATION@',VALIDATION)
 one(old,new)
 start=text.index("        FPS=read(validation_path.parent/'actual-FPS-boundaries.json'")
 end=text.index("        identity=u(capture('widget/identity.bin')",start)
 old=text[start:end]
 new="""        FPS=sealed('FPS-observations.json');fps_identity=u(capture('fps/identity.bin'),0,4)
        boundaries=sealed('widget-GDI-observations.json');fsrows=sealed('widget-FS-observations.json');endpoints=sealed('widget-root-observations.json');lifetimes=sealed('font-resource-lifetimes.json')
        need(len(endpoints)==42 and len(boundaries)==validation['counts']['widget_complete_GDI_boundary_sides']and len(fsrows)==validation['counts']['widget_actual_FS_instruction_events'],'Complete current metadata extents')
        for fact in boundaries:fact['side']='entry'if fact['side']==0 else'first-source-return'
        for fact in fsrows:fact.update(words=fact['header'],FX_before_hex=fact['FX_hex'],ENV_before_hex=fact['ENV28_hex'],record_before_hex=fact['frame16_hex'])
        for fact in FPS:fact.update(format_input16_hex=fact['format16_hex'],va_input64_hex=fact['va64_hex'])
"""
 one(old,new)
 one("        for phase,root in enumerate(G.contracts()['selected_roots']):", "        roots={r['entry']:r for r in G.contracts()['selected_roots']};schedule=((15,0x40e250),(16,0x40ef50),(17,0x40f000),(47,0x479590),(134,0x5a3c30),(135,0x5a3ff0),(136,0x5a66f0));need(set(roots)=={r for _,r in schedule},'Exact seven literal roots');need(all(contract['selected_order'][p]['entry']==r for p,r in schedule),'Exact current chronological widget phases')\n        for seq,phase,root in [(s,p,roots[r])for s in range(6)for p,r in schedule]:")
 one("stem=f'phase/0/{phase}/';record=capture(f'phase/0/{phase}.bin')", "stem=f'phase/{seq}/{phase}/';record=capture(f'phase/{seq}/{phase}.bin')")
 one("memory={p:bytearray(raw(exports/'actual-inputs'/f'phase-{phase}'/'BEFORE'/f'{p}.bin'))for p in whole}","memory={p:bytearray(b)for p,b in actual_pages(record,stem,'before').items()};need(all(len(b)==4096 for b in memory.values()),'Whole own actual69 BEFORE inputs')")
 one("registry[1]-registry[0]==4*phase", "registry[0]<=registry[1]<=registry[0]+registry[2]and u(memory[0x78037000],0x888)[0]==registry[1]and u(memory[0x78037000],0x88c)[0]==registry[0]")
 one("facts=[v for v in boundaries if v['phase']==phase];fsfacts=[v for v in fsrows if v['phase']==phase]", "facts=[v for v in boundaries if v['sequence']==seq and v['phase']==phase];fsfacts=[v for v in fsrows if v['sequence']==seq and v['phase']==phase]")
 one("fpsfacts=[v for v in FPS if v['phase']==phase]", "fpsfacts=[v for v in FPS if v['sequence']==seq and v['phase']==phase]")
 one("if key not in snap_cache:snap_cache[key]=raw(fact['raw_snapshot'],fact['raw_snapshot_sha256'])", "if key not in snap_cache:\n                    blob=capture(stem+'widget-snapshots.bin');need(len(blob)==len(facts)*287444,'Whole original GDI69 snapshot blob');snap_cache[key]=blob[key*287444:(key+1)*287444];need(hashlib.sha256(snap_cache[key]).hexdigest()==fact['raw_sha256'],'Current individually sealed GDI snapshot identity')")
 one("s=raw(fact['raw_snapshot'],fact['raw_snapshot_sha256']);stack=", "blob=capture(stem+'fps-snapshots.bin');need(len(blob)==len(fpsfacts)*550180,'Whole original FPS snapshot blob');s=blob[fact['index']*550180:(fact['index']+1)*550180];need(hashlib.sha256(s).hexdigest()==fact['raw_sha256'],'Current individually sealed FPS snapshot identity');stack=")
 one("s[266964+j*4096:266964+(j+1)*4096]", "s[287444+j*4096:287444+(j+1)*4096]")
 one("raw(fpsfacts[0]['raw_snapshot'],fpsfacts[0]['raw_snapshot_sha256'])[724:4820]", "blob[:550180][724:4820]")
 one("complete_nonstack_pages=63", "complete_nonstack_pages=68")
 one("complete_source_nonstack_pages=63", "complete_source_nonstack_pages=68")
 one("raw(exports/'actual-inputs'/f'phase-{phase}'/'AFTER'/f'{p}.bin')", "actual_pages(record,stem,'after')[p]")
 one("dict(phase=phase,root=root['entry']", "dict(sequence=seq,phase=phase,root=root['entry']")
 one("counts['literal_widget_registration_prefixes']==7 and counts['literal_FPS_CPU_FX_ENV_frame_joins']==2", "counts['literal_widget_registration_prefixes']==42 and counts['literal_FPS_CPU_FX_ENV_frame_joins']==12")
 one("validation['counts']['actual_stdcall_RET_joins']", "validation['counts']['widget_actual_stdcall_RETURN_relations']")
 one("validation['counts']['actual_FS_instruction_observations']", "validation['counts']['widget_actual_FS_instruction_events']")
 one('    finally:\n        for name_,value', "    finally:\n        if reader is not None:reader.close()\n        for name_,value")
 one("scope='Literal carried seven-root widget/font/fps registration prefixes", "scope='Current138 six-sequence literal seven-root widget/font/fps registration prefixes")
 one("archive_reader_opened=False,files=PINS", "archive_reader_opened=False,ordinary_raw_export_closed=reader is None or reader.closed,complete_current_widget_gate=False,registration_provider69_endpoint_frontier=True,files=PINS")
 reverse=text
 for d in reversed(changes):
  position=d['position'];assert reverse[position:position+len(d['new'])]==d['new'],d['new'][:90];reverse=reverse[:position]+d['old']+reverse[position+len(d['new']):]
 assert reverse==base.read_text();ast.parse(text)
 target=Path(__file__).with_name('compare_widget_source.py');assert not target.exists();target.write_text(text)
 out=R/'reports/m4-startup138-original/widget-source-preparation-r1';assert not out.exists();out.mkdir()
 validator=R/'reports/m4-startup138-original/original-validation-r2/report.json';assert sha(validator)==VALIDATION
 files={str(p):sha(p)for p in(base,target,Path(__file__).resolve(),validator,R/'tools/m4-startup131-original/export_reader.py',R/'reports/m4-fps-original/source-preparation-r4/game_model.py',R/'tools/m4-startup138-original/widget_phase_v3.py')}
 receipt=dict(passed=True,scope='Unexecuted additive source input adapter for current138 seven widgets by six sequences; strict all69 snapshot/endpoint comparisons retained',changes=changes,exact_inverse_restores_parent=True,original_validation_sha256=VALIDATION,source_entrypoint=str(target),no_canonical_reader=True,own_root_BEFORE_input=True,AFTER_machine_seed=False,complete_widget_source_gate=False,
  pending_gates=['Original source registration body/return and full69 root endpoints after provider effects','Source-derived font occurrence/liveness and actual reverse manual cleanup joins across all six sequences','Whole current inherited source and paired semantic policy gates remain separate'],initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),entrypoint=str(target),complete_widget_gate=False)))
if __name__=='__main__':main()
