"""Freeze physical original141 capture geometry; no observer build/worker/readers."""
from pathlib import Path
import hashlib,json,re,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main():
 out=R/'reports/m4-original141/geometry-preparation-r1';need(not out.exists(),'Fresh static preparation');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary physical inputs only');v=sha(p);need(h is None or v==h,'Exact physical input '+str(p));files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=R/'reports/m4-startup138-original/preparation-r8';supp=R/'reports/m4-138-validation-review/constructor-input-capture-preparation-r5'
 parent=read(old/'report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161');sc=read(supp/'contracts.json');supplement=read(supp/'report.json')
 native=R/'reports/m4-startup141-runway/preparation-r3';n=read(native/'report.json','98b3f726249ef233ccdc63855cd5c735aa2ff01cc8717494b686bec34dafb46e')
 order=read(native/'selected-order.json');roots=(0x4103f0,0x410440,0x459b40)
 need(order==n['selected_order']and len(order)==141,'Current physical native141 schedule')
 need([v for v in order if v['entry']not in roots]==parent['selected_order'],'Removing only3 inserted roots recovers entire138 schedule')
 need([i for i,v in enumerate(order)if v['entry']in roots]==[13,14,39]and order[15]['entry']==0x5ae3e4,'Exact physical constructor and MFC positions')
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 pin(R/'tools/analysis/pe.py');game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 def physical(pc,width):offset,_=game.rva_range(pc-game.image_base,width);return game.data[offset:offset+width],offset
 raw=pin(old/'pages.bin',parent['pack_sha256']).read_bytes();count=struct.unpack_from('<I',raw,8)[0];need(raw[:8]==b'MW4J124P'and len(raw)==12+count*4104,'Exact retained sparse pack')
 pages={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(count)}
 spans=list(parent['source_spans']);known={v['pc']:v for v in spans};overlays=[]
 for row in sc['new_source_spans']:
  need(row['origin']==0 and row['pc']not in known,'All1371 additional physical game rows are genuinely additive')
  value,offset=physical(row['pc'],row['size']);need(offset==row['image_offset'],'Physical source file offset')
  for index,byte in enumerate(value):
   address=row['pc']+index;base=address&~4095;within=address&4095
   if base not in pages:pages[base]=(1,bytearray(b'\xcc'*4096))
   permission,page=pages[base];need(permission==1 and page[within]in(0xcc,byte),'Only physical RX padding/source overlay')
   if page[within]!=byte:overlays.append(dict(address=address,previous=page[within],physical=byte,source_PC=row['pc']))
   page[within]=byte
  spans.append(row);known[row['pc']]=row
 need(len(spans)==6411 and len(sc['new_source_spans'])==1371 and len(pages)==176,'Exact5040+1371 source rows;161+15 pages')
 for row in parent['source_spans']:
  pc=row['pc'];need(row==known[pc],'Every prior complete source row retained')
  # Retained provider origins remain untouched; new overlays belong only to game.
 for row in order:
  value,_=physical(row['slot'],4);need(value==struct.pack('<I',row['entry'])and pages[row['slot']&~4095][1][row['slot']&4095:(row['slot']&4095)+4]==value,'Every actual physical CRT table cell')
 pack=raw[:8]+struct.pack('<I',len(pages))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in pages.items());(out/'pages.bin').write_bytes(pack)
 fs=read(old/'fs-hook-bindings.json');sf=read(supp/'fs-hook-bindings.json');byPC={v['PC']:v for v in fs};added=[]
 for v in sf:
  if v['PC']in byPC:need(v==byPC[v['PC']],'Every shared FS observer binding byte-identical')
  else:added.append(v);byPC[v['PC']]=v
 need(len(fs)==93 and len(added)==15 and len(byPC)==108,'Retain every widget FS hook and add exact constructor physical sites')
 callbacks={};contracts={}
 sources=[('m4-onexit-batch-recovery/recovery-r3/registration-roots.json',None),('m4-strings-source/recovery-r7/string-roots.json',None),('m4-mfc-source/recovery-r4/mfc-roots.json',None),('m4-fs-source/recovery-r3/fs-roots.json',None),('m4-container-source/recovery-r3/container-roots.json',None),('m4-next-source/recovery-r1/instruction-contracts.json','roots'),('m4-lockit-source/recovery-r1/Lockit-roots.json',None),('m4-fps-original/source-preparation-r4/source-contracts.json','selected_roots')]
 for rel,key in sources:
  values=read(R/'reports'/rel);values=values[key]if key else values
  for v in values:
   cb=v['registration']['callback'];need(v['entry']not in callbacks or callbacks[v['entry']]==cb,'Same original callback identity');callbacks[v['entry']]=cb;contracts[v['entry']]=v['registration']
 for v in sc['new_roots']:callbacks[v['entry']]=v['callback'];contracts[v['entry']]=v
 vector=[dict(root=v['entry'],callback=callbacks[v['entry']],physical_slot=v['slot'])for v in order if v['entry']in callbacks]
 need(len(vector)==111 and sum(v['root']in roots for v in vector)==3,'Physical carried111-registration vector')
 spec=pin(old/'spec.hpp').read_text();spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[v['entry']for v in order]),('table_slots',[v['slot']for v in order]),('page_bases',list(pages)),('page_permissions',[v[0]for v in pages.values()])]:
  pattern=r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;';need(len(re.findall(pattern,spec))==1,'One actual array '+field);spec=re.sub(pattern,f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 pattern=r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;';need(len(re.findall(pattern,spec))==1,'One source binding array');spec=re.sub(pattern,f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings'+'{{'+','.join('{'+','.join(hex(v[k])for k in('pc','size','image_offset','origin'))+'}'for v in spans)+'}};',spec)
 oldnull=re.search(r'inline constexpr std::array<NullFreeBinding,5> nullfree_bindings\{\{[^;]+;',spec);need(oldnull is not None,'Retained old5 NULL call sites');newnull=re.search(r'inline constexpr std::array<NullFreeBinding,7> nullfree_bindings\{\{[^;]+;',pin(supp/'spec.hpp').read_text());need(newnull is not None,'Tested exact2 new NULL sites');spec=spec.replace(oldnull[0],newnull[0]);(out/'spec.hpp').write_text(spec)
 protocol=pin(old/'protocol.hpp').read_text();need(protocol.count('sequences=6, roots=138')==1,'Exact fixed ABI root count');(out/'protocol.hpp').write_text(protocol.replace('sequences=6, roots=138','sequences=6, roots=141'))
 plan=pin(R/'docs/m4-execution-plan-r14.md');(out/'frozen-plan.md').write_bytes(plan.read_bytes())
 for name in ['reference.cpp','reference_x86.asm','constructor_normal.hpp','constructor_observer_x86.asm','constructor-hook-bindings.json','fs_observer_x86.asm','original_broker.hpp','changes.json','asm-changes.json']:pin(supp/name)
 pin(old/'reference.cpp');pin(old/'reference_x86.asm');pin(old/'fs_observer_x86.asm');pin(old/'source-hook-inventory.json');pin(R/'reports/m4-138-validation-review/constructor-input-capture-validation-r2/report.json','aec13bc32dc8a0a02b5d9fd63d999e52c82bef8e9d63dbee8f74b330a786469f')
 payloads={'selected-order.json':order,'callback-vector111.json':vector,'source-spans.json':spans,'source-overlays.json':overlays,'fs-hook-bindings.json':fs+added,'new-FS-bindings.json':added,'callback-source-contracts.json':contracts}
 for name,value in payloads.items():(out/name).write_text(json.dumps(value,indent=2)+'\n')
 for p in out.iterdir():pin(p)
 pin(__file__)
 requirements=['Compose observer from138 prep8, never copy37 partial-root relaxed vector/FS counts. Keep all GDI/FPS/typed HeapReAlloc backing/resource/manual font cleanup gates.',
 'Apply exact tested7 CPP/2 ASM own constructor input supplement deltas: whole CRT64 pages before/after, named144? API bindings measured anew, own6-selector34DWORD descriptors inside existing execute SEH, CS24 inputs inline before actual API and outputs after.',
 'Add tested constructor normal observer header/ASM and exact9 patches; retain all shared63 plus widget30 and new15 FS hooks. Prove every active source/IAT patch span disjoint except exact declared observer mode transitions.',
 'MFC phase moves13 to15; strict continuity must reconstruct exact full-page CRT observer disable/reinstall at15 and16 using current linked identities, plus temporary constructor823 IAT install/restore at13/14/39. Never mask whole pages or borrow AFTER inputs.',
 'Keep fixed Record356992/43 pages and69 existing source endpoint pages; export whole constructor-global5F2000 before/after every846 phase (1692 endpoints) and lifecycle boundaries independently.',
 'Collect original allocation occurrences at every genuine phase, including registry realloc revisions and constructor owners. Capture initial full allocation backings before guest writes; bind6 constructor births and2 genuineNULL calls to exact source sites.',
 'Registry cap512 remains adequate for111*4=444 callback bytes; require exact111 vector in physical selected chronology with same root/slot/callback identities.',
 'Add exact source-owned constructor cleanup6 live owners with measured full backings and named825 return; distinguish observed manual cleanup from unexecuted new callback shutdown.',
 'Reuse physical source6411 rows and existing compiler/Ghidra/REA artifacts; no new lifting or installs. Complete whole-link/observer11+new compiled PUSHFD/FX/stack replay review before writer admission.',
 'Original141 finite source evaluators must bind own current BEFORE descriptors/whole CRT inputs and named API facts. Original138 numerical scalar oracles are baseline only and cannot authenticate current141 measured endpoints.',
 'Do not fabricate native global35/70: actual normal FS stays28/56, constructor component has7 scopes/21events/14source-owned record checkpoints. Original observer FS capture has its own actual schema and must independently validate same literal scopes.',
 'Prepare fresh strict controller/validator and ordinary export only after observer compile and ROOT independent admission. Capture execution/source/pair/current criteria gates remain pending; no credit from preparation.']
 (out/'requirements.json').write_text(json.dumps(requirements,indent=2)+'\n');pin(out/'requirements.json')
 report=dict(passed=True,geometry_only=True,observer_source_composed=False,original_roots=141,original_sequences=6,original_phases=846,callback_count=111,fixed_Record_bytes=356992,inherited_source_pages=69,additional_global_source_page=0x5f2000,source_spans=6411,new_source_spans=1371,sparse_pack_pages=176,FS_hooks=108,new_FS_hooks=15,exact138_order_retained=True,physical_table_verified=True,physical_new_source_verified=True,whole_source_rows_retained=True,current_plan_sha256=sha(plan),remaining_requirements=requirements,build_executed=False,worker_executed=False,canonical_reader_opened=False,writer_admitted=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(out/'report.json'),sha256=sha(out/'report.json'),geometry_only=True)))
if __name__=='__main__':main()
