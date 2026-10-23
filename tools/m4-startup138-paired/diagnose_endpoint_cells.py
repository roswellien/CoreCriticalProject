"""Narrow ordinary sealed-export CPU/FX/ENV cells, no capture reader/source model."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def entries(index,pattern):
 result={}
 with index.open(encoding='utf8')as f:
  for line in f:
   hit=re.fullmatch(r'    ("(?:[^"\\]|\\.)*"): \{\n',line)
   if not hit:continue
   name=json.loads(hit[1]);body=''
   for line in f:
    if line.startswith('    }'):break
    body+=line
   if pattern.fullmatch(name):
    value=json.loads('{'+body+'}');assert set(value)=={'offset','bytes','sha256'}and name not in result;result[name]=value
 return result

def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 report_path=pin(R/'reports/m4-startup138-original/original-validation-r3/report.json','02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f');report=json.loads(report_path.read_bytes());assert report['passed']and report['reader_closed'];row=report['paired_exports'][0];assert row['branch']=='original';oi=pin(row['index_path'],row['index_sha256']);op=Path(row['payload_path'])
 ni=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/paired/O0/index.json');np=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/paired/O0/payload.bin';native_payload_size=np.stat().st_size
 oe=entries(oi,re.compile(r'phase/[0-5]/\d+\.bin'));ne=entries(ni,re.compile(r'sequence-[0-5]/phase-\d+\.bin'));assert len(oe)==len(ne)==828
 schedule=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161').read_bytes())['selected_order'];rows=[]
 def data(f,index,key,extent):
  v=index[key];assert v['bytes']==extent;f.seek(v['offset']);raw=f.read(extent);assert len(raw)==extent and hashlib.sha256(raw).hexdigest()==v['sha256'];return raw
 with op.open('rb')as original,np.open('rb')as native:
  for seq in range(6):
   for phase,root in enumerate(schedule):
    a=data(original,oe,f'phase/{seq}/{phase}.bin',356992);b=data(native,ne,f'sequence-{seq}/phase-{phase}.bin',159716)
    for side,co,fo,eo in [('before',36,116,2164),('after',76,628,2192)]:
     cpu_a=list(struct.unpack_from('<10I',a,co));cpu_b=list(struct.unpack_from('<10I',b,co));fxa=a[fo:fo+512];fxb=b[fo:fo+512];enva=a[eo:eo+28];envb=b[eo:eo+28]
     # Existing accepted hardware capability descriptor projection only, not FP value masks.
     projected=bytearray(fxb);projected[28:32]=fxa[28:32]
     rows.append(dict(sequence=seq,phase=phase,root=root['entry'],side=side,original_CPU=cpu_a,native_CPU=cpu_b,CPU_differences=[i for i in range(10)if cpu_a[i]!=cpu_b[i]],original_FX_hex=fxa.hex(),native_FX_hex=fxb.hex(),FX_differences=[i for i,(x,y)in enumerate(zip(fxa,fxb))if x!=y],FX_differences_except_physical_MXCSR_MASK=[i for i,(x,y)in enumerate(zip(fxa,projected))if x!=y],original_ENV_hex=enva.hex(),native_ENV_hex=envb.hex(),ENV_differences=[i for i,(x,y)in enumerate(zip(enva,envb))if x!=y]))
 assert sha(oi)==pins[str(oi)]and sha(ni)==pins[str(ni)]and np.stat().st_size==native_payload_size
 p=out/'cells.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable)
 counts=dict(whole_cells=len(rows),CPU_nonvolatile_or_EAX_ESP_PC_differing_cells=sum(any(i in r['CPU_differences']for i in(0,3,4,5,6,7,9))for r in rows),CPU_ECX_or_flags_differing_cells=sum(any(i in r['CPU_differences']for i in(1,8))for r in rows),whole_FX_except_physical_MXCSR_MASK_differing_cells=sum(bool(r['FX_differences_except_physical_MXCSR_MASK'])for r in rows),whole_ENV_differing_cells=sum(bool(r['ENV_differences'])for r in rows))
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Narrow whole ordinary original/current exploratory O0 source6 per-entry-authenticated CPU10/FX512/ENV28 cells only; complete active native source gate not admitted',counts=counts,original_validation_sha256=sha(report_path),native_source_pass_admission=False,native_export_index_sha256=sha(ni),raw_entry_extents_digests_checked=True,full_payloads_rehashed=False,ordinary_file_readers_closed=True,archive_reader_opened=False,source_machine_executed=False,endpoint_difference_authorization=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
