"""Prepare own-BEFORE pure seven-root source tools without reading observations."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh source comparison preparation');out.mkdir();pins={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact static source preparation '+str(p));pins[str(p)]=v;return p
 parent=pin(R/'tools/m4-widget-native/compare_prefix_v4.py');target=R/'tools/m4-fps-native/compare_prefix_v2.py';need(not target.exists(),'Fresh source comparer');text=parent.read_text()
 def replace(a,b,n=1):
  nonlocal text
  need(text.count(a)==n,'Exact prefix source hunk '+a);text=text.replace(a,b);changes.append(dict(before=a,after=b,count=n))
 replace('Pure six-widget source prefix','Pure seven-root widget/FPS source prefix')
 replace("out=R/'reports/m4-widget-native'","out=R/'reports/m4-fps-native'")
 replace('036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98','636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a')
 replace('58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401','bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0')
 replace('reports/m4-widget-native/fixture-build-r13','reports/m4-fps-native/fixture-build-r2');replace('reports/m4-widget-native/fixture-preparation-r16','reports/m4-fps-native/fixture-preparation-r2')
 replace("c=read(R/'reports/m4-widget-native/preparation-r3/contracts.json')","component=read(R/'reports/m4-fps-native/component-preparation-r1/report.json','294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18');c=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json',component['files'][str((R/'reports/m4-fps-native/component-preparation-r1/contracts.json').resolve())])")
 replace('reports/m4-font479590-original/source-preparation-r1/game_model.py','reports/m4-fps-original/source-preparation-r4/game_model.py')
 replace('sites=(0x5a013c,0x5a063f,0x5a074b);slots=(0x5bb070,0x5bb074,0x5bb068);targets=(0x71f00010,0x71f00020,0x71f00030)','sites=(0x5a013c,0x5a063f,0x5a074b);slots=(0x5bb070,0x5bb074,0x5bb068);targets=(0x71f00010,0x71f00020,0x71f00030)')
 replace("need(len(service_before)==6,'Six actual borrowed-provider entry checkpoints')","need(len(service_before)==7,'Seven actual borrowed-provider entry checkpoints')")
 replace('boundary_index=[0];undefined={};FS=[];FP=fx','boundary_index=[0];undefined={};FS=[];FP=fx;formatter=[];dispatches=[]')
 replace('      return super().read(address,size,domain,pc)',"""      result=super().read(address,size,domain,pc)
      if domain=='source'and source_pc==0x7800fcef:
       need(root_pc==0x40f000 and address==0x780103fa and size==4 and result==0x7800fe25 and self.reg('eax')==0,'Exact source-derived finite index0 readonly character route')
       dispatches.append((root_pc,source_pc,address,result,len(dispatches),self.call_stack[-1][1],len(self.accesses)-1+access_start,self.reg('eax')))
      return result""")
 replace("      row=self.program.get(self.cursor);need(row is not None,'Recovered literal widget source PC');next_undefined=F.advance(self,row,undefined);", """      if self.cursor in(0x780230dd,0x5a2f6e):
       need(root_pc==0x40f000,'Only actual FPS format source boundary');frame_=frame-140;destination=root['object']+0x34;va=frame-108
       need(self.reg('esp')==frame_+(4 if self.cursor==0x5a2f6e else 0),'Literal format boundary stack geometry')
       formatter.append(dict(PC=self.cursor,CPU=tuple(self.projected_cpu()),undefined=dict(undefined),FX=bytes(self.fx),frame=self.bytes(frame_,64),destination=self.bytes(destination,512),va=self.bytes(va,64),format=self.bytes(0x5e1590,16)))
      row=self.program.get(self.cursor);need(row is not None,'Recovered literal widget/FPS source PC');next_undefined=F.advance(self,row,undefined);""")
 marker="    cumulative_apis=raw(after_dir/'APIs.bin');"
 replace(marker,"""    slot=0x5bb53c;owner=next(a for a,b in memory.items()if a<=slot<slot+4<=a+len(b));imports[(0x5a2f68,slot)]=dict(raw_value=words(bytes(memory[owner]),1,slot-owner)[0],target=0x780230dd)
    cumulative_apis=raw(after_dir/'APIs.bin');""")
 marker="    native_FS=rows(raw(after_dir/'FS-events.bin'),32,'<8I')[FS_start:];"
 replace(marker,"""    format_raw=raw(after_dir/'formats.bin');native_dispatch=rows(raw(after_dir/'format-dispatches.bin'),32,'<8I')
    if root_pc!=0x40f000:need(not formatter and not dispatches and not format_raw and not native_dispatch,'Six earlier roots retain null-format domain')
    else:
     need(len(formatter)==2 and len(format_raw)==2528 and len(dispatches)==3,'One complete literal formatter lifetime and three exact dispatches');w=struct.unpack_from('<16Q',format_raw);need(w[:12]==(1,root_pc,0x5a2f68,0x780230dd,frame-140,0x5a2f6e,root['object']+0x34,0x5e1590,frame-108,512,16,64)and w[12]==formatter[1]['CPU'][0]and w[13]>0 and w[14:]==(3,1),'Complete16Q measured formatter context');need(all(a['words'][12]==w[13]for a in api_records),'Actual same current native thread identity')
     for side,base in enumerate((128,168)):eq(F.project(formatter[side]['CPU'],formatter[side]['undefined']),F.project(words(format_raw,10,base),formatter[side]['undefined']),'Whole defined formatter CPU40 side')
     for field,offset,size in(('FX',208,512),('destination',1232,512),('frame',2256,64),('va',2384,64)):
      for side in(0,1):eq(formatter[side][field],format_raw[offset+side*size:offset+(side+1)*size],'Complete literal formatter '+field+' side')
     eq(formatter[0]['format'],format_raw[2512:2528],'Whole16B physical finite format input');eq(native_dispatch,dispatches,'Full8DWORD source index/cell/target/frame/access character ledger');counts['literal_formatter_lifetimes']+=1;counts['whole_formatter_defined_CPU40_sides']+=2;counts['whole_formatter_frame64_sides']+=2;counts['whole_formatter_destination512_sides']+=2;counts['whole_formatter_FX512_sides']+=2;counts['whole_formatter_va64_sides']+=2;counts['literal_character_dispatches']+=3
    native_FS=rows(raw(after_dir/'FS-events.bin'),32,'<8I')[FS_start:];""")
 replace("counts['literal_prefixes']==12 and counts['actual_GDI_scalar_response_joins']==294 and counts['exact_prefix_operand_rows']==49250 and counts['FS_source_relations']==1158 and counts['virtual_source_relations']==1010 and counts['array_source_relations']==150","counts['literal_prefixes']==14 and counts['actual_GDI_scalar_response_joins']==298 and counts['exact_prefix_operand_rows']==49964 and counts['FS_source_relations']==1176 and counts['virtual_source_relations']==1022 and counts['array_source_relations']==150 and counts['literal_formatter_lifetimes']==2 and counts['literal_character_dispatches']==6")
 replace('Exact both-level current six-root finite prefix extent','Exact both-level current seven-root finite prefix extent')
 replace(" memory[0x20001000]=bytearray(raw(folder/'stack.bin'))", """ for f in sorted(folder.glob('provider-source-page-*.bin')):
  address=int(f.stem.removeprefix('provider-source-page-'));b=raw(f);need(len(b)==4096 and not any(a<address+4096 and address<a+len(v)for a,v in memory.items()),'Whole nonoverlapping current provider source input page');memory[address]=bytearray(b)
 need({address for address in memory if address>=0x78000000}=={0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000},'Five exact own provider BEFORE source pages')
 memory[0x20001000]=bytearray(raw(folder/'stack.bin'))""")
 replace("    derivations.append(dict(level=level,phase=phase,root=root_pc", """    for f in sorted((phase_dir/'before').glob('provider-source-page-*.bin')):
     address=int(f.stem.removeprefix('provider-source-page-'));expected=raw(f)
     if address==0x78037000:
      observed=raw(prefix/f'registry-checkpoint-{n}-page-{address}.bin');eq(m.bytes(address,4096),observed,'Whole carried CRT RW page at source-derived actual registry provider entry')
     else:
      observed=raw(phase_dir/'after'/f.name);eq(m.bytes(address,4096),observed,'Whole provider source/readonly page carried through literal current prefix and registry service')
     counts['whole_current_provider_source_page_joins']+=1
    derivations.append(dict(level=level,phase=phase,root=root_pc""")
 replace("counts['literal_formatter_lifetimes']==2 and counts['literal_character_dispatches']==6", "counts['literal_formatter_lifetimes']==2 and counts['literal_character_dispatches']==6 and counts['whole_current_provider_source_page_joins']==70")
 pin(R/'tools/m4-fps-native/derive_source.py');pin(R/'tools/m4-fps-native/derive_source_v2.py');pin(R/'reports/m4-fps-native/fixture-preparation-r2/provider-page-contracts.json')
 ast.parse(text);target.write_text(text);pin(target)
 q=out/'prefix-source-relations.json';q.write_text(json.dumps(changes,indent=2)+'\n');pin(q)
 for p in(Path(__file__),R/'reports/m4-fps-native/controller-preparation-r3/report.json',R/'reports/m4-fps-native/component-preparation-r1/report.json',R/'reports/m4-fps-original/source-r3/report.json',R/'reports/m4-fps-original/source-preparation-r4/game_model.py'):pin(p)
 report=dict(passed=True,scope='Seven-root own-BEFORE prefix comparer prepared and parsed only; no observation consumed',prefix_entrypoint=str(target),prefix_sha256=sha(target),source_changes=len(changes),prefix_operand_rows_per_level=24982,formatter_defined_CPU40_sides_per_level=2,literal_formatter_dispatches_per_level=3,whole_after_seed=False,expected_formatter_output_or_CPU_input=False,host_vsprintf=False,archive_reader_opened=False,actual_worker_launches=0,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True)))
if __name__=='__main__':main(sys.argv[1])
