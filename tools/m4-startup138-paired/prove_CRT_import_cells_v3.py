"""Physical named144-cell CRT import proof over sealed ordinary inputs; no archives."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 d=load('entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');pe=load('physicalPE',R/'tools/analysis/pe.py');policy=load('physicalPolicy',R/'tools/m4-startup138-paired/crt_page_policy_v3.py')
 oldp=pin(R/'reports/m4-startup138-paired/CRT-page-policy-r4/report.json','35fab86e1f2fe5199b69759cff6d995edd4a041ad40d9e99b8aece382c179f5e');old=json.loads(oldp.read_bytes());assert old['passed']and old['ordinary_readers_closed'];
 for path,h in old['files'].items():pin(path,h)
 dp=pin(old['domains_path'],old['domains_sha256']);domains=json.loads(dp.read_bytes());assert len(domains)==12
 gp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(gp.read_bytes());assert gate['passed']and gate['reader_closed'];e=next(x for x in gate['paired_exports']if x['branch']=='original');idx=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);selected=d.entries(idx,re.compile(r'lockit/modules/(1984036864|1997275136)/(image|path).bin'));assert len(selected)==4;modules={};modulefacts=[]
 with payload.open('rb')as f:
  for base,library in [(0x76420000,'KERNEL32.DLL'),(0x770c0000,'NTDLL.DLL')]:
   def read(suffix):
    n=f'lockit/modules/{base}/{suffix}.bin';z=selected[n];f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'];return b
   raw=read('image');path=read('path');assert library.lower()in path.decode('utf-16le').lower();im=pe.PEImage(raw);exports={n:r for r in im.exports()for n in r['names']};modules[library]=(base,exports);modulefacts.append(dict(runtime_base=base,library=library,physical_image_sha256=hashlib.sha256(raw).hexdigest(),captured_path_hex=path.hex(),captured_entry=selected[f'lockit/modules/{base}/image.bin']))
 physical_path=(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve();physical=pin(physical_path,gate['files'][str(physical_path)]);image=pe.PEImage(physical.read_bytes());assert image.image_base==0x78000000;imports=image.imports();assert len(imports)==1 and imports[0]['library'].lower()=='kernel32.dll'and len(imports[0]['symbols'])==144
 cases=[];controls=[];forwarded=0
 for domain in domains:
  rows=[];patches={r['pc']-0x7802e000:r for r in domain['patches']};a={int(k):bytes.fromhex(v)for k,v in domain['original_inputs'].items()};b={int(k):bytes.fromhex(v)for k,v in domain['native_inputs'].items()}
  for symbol in imports[0]['symbols']:
   offset=symbol['iat_rva']-0x2e000;assert 0<=offset<=4092 and offset%4==0;name=symbol['name'];base,exports=modules['KERNEL32.DLL'];ex=exports[name];chain=[dict(library='KERNEL32.DLL',name=name,rva=ex['rva'])]
   if 'forwarder'in ex:
    lib,forward=ex['forwarder'].split('.',1);assert lib=='NTDLL';base,exports=modules['NTDLL.DLL'];ex=exports[forward];assert 'forwarder'not in ex;chain.append(dict(library='NTDLL.DLL',name=forward,rva=ex['rva']));forwarded+=1
   real=base+ex['rva'];raw=image.rva_u32(symbol['iat_rva']);assert image.rva_string(raw+2)==name;installed=real;shim=False
   if offset in patches:
    patch=patches[offset];assert patch['named_API']==name;assert int.from_bytes(bytes.fromhex(patch['original_hex']),'little')==real;installed=int.from_bytes(bytes.fromhex(patch['instrumented_hex']),'little');shim=True
   assert struct.unpack_from('<I',a[0x7802e000],offset)[0]==installed and struct.unpack_from('<I',b[0x7802e000],offset)[0]==raw
   rows.append(dict(offset=offset,library=imports[0]['library'],name=name,native_raw_thunk=raw,original_real_target=real,original_installed_target=installed,observer_shim=shim,physical_export_chain=chain))
  instance=policy.Policy(a,b,domain['patches'],domain['unused_input_offsets'],rows)
  for phase in range(138):
   aa=bytearray(a[0x7802e000])
   if phase==13:
    for row in rows:
     if row['observer_shim']:struct.pack_into('<I',aa,row['offset'],row['original_real_target'])
   instance.page(phase,'before',0x7802e000,bytes(aa),b[0x7802e000],[],[])
  for label in ('raw-thunk','actual-export','missing-cell'):
   wrong=[dict(r)for r in rows]
   if label=='raw-thunk':wrong[0]['native_raw_thunk']^=1
   elif label=='actual-export':wrong[0]['original_installed_target']^=1
   else:wrong.pop()
   try:policy.Policy(a,b,domain['patches'],domain['unused_input_offsets'],wrong)
   except ValueError:controls.append(dict(level=domain['level'],sequence=domain['sequence'],name=label,refused=True))
   else:raise AssertionError(label)
  cases.append(dict(level=domain['level'],sequence=domain['sequence'],physical_import_cells=rows))
 assert forwarded==96 and len(controls)==36;assert sha(idx)==e['index_sha256']and sha(payload)==e['payload_sha256'];cp=out/'import-cells.json';cp.write_text(json.dumps(cases,indent=2)+'\n');pin(cp);pin(__file__);pin(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All144 physical named MSVCRT imports per12 own inputs resolved through captured actual32bit KERNEL32/NTDLL exports plus exact8 current observer shims; zero opaque IAT exclusions; prior wholepage carry retained',physical_named_cell_relations=1728,forwarded_relations=forwarded,module_facts=modulefacts,negative_controls=controls,prior_wholepage_relations_report_sha256=sha(oldp),physical_import_cells_path=str(cp),physical_import_cells_sha256=sha(cp),archive_reader_opened=False,ordinary_readers_closed=True,source_machine_executed=False,complete_paired_policy_admitted=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
