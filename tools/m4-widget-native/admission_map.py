"""Compile and source inventory for an independent reviewer; no worker launch."""
from pathlib import Path
import collections,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower() not in ('.mwb','.zip'),'No archives');v=sha(p);need(h is None or v==h,'Physical pin '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def coff(p):
 data=pin(p).read_bytes();machine,n,stamp,table,total,optional,flags=struct.unpack_from('<HHIIIHH',data);need(machine==0x8664 and not optional,'Actual AMD64 COFF');strings=table+18*total;end=strings+struct.unpack_from('<I',data,strings)[0];need(end<=len(data),'Complete string table');symbols={};i=0
 while i<total:
  raw,value,section,typ,storage,aux=struct.unpack_from('<8sIhHBB',data,table+18*i)
  if raw[:4]==bytes(4):start=strings+struct.unpack_from('<I',raw,4)[0];need(strings+4<=start<end,'Bounded symbol name');raw=data[start:data.index(b'\0',start,end)]
  else:raw=raw.rstrip(b'\0')
  symbols[i]=dict(name=raw.decode('utf-8'),value=value,section=section,type=typ,storage=storage);i+=1+aux
 sections={};counts=collections.Counter();non=[];functions=[]
 for j in range(n):
  start=20+40*j;name=data[start:start+8].rstrip(b'\0').decode('ascii');size,raw,reloc,_,number=struct.unpack_from('<IIIIH',data,start+16);flags=struct.unpack_from('<I',data,start+36)[0];need((raw+size<=len(data)or not raw and flags&0x80)and reloc+number*10<=len(data),'Whole section and relocation bytes');sec=data[raw:raw+size]if raw else b'';rs=[]
  for k in range(number):
   offset,target,typ=struct.unpack_from('<IIH',data,reloc+10*k);need(target in symbols,'Exact relocation target symbol');counts[typ]+=1;row=dict(section=j+1,section_name=name,offset=offset,type=typ,symbol=symbols[target]);rs.append(row)
   if typ not in range(4,10):row['raw_relocation_bytes_hex']=sec[offset:offset+(8 if typ==1 else 4)].hex();non.append(row)
  sections[j+1]=dict(name=name,bytes=sec,size=size,flags=flags,relocations=rs)
 for index,s in symbols.items():
  if s['section']<=0 or s['type']!=0x20:continue
  sec=sections[s['section']];ends=[t['value']for t in symbols.values()if t['section']==s['section']and t['type']==0x20 and t['value']>s['value']];last=min(ends,default=len(sec['bytes']));raw=sec['bytes'][s['value']:last];functions.append(dict(s,COFF_symbol_index=index,extent_bytes=len(raw),unrelocated_sha256=hashlib.sha256(raw).hexdigest(),relocations=[r for r in sec['relocations']if s['value']<=r['offset']<last]))
 return dict(object=str(p),sha256=sha(p),machine=machine,TimeDateStamp=stamp,all_function_definitions=functions,all_non_REL32_relocations=non,all_relocation_type_counts=dict(counts),section_count=n)
def main(name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh map');out.mkdir();bpath=R/'reports/m4-widget-native/fixture-build-r9/build.json';b=read(bpath,'4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60');p=read(R/'reports/m4-widget-native/fixture-preparation-r9/report.json',b['preparation_sha256']);c=read(R/'reports/m4-widget-native/preparation-r3/report.json',p['component_preparation_sha256']);lib=read(R/'reports/m4-widget-native/build-r5/build.json',p['component_build_sha256']);service=read(R/'reports/m4-widget-native/service-preparation-r2/report.json',p['service_preparation_sha256']);need(b['passed']and p['passed']and lib['passed'],'Current builds passed');maps={}
 for level in ('O0','O2'):
  objs=[bpath.parent/level/'fixture.obj',bpath.parent/level/'registry.obj']+[Path(r['path'])for r in lib['levels'][level]['objects']];maps[level]=[coff(o)for o in objs]
  for q,h in b['files'].items():pin(q,h)
 contracts=read(R/'reports/m4-widget-native/preparation-r3/contracts.json');need(sum(len(e['source_read_PC_and_frame_offsets'])for e in contracts['registration_epilogues'])==18,'All source-only tail reads')
 sources={v:dict(path=str(Path(q)),sha256=pin(q)and sha(Path(q)))for v,q in [('component',R/'reports/m4-widget-native/preparation-r3/component.cpp'),('API/caller_ASM',R/'reports/m4-widget-native/preparation-r3/native_api.s'),('fixture',R/'reports/m4-widget-native/fixture-preparation-r9/fixture.cpp'),('inherited_definitions',R/'reports/m4-widget-native/fixture-preparation-r9/inherited_main.cpp'),('borrowed_Service',R/'tools/m4-widget-native/borrowed_onexit_v2.inc'),('Session_definition',R/'reports/m4-widget-native/service-preparation-r2/session_impl.inc')]}
 for q,h in service['files'].items():pin(q,h)
 metadata=dict(schedule=[hex(x)for x in c['roots']],caller='One authored external CPU/CW/TOP before bootstrap; same actual admitted Runtime/State and current persistent accepted registry Session, six real registered callbacks, no per-root seed',service='Committed source CALL5AC11E→actual accepted CRT78004A36; six callback publications, current producer allocation; literal source CRT free and five native CS deletes/same HeapDestroy on explicit Session.finish. Source callbacks/shutdown are not invoked.',GDI='Real current GetStockObject/DeleteObject/CreateFontA; guest logical handles are distinct from 64-bit native handles. Only owned CreateFont successes get manual reverse DeleteObject cleanup. No borrowed stock cleanup.',source_steps=dict(observed_prefix_operands=24625,literal_epilogue_read_operands=18,total_operand_guards=24643,physical_instruction_rows=1093,literal_bodies=51,GDI=147,virtuals=505,FS=579,array_iterations=75),substitutions=['51IR symbol-prefix changes only mw34_onexit_game_→mw34_widget_game_','Borrowed service adds only Session.hpp and session_impl.inc; all69 remaining native19 files byte-identical','Inherited definitions preserve code except two disambiguated absolute Session include paths; main and need renamed by visible preprocessor macros; renamed inherited main never called','Actual forced per-level registry header and parent per-level adapter headers; no semantic template edits','Only literal epilogue PC/order/stack-role entries augment the observed prefix tables; no source values copied'],comparison='Prepared own-BEFORE persistent literal model plus current measured native GDI volatile projections; complete stack/frame/page and actual accepted provider proof are pending fresh execution; no original numerical/GDI handle/AFTER seed',open_claims=['Current full136 startup chronology','Source callback dispatch/shutdown','Cold GDI error/unwind path','Actual causal refusal execution','Individual source every-instruction observation','Native GDI physical owner/export observation and whole outside Session.cleanup caller proof'])
 pin(__file__);proof=out/'COFF-function-relocation-inventory.json';proof.write_text(json.dumps(maps,indent=2)+'\n');pin(proof);report=dict(passed=True,scope='Concrete compiler/source admission inventory only; independent final-linked attribution and first writer admission belong to root',build_path=str(bpath),build_sha256=sha(bpath),preparation_sha256=b['preparation_sha256'],component_preparation_sha256=p['component_preparation_sha256'],sources=sources,metadata=metadata,files=PINS,archive_reader_opened=False,native_executed=False,initializer_credit=0);f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(f),sha256=sha(f))))
if __name__=='__main__':main(sys.argv[1])
