"""Independent static component142 source/library readiness; no execution."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def members(raw):
 assert raw[:8]==b'!<arch>\n';at=8;rows=[]
 while at<len(raw):
  h=raw[at:at+60];assert len(h)==60 and h[58:60]==b'`\n';n=int(h[48:58]);blob=raw[at+60:at+60+n];assert len(blob)==n;rows.append(dict(header_name=h[:16].decode('ascii').strip(),offset=at,bytes=n,sha256=hashlib.sha256(blob).hexdigest()));at+=60+n+(n%2)
 assert at==len(raw);return rows
def coff_function(raw,name):
 machine,count,timestamp,table,symbols,optional,flags=struct.unpack_from('<HHIIIHH',raw);assert machine==0x8664 and optional==0
 strings=raw[table+18*symbols:];size=struct.unpack_from('<I',strings)[0];assert size<=len(strings);found=[];i=0
 while i<symbols:
  entry=raw[table+18*i:table+18*i+18];assert len(entry)==18
  zero,offset=struct.unpack_from('<II',entry)
  label=strings[offset:].split(b'\0',1)[0].decode()if zero==0 else entry[:8].split(b'\0',1)[0].decode()
  value,section,typ,storage,aux=struct.unpack_from('<IhHBB',entry,8)
  if label==name:found.append((value,section,typ,storage))
  i+=1+aux
 assert len(found)==1;value,section,typ,storage=found[0];assert section>0 and typ==0x20
 header=raw[20+40*(section-1):20+40*section];length,start=struct.unpack_from('<II',header,16);assert value<length
 return dict(section=section,section_offset=value,object_offset=start+value,first16_hex=raw[start+value:start+value+16].hex())
def main():
 out=R/'reports/m4-142-component-review/static-review-r1';out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'and p.drive.upper()!='G:';v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def receipt(p,h=None):
  p=pin(p,h);j=json.loads(p.read_bytes());assert j['passed']
  for q,v in j.get('files',{}).items():pin(q,v)
  return j
 prep=R/'reports/m4-startup142-runway/component-preparation-r3';build=R/'reports/m4-startup142-runway/component-build-r2'
 prepared=receipt(prep/'report.json','353213df81b3fa35839c6024acd8e92697882de858b980af4fb1a436a97f5c08');compiled=receipt(build/'build.json','d5af15dbddcdbc3a8ada9739c3d7ad04dee6f047a9077e1e65d316c090978533');controls=receipt(R/'reports/m4-startup142-runway/component-controls-r1/report.json','991166ad045aabcffa1b50eaafd0e7da83bd86e6a9e31dd9f3a6a144b5d3d077')
 assert prepared['carried_domain_admitted']is False and compiled['carried_domain_admitted']is False and controls['current142_input_domain_proved']is False
 for q,h in compiled['artifacts'].items():pin(q,h)
 inverse=json.loads(pin(prep/'source-inverse.json').read_bytes());parent=pin(inverse['parent_source'],inverse['parent_sha256']).read_text(encoding='utf-8');code=pin(prep/'component.cpp').read_text(encoding='utf-8');tail=inverse['added_component_tail'];assert code.endswith(tail);prefix=code[:-len(tail)];restored=prefix
 for d in reversed(inverse['changes']):assert restored.count(d['new'])==1;restored=restored.replace(d['new'],d['old'])
 assert restored+inverse['removed_standalone_tail']==parent and len(inverse['changes'])==6
 a='static Context &owner(void *p)';z='#include "generated_bridges.inc"';assert prefix[prefix.index(a):prefix.index(z)+len(z)]==parent[parent.index(a):parent.index(z)+len(z)]
 source_ASM=pin(R/'tools/m4-hypot-native/hardware_boundary.s').read_text(encoding='utf-8');ASM=pin(prep/'hardware_boundary.s').read_text(encoding='utf-8');assert ASM.replace('mw34_hypot_borrow_hardware_call','hypot_hardware_call').replace('mw34_hypot_borrow_invoke_guarded','hypot_invoke_guarded')==source_ASM
 assert 'bool Component::carried_domain_admitted()noexcept{return false;}'in tail and tail.index('need(Component::carried_domain_admitted()')<tail.index('r.memory().load<unsigned>')
 assert all(x not in tail for x in('std::memset','std::memcpy','r.memory().write','Runtime::from_admitted_image','register_translation','freeze_registry'))
 assert 'Exact source DF assumption retained'in prefix and (0x8d5&(1<<10))==0
 artifact_rows=[]
 for level in ('O0','O2'):
  row=compiled['libraries'][level];lib=pin(row['path'],row['sha256']);library_members=members(lib.read_bytes());objects=prepared['objects'][level];assert len(objects)==len(set(objects))==21 and row['literal_objects']==objects
  matches=[]
  for p in objects:
   q=pin(p,prepared['files'][str(Path(p).resolve())]);hits=[v for v in library_members if v['sha256']==sha(q)and v['bytes']==q.stat().st_size];assert len(hits)==1;matches.append(dict(object=str(q),member=hits[0]))
  hardware=pin(row['hardware']);assert sum(v['sha256']==sha(hardware)for v in library_members)==1
  obj=pin(build/('build-'+level)/'CMakeFiles/hypot-borrow.dir/component.cpp.obj');assert sum(v['sha256']==sha(obj)for v in library_members)==1
  frontier=coff_function(obj.read_bytes(),'?carried_domain_admitted@Component@m4_hypot_borrow@mw34@@SA_NXZ');expected='31c02401c3'if level=='O0'else'31c0c3';assert frontier['first16_hex'].startswith(expected)
  artifact_rows.append(dict(level=level,library=str(lib),members=len(library_members),whole_literal_object_members=matches,compiled_closed_frontier=frontier,hardware_whole_member=True,component_whole_member=True))
 spec=pin(prep/'fixture_spec_O0.hpp').read_text();spec2=pin(prep/'fixture_spec_O2.hpp').read_text();pattern=r'\{(\d+)U,(\d+)U,(\d+)U,(\d+)U\}';accesses=[tuple(map(int,x))for x in re.findall(pattern,spec)];assert len(accesses)==616 and accesses==[tuple(map(int,x))for x in re.findall(pattern,spec2)]
 written=set();inputs=set();input_occurrences=[]
 for index,(pc,address,width,writing)in enumerate(accesses):
  assert width in(1,2,4,8,10,28)
  if writing:written.update(range(address,address+width))
  else:
   missing={p for p in range(address,address+width)if p not in written};inputs.update(missing)
   if missing:input_occurrences.append(dict(index=index,pc=pc,address=address,width=width,source_input_bytes=sorted(missing)))
 ranges=[]
 for p in sorted(inputs):
  if ranges and ranges[-1]['address']+ranges[-1]['bytes']==p:ranges[-1]['bytes']+=1
  else:ranges.append(dict(address=p,bytes=1))
 assert ranges==[dict(address=0x5bb5b0,bytes=4),dict(address=0x5c93a8,bytes=8),dict(address=0x20001800,bytes=4),dict(address=0x7802ffb8,bytes=8),dict(address=0x7803b738,bytes=4)]
 pages=sorted({a&~4095 for pc,a,w,wr in accesses});old=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes());missing=sorted(set(pages)-set(old['observed_pages']+old['extra_whole_source_pages']));assert missing==[0x7802f000,0x7803b000]
 pe_tool=pin(R/'tools/analysis/pe.py');sp=importlib.util.spec_from_file_location('hypot142_static_PE',pe_tool);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);crt=m.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());disk=[]
 for address,width in((0x7802ffb8,8),(0x7803b738,4)):
  sec=next(s for s in crt.sections if crt.image_base+s['virtual_address']<=address<crt.image_base+s['virtual_address']+max(s['virtual_size'],s['raw_size']));offset,_=crt.rva_range(address-crt.image_base,width);disk.append(dict(address=address,bytes=width,section=sec['name'],writable=bool(sec['characteristics']&0x80000000),physical_disk_hex=crt.data[offset:offset+width].hex(),actual_carried_value_proven=False))
 order=json.loads(pin(R/'reports/m4-startup142-runway/readiness-r1/selected-order142.json').read_bytes());current=json.loads(pin(R/'reports/m4-startup141-runway/preparation-r3/selected-order.json').read_bytes());assert len(order)==142 and [x for x in order if x['entry']!=0x4b5910]==current and order[82]==dict(slot=0x5e0154,entry=0x4b5910)
 pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');pin(__file__)
 data=dict(libraries=artifact_rows,source_before_byte_ranges=ranges,first_read_before_write_occurrences=input_occurrences,source_operand_pages=pages,missing_current69_observation_pages=missing,physical_CRT_input_cells=disk)
 p=out/'physical-readiness.json';p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');pin(p)
 gates=[
 'Establish exact current141 prefix before insertion phase82; prove actual broker CALL preparation to4B5910/frame20001800/return410A80 without borrowing a different root AFTER or standalone State/page pack.',
 'Prove all28 source-read-before-write bytes, actual named hypotIAT5BB5B0/module ownership, readonly CRT constant7802FFB8, and writable CRTglobal7803B738. Raw disk zero at writable cell is not actual carried input; source-owned load plus exhaustive prior writes/typed opaque API effects or genuine earlier input plus causal carry required.',
 'Prove whole carried State3504/CPU40/FX512, normalized masked sourceCW, actual TOP/tag/ST raw80 and defined/undefined flags select exactly retained616 operand/PC branch; verify segments23/2B/2B and DF0 from current source, not sequence-number assumption.',
 'Prepare source-admitted immutable component derivative, then current142 callback registration and observation geometry including two extra operand pages, exact two cdecl intervals/RET4/caller cleanup, nine source F32 stores and current raw80/C1 hardware seams; no state/page/owner reseed.',
 'Build and independently review whole current142 link/relocations/typed targets/TLS/private owners+callbacks and actual compiler inputs; adapt all8 same-runtime poison/retry controls. Static-library membership alone is not final-link or worker admission.'
 ]
 report=dict(passed=True,independent_static_review=True,source_six_delta_inverse=True,numeric_callback_body_byteidentical=True,hardware_two_symbol_inverse=True,whole_literal_objects_verified=42,compiled_false_frontier_verified_both_levels=True,source_operand_count=616,first_read_before_write_input_bytes=28,current_physical_insertion_phase=82,carried142_source_domain_proven=False,full_current142_worker_exists=False,prelaunch_ready=False,smallest_next_gate=gates[0:3],subsequent_gates=gates[3:],source_evaluator_executed=False,native_worker_launched=False,canonical_reader_opened=False,ordinary_payload_reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(p),inputs=len(files),literal_members=42)))
if __name__=='__main__':main()
