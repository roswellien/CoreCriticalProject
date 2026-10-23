"""Bounded O0/seq0 ordinary scalar diagnosis; no archive/model/new State."""
from pathlib import Path
import hashlib,json,re,struct
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-142-component-review/checkpoint-label-failure-r1'
assert not O.exists();O.mkdir();pins={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json';h=sha(source);assert h=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3';pins[str(source)]=h
S=json.loads(source.read_text());row=next(x for x in S['paired_exports']if x['branch']=='O0');p=Path(row['index_path']);assert sha(p)==row['index_sha256'];pins[str(p)]=row['index_sha256'];entries={}
with p.open()as f:
 for line in f:
  m=re.fullmatch(r'    "(sequence-0/(?:selected/registry-checkpoint-\d+-(?:name|cpu|runtime-cpu|state|fx)\.bin|phase-(?:81|82)\.bin))": \{\n',line)
  if m:
   lines=[next(f)for _ in range(4)];entries[m[1]]=json.loads('{'+''.join(lines[:3])+'}')
facts=[];reads={}
with Path(row['payload_path']).open('rb')as payload:
 def raw(k):
  e=entries[k];assert e['bytes']<=159716;payload.seek(e['offset']);b=payload.read(e['bytes']);assert len(b)==e['bytes']and hashlib.sha256(b).hexdigest()==e['sha256'];reads[k]=e;return b
 for k in entries:
  if k.endswith('-name.bin'):
   name=raw(k).decode();prefix=k[:-9]
   if not name.startswith('registry-root-'):continue
   cpu=list(struct.unpack('<10I',raw(prefix+'-cpu.bin')))
   if cpu[9]==0x4b5220 or name.startswith(('registry-root-61-','registry-root-64-')):
    facts.append(dict(label=name,prefix=prefix,CPU=cpu,runtime_CPU=list(struct.unpack('<10I',raw(prefix+'-runtime-cpu.bin'))),State_bytes=len(raw(prefix+'-state.bin')),FX_bytes=len(raw(prefix+'-fx.bin'))))
 for phase in(81,82):
  b=raw(f'sequence-0/phase-{phase}.bin');facts.append(dict(phase=phase,CPU_before=list(struct.unpack_from('<10I',b,36)),CPU_after=list(struct.unpack_from('<10I',b,76)),raw_IAT5BB5B0=struct.unpack_from('<I',b,2276+11*4096+0x5b0)[0]))
pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
q=O/'report.json';q.write_text(json.dumps(dict(passed=True,selector_predicate_failed=True,scope='Bounded actual O0seq0 ordinary scalar diagnostic, retained source6 + exactindexSHA + individual raw byteSHA; wholepayload rehash delegated previous ROOT selection receipt, not repeated',facts=facts,actual_raw_reads=reads,payload_whole_rehashed=False,canonical_reader_opened=False,source_executed=False,State_created=False,acceptance_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),facts=facts)))
