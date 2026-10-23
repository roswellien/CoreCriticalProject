"""Bounded read-only compile/source/object/library/current-worker linkage; no source run."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-paired/constructor-entry-linkage-r1';assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def receipt(p,h=None):return json.loads(pin(R/p,h).read_bytes())
 C=receipt('reports/m4-constructor-native/build-r5/build.json');W=receipt('reports/m4-startup141-runway/build-r3/build.json','ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc');N=receipt('reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3');X=receipt('reports/m4-startup141-root/execution-r2/report.json','536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6');P=json.loads(pin(C['preparation_path'],C['preparation_sha256']).read_bytes());assert C['passed']and W['passed']and N['passed']and N['reader_closed']and C['preparation_sha256']=='d291ae395b5ee16243f160daba61d360a08142188c84291f4c7458bc86693384'
 source=pin(R/'reports/m4-constructor-native/preparation-r7/component.cpp','e0c28723fb1e0b03ad17da292498810981cc8ba06e25266cefd9c51095cdbeae');assert source.read_text().index('session.constructor_scope(s,root,true)')<source.read_text().index('checkpoint("before")')<source.read_text().index('literal::body(entry)')
 def declared(files,p):
  hits=[h for q,h in files.items()if Path(q).resolve()==Path(p).resolve()];assert len(set(hits))==1;return hits[0]
 cases=[]
 for level,L in C['levels'].items():
  objrow=next(v for v in L['objects']if Path(v['path']).name=='component.obj');obj=pin(objrow['path'],objrow['sha256']);lib=pin(L['library'],L['library_sha256']);worker=pin(W['workers'][level]['path'],W['workers'][level]['sha256']);assert sha(lib)==declared(W['files'],lib);pin(source,declared(C['files'],source))
  for dep in L['actual_compiler_header_dependencies']:pin(dep,declared(C['files'],dep))
  compilecmd=[c for c in C['commands']if str(source)in [str(Path(v).resolve())for v in c['argv']if v.endswith('component.cpp')]and str(obj)in [str(Path(v).resolve())for v in c['argv']if v.endswith('component.obj')]];assert len(compilecmd)==1 and compilecmd[0]['exit_code']==0 and '-'+level in compilecmd[0]['argv']and '-c'in compilecmd[0]['argv'];pin(compilecmd[0]['argv'][0],declared(C['files'],compilecmd[0]['argv'][0]))
  depfile=pin(obj.with_suffix('.d'),declared(C['files'],obj.with_suffix('.d')));assert 'component.cpp'in depfile.read_text()
  archivecmd=[c for c in C['commands']if any(v.startswith('/out:')and Path(v[5:]).resolve()==lib for v in c['argv'])];assert len(archivecmd)==1 and archivecmd[0]['exit_code']==0 and any(Path(v).resolve()==obj for v in archivecmd[0]['argv'][1:]if v.endswith('.obj'))
  data=lib.read_bytes();assert data[:8]==b'!<arch>\n';offset=8;members=[]
  while offset<len(data):
   h=data[offset:offset+60];assert len(h)==60 and h[58:]==b'`\n';size=int(h[48:58]);payload=data[offset+60:offset+60+size];assert len(payload)==size
   if payload==obj.read_bytes():members.append(dict(header_offset=offset,payload_bytes=size,sha256=sha(obj)))
   offset+=60+size+(size%2)
  assert len(members)==1 and offset==len(data)
  d=obj.read_bytes();machine,nsec,_,sptr,nsyms,opt,_=struct.unpack_from('<HHIIIHH',d);assert machine==0x8664 and opt==0;st=sptr+18*nsyms;symbols={};i=0
  while i<nsyms:
   z=d[sptr+i*18:sptr+(i+1)*18];name=d[st+struct.unpack_from('<I',z,4)[0]:].split(b'\0',1)[0].decode()if z[:4]==bytes(4)else z[:8].rstrip(b'\0').decode();value,sec,typ,storage,aux=struct.unpack_from('<IhHBB',z,8);symbols[i]=(name,value,sec);i+=1+aux
  invoke=[v for v in symbols.values()if v[0].startswith('?invoke@Impl@Component@')];assert len(invoke)==1 and invoke[0][1]==0;sec=20+(invoke[0][2]-1)*40;size,rawptr,rptr=struct.unpack_from('<III',d,sec+16);nr=struct.unpack_from('<H',d,sec+32)[0];body=d[rawptr:rawptr+size];relocs=[]
  for j in range(nr):
   at,symbol,kind=struct.unpack_from('<IIH',d,rptr+10*j);assert kind==4 and at+4<=size;relocs.append(dict(offset=at,type=kind,symbol=symbols[symbol][0]))
  scope=[v for v in relocs if 'constructor_scope@Session@'in v['symbol']];checkpoints=[v for v in relocs if '?checkpoint@Impl@Component@'in v['symbol']];literal=[v for v in relocs if '?body@literal@m4_constructor_native@'in v['symbol']];assert len(scope)==len(checkpoints)==2 and len(literal)==1 and scope[0]['offset']<checkpoints[0]['offset']<literal[0]['offset']<scope[1]['offset']<checkpoints[1]['offset'];assert all(body[v['offset']-1]==0xe8 for v in scope)
  # COFF linker relocation operands alone are resolved, never acceptance bytes masked.
  used={at+k for v in relocs for at in [v['offset']]for k in range(4)};segments=[];start=0
  for at in sorted(used):
   if at>start:segments.append((start,body[start:at]))
   start=at+1
  if start<len(body):segments.append((start,body[start:]));anchor_at,anchor=max(segments,key=lambda v:len(v[1]));exe=worker.read_bytes();pe=struct.unpack_from('<I',exe,60)[0];count=struct.unpack_from('<H',exe,pe+6)[0];os=struct.unpack_from('<H',exe,pe+20)[0];sections=[]
  for j in range(count):
   so=pe+24+os+j*40;vs,va,rs,rp=struct.unpack_from('<IIII',exe,so+8);sections.append((va,rp,rs))
  hits=[];at=exe.find(anchor)
  while at!=-1:
   base=at-anchor_at
   if base>=0 and base+size<=len(exe)and all(exe[base+j]==body[j]for j in range(size)if j not in used):hits.append(base)
   at=exe.find(anchor,at+1)
  assert len(hits)==1;fileoff=hits[0];rva=next(va+fileoff-rp for va,rp,rs in sections if rp<=fileoff<rp+rs);targets=[rva+v['offset']+4+struct.unpack_from('<i',exe,fileoff+v['offset'])[0]for v in scope];assert targets[0]==targets[1]
  config=[c for c in W['commands']if any(v.startswith('-DMW34_CONSTRUCTOR_LIBRARY=')and Path(v.split('=',1)[1]).resolve()==lib for v in c['arguments'])];assert len(config)==1 and config[0]['exit_code']==0
  ninja=pin(worker.parent/'build.ninja');lines=ninja.read_text().splitlines();assert any('LINK_LIBRARIES' in x and str(lib).replace(chr(92)+chr(92),chr(92))in x for x in lines);cmake=pin(R/'reports/m4-startup141-runway/preparation-r3/CMakeLists.txt',declared(W['files'],R/'reports/m4-startup141-runway/preparation-r3/CMakeLists.txt'));assert '"${MW34_CONSTRUCTOR_LIBRARY}"'in cmake.read_text()
  cases.append(dict(level=level,source_sha256=sha(source),component_object_sha256=sha(obj),library_sha256=sha(lib),actual_worker_sha256=sha(worker),compiler_command=compilecmd[0],archive_command=archivecmd[0],configure_command=config[0],exact_component_archive_member=members[0],invoke_symbol=invoke[0][0],invoke_code_bytes=size,object_relocations=relocs,entry_guard_before_checkpoint_before_literal=True,whole_nonrelocated_object_body_uniquely_in_actual_worker=True,worker_invoke_RVA=rva,same_resolved_Session_constructor_scope_RVA=targets[0],complete_53_pair_policy_claim=False))
 for p,h in pins.items():assert sha(p)==h
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Finite physical current component source compile provenance, exact object library membership, current worker linkage and invoke ordering; not CPU execution or M4 acceptance',cases=cases,source_evaluated=False,worker_launched=False,capture_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(dict(report_sha256=sha(q),cases=len(cases),files=len(pins)))
if __name__=='__main__':main()
