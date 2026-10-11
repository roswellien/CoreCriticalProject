"""Append one genuine font initializer to the measured widget prefix; no execution."""
from pathlib import Path
import copy,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BASE=R/'reports/m4-font479590-original'
OLD=R/'reports/m4-widget-original/preparation-r9'
SOURCE=R/'reports/m4-remaining-service-source/preparation-r2'
sys.path.insert(0,str(R/'tools/analysis'))
from pe import PEImage

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'Exact additive replacement '+a[:100]);return s.replace(a,b,1)

def main(name):
 out=BASE/name;need(not out.exists(),'Fresh preparation required');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archive');v=sha(p);need(h is None or h==v,'Exact physical identity '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable pin');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=read(OLD/'report.json','ad3a1d2b6527a9ca19904743364273c366ea2a8565e627b9453a0d263c73ab6c')
 need(old['passed']and old['original_roots']==5 and old['combined_source_pages']==64,'Exact measured five-widget preparation')
 prior=read(R/'reports/m4-widget-original/validation-r1/report.json','2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c');need(prior['passed']and prior['reader_closed'],'Closed genuine prior widget observations')
 source=read(SOURCE/'report.json','e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4');need(source['passed'],'Exact physical remaining source recovery')
 for p,h in old['files'].items():pin(p,h)
 graphs=read(SOURCE/'all-seven-graphs.json');registration=next(v for v in read(SOURCE/'registration-roots.json')if v['entry']==0x479590)
 need((registration['slot'],registration['callback'],registration['registration_CALL_pc'],registration['registration_return_PC'])==(0x5e00cc,0x4795d0,0x4795c5,0x4795ca),'Exact newroot callback source chronology')
 physical=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 contract=read(OLD/'normal-contracts.json');contract=copy.deepcopy(contract)
 rows=graphs[str(0x479590)]['instructions']+graphs[str(0x4795a0)]['instructions'];need(len(rows)==12 and sum(v['size']for v in rows)==41,'Exact two new literal bodies')
 allcontracts=read(SOURCE/'instruction-contracts.json');allcontracts=allcontracts.get('instructions',allcontracts)if isinstance(allcontracts,dict)else allcontracts
 descriptors={v['pc']:v for v in allcontracts};newrows=[descriptors[v['pc']]for v in rows]
 need(all('fs:'not in v['operands']for v in rows),'No new FS observer sites')
 pack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();n=struct.unpack_from('<I',pack,8)[0];need(pack[:8]==b'MW4J124P'and len(pack)==12+n*4104,'Exact inherited sparse pack')
 records={struct.unpack_from('<I',pack,12+i*4104)[0]:(struct.unpack_from('<I',pack,16+i*4104)[0],bytearray(pack[20+i*4104:4116+i*4104]))for i in range(n)}
 need(len(records)==n==159,'Same sparse page inventory');spans=copy.deepcopy(old['source_spans']);known={(v['pc'],v['size'])for v in spans};overlay=[]
 for row in rows:
  pc=row['pc'];b=bytes.fromhex(row['bytes']);off,_=physical.rva_range(pc-physical.image_base,len(b));need(physical.data[off:off+len(b)]==b,'Whole physical new instruction')
  for j,value in enumerate(b):
   p=(pc+j)&~4095;o=(pc+j)&4095;need(p in records and records[p][0]==1 and len(records[p][1])==4096,'Existing exact4096B RX page')
   oldvalue=records[p][1][o];need(oldvalue in(0xcc,value),'Only physical source overlays inherited sparse padding')
   if oldvalue!=value:overlay.append(dict(address=pc+j,old=oldvalue,new=value,source_PC=pc))
   records[p][1][o]=value
  need((pc,len(b))not in known,'New rows disjoint inherited whole instructions');spans.append(dict(pc=pc,size=len(b),image_offset=off,origin=0));known.add((pc,len(b)))
 need(struct.unpack_from('<I',records[0x5e0000][1],0xcc)[0]==0x479590,'Genuine original table DWORD')
 out.mkdir(parents=True)
 for p in OLD.iterdir():
  if p.name not in('report.json','pins.json')and p.is_file():(out/p.name).write_bytes(pin(p).read_bytes())
 fresh=b'MW4J124P'+struct.pack('<I',n)+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items());need(len(fresh)==len(pack),'Unchanged exact pack geometry');(out/'pages.bin').write_bytes(fresh)
 spec=text(OLD/'spec.hpp');spec=one(spec,old['pack_sha256'],sha(out/'pages.bin'))
 for field,newvalue in [('entries',0x479590),('table_slots',0x5e00cc)]:
  m=re.search(r'inline constexpr std::array<std::uint32_t,5> '+field+r'\{([^}]+)\};',spec);need(m is not None,'Exact five-root '+field)
  spec=one(spec,m[0],f'inline constexpr std::array<std::uint32_t,6> '+field+'{'+m[1]+','+hex(newvalue)+'};')
 m=re.search(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',spec);need(m is not None,'Exact source span array')
 spec=one(spec,m[0],f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings'+'{{'+','.join('{'+','.join(hex(v[k])for k in('pc','size','image_offset','origin'))+'}'for v in spans)+'}};');(out/'spec.hpp').write_text(spec)
 protocol=one(text(OLD/'protocol.hpp'),'sequences=1, roots=5','sequences=1, roots=6');(out/'protocol.hpp').write_text(protocol)
 reference=one(text(OLD/'reference.cpp'),'Five genuine widget initializer endpoints captured','Six genuine widget/font initializer endpoints captured');(out/'reference.cpp').write_text(reference)
 root=dict(root=0x479590,slot=0x5e00cc,callback=0x4795d0,registration_CALL_pc=0x4795c5,registration_return_PC=0x4795ca,callback_executed=False)
 need(len(contract['roots'])==5,'Exact five-root contract');contract['roots'].append(root);contract['instructions']+=newrows
 contract.update(new_font_root=root,new_font_object=dict(base=0x608628,extent=0x4b0,constructor=0x40e840,constructor_CALL_pc=0x4795ab,arguments=[0,0,0],source_vptr=0x5bc598,source_vptr_store_PC=0x40e880,virtual_CALL_pc=0x5a0669,slot_offset=0x8c,physical_target=0x5a0680),sequence_scope='Measured five-widget relative order followed by479590, without perphase reset or API preinvocation; not original startup table chronology',zero_font_registry_domain=dict(address=0x6384e8,value_supplied_to_execution=False,actual_value_required_by_later_validation=True),new_source_overlay=overlay,normal_counts_are_unmeasured=True,source_shutdown_callbacks_executed=False,new_root_trace_admitted=False,real_fps_formatter40F000_admitted=False)
 (out/'normal-contracts.json').write_text(json.dumps(contract,indent=2)+'\n')
 (out/'new-source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
 newgraphs={str(e):graphs[str(e)]for e in(0x479590,0x4795a0)};(out/'new-game-graphs.json').write_text(json.dumps(newgraphs,indent=2)+'\n')
 for i,a in enumerate(contract['normal_patch_spans']):
  for b in contract['normal_patch_spans'][i+1:]:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'All inherited normal source patches remain disjoint')
 broker=(out/'original_broker.hpp').read_text();m=re.search(r'inline constexpr std::array<std::uint32_t,(\d+)> bases\{([^}]+)\};',broker);reserved=[int(v,16)for v in m[2].split(',')];need(len(reserved)==35 and all(p&~65535 in reserved for p in records),'Same complete35 pre-CRT reservation bases')
 pin(__file__);pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');pin(R/'tools/m4-capture-direct/capture_direct_v3.hpp')
 for p in out.iterdir():pin(p)
 report={k:copy.deepcopy(v)for k,v in old.items()if k!='files'}
 report.update(scope='Additive authentic five-widget prefix plus479590 original normal preparation only',parent_preparation_sha256=sha(OLD/'report.json'),parent_widget_validation_sha256=sha(R/'reports/m4-widget-original/validation-r1/report.json'),source_preparation_sha256=sha(SOURCE/'report.json'),original_roots=6,original_phases=6,game_rows=1093,game_instruction_bytes=3391,source_spans=spans,pack_sha256=sha(out/'pages.bin'),new_root=0x479590,new_source_rows=12,new_source_bytes=41,new_sparse_pages=0,unchanged_GDI_FS_observer_bodies=True,sequence_reseeding=False,source_after_seed=False,provider_preinvoked=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
