"""Bounded ordinary source fixture controls, not capture equivalence."""
from pathlib import Path
import copy,hashlib,json,struct,sys,types
R=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(R/'tools/m4-native141-source'))
import constructor_fs_union141_v2 as F
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/FS-domain-controls-r1';assert not out.exists();out.mkdir()
 source=R/'reports/m4-startup141-source/combined-source-provider-r1/Constructor-carried-source-derivations.json';rows=json.loads(source.read_bytes());roots=tuple(v['root']for v in rows);data={};stem='sequence-0/'
 frames=[];records=[]
 for i in range(28):
  f=[0]*32;f[0]=1;f[2]=0x4ada90;frames.append(f)
  for point in(81,84):
   row=[0]*16;row[2]=i;row[3]=f[2];row[4]=point;records.append(row)
 data[stem+'fs-frame-witnesses.bin']=b''.join(struct.pack('<32Q',*v)for v in frames);data[stem+'fs-record-bytes.bin']=b''.join(struct.pack('<16Q',*v)for v in records)
 accesses=b'';fs=b''
 for v in rows:
  base=stem+'Constructors/root-'+str(v['root'])+'/'
  data[base+'before/accesses.bin']=accesses;accesses+=b''.join(struct.pack('<IIQII',*x)for x in v['component_source_accesses']);data[base+'after/accesses.bin']=accesses
  data[base+'before/FS-events.bin']=fs;fs+=b''.join(struct.pack('<12I',*x)for x in v['component_FS_rows']);data[base+'after/FS-events.bin']=fs;data[base+'after/FS-frames.bin']=b''
 obs=[e for v in rows for e in v['game_FS_observations']];checks=[]
 def run(d,events):
  owner=types.SimpleNamespace(constructor_FS_observations=events);returned=F.partition(types.SimpleNamespace(data=lambda k:d[k]),stem,owner,roots)
  return returned,owner.constructor_FS_partition
 result,proof=run(data,obs);assert result==([tuple(v)for v in frames],[tuple(v)for v in records]);checks.append('Unchanged normal28/56 returned; all7/21/14 constructor source scopes separately reconstructed')
 physical=json.loads((R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json').read_bytes());byentry={v['entry']:v for v in physical['frames']}
 for e in obs:
  p=byentry[e['group_entry']];assert p['handler']==e['handler']and p[('read','install','restore')[e['kind']]]==e['PC']
 assert [len([e for e in obs if e['root']==v['root']and e['kind']==0])for v in rows]==[3,3,1];checks.append('Every21 source event matches physical constructor FS declaration; dynamic frames3+3+1')
 def reject(label,mutate):
  d=copy.deepcopy(data);events=copy.deepcopy(obs);mutate(d,events)
  try:run(d,events)
  except ValueError:checks.append(label);return
  raise AssertionError('Missing rejection '+label)
 base=stem+'Constructors/root-'+str(roots[0])+'/'
 reject('Missing normal raw record',lambda d,e:d.__setitem__(stem+'fs-record-bytes.bin',d[stem+'fs-record-bytes.bin'][:-128]))
 def phantom(d,e):
  x=list(struct.unpack('<32Q',d[stem+'fs-frame-witnesses.bin'][:256]));x[2]=roots[0];d[stem+'fs-frame-witnesses.bin']=struct.pack('<32Q',*x)+d[stem+'fs-frame-witnesses.bin'][256:]
 reject('Constructor row falsely inserted into normal journal',phantom)
 reject('Missing constructor event',lambda d,e:e.pop())
 reject('Wrong source frame handler',lambda d,e:e[1].__setitem__('handler',e[1]['handler']^1))
 reject('Wrong whole source12B record',lambda d,e:e[1].__setitem__('record_hex','00'+e[1]['record_hex'][2:]))
 def wrongbyte(d,e):
  raw=bytearray(d[base+'after/accesses.bin']);index=next(i for i,v in enumerate(rows[0]['component_source_accesses'])if v[1]==e[1]['record_address']and v[4]==1);raw[index*24+8]^=1;d[base+'after/accesses.bin']=bytes(raw)
 reject('Changed pre-event actual committed record byte',wrongbyte)
 def wrongdepth(d,e):
  raw=bytearray(d[base+'after/FS-events.bin']);raw[48+24]^=1;d[base+'after/FS-events.bin']=bytes(raw)
 reject('Wrong actual component nesting depth',wrongdepth)
 reject('Nonempty returned constructor FS scopes',lambda d,e:d.__setitem__(base+'after/FS-frames.bin',b'x'))
 p=out/'constructor-record-joins.json';p.write_text(json.dumps(proof,indent=2)+'\n')
 files={str(p):sha(p),str(source):sha(source),str(Path(F.__file__).resolve()):sha(Path(F.__file__)),str(Path(__file__).resolve()):sha(Path(__file__))}
 physicalpath=R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json';files[str(physicalpath)]=sha(physicalpath)
 report=dict(passed=True,controls=len(checks),checks=checks,scope='Retained actual source-computed component fixture plus synthetic inherited normal scaffolding; genuine current native constructor journals were compared by failed full source run, current global native cardinality diagnostic remains ROOT-owned.',normal_fixture_is_synthetic=True,source_values_used_as_test_fixture_only=True,canonical_reader_opened=False,worker_executed=False,actual_native_equivalence_claim=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(out/'report.json'),sha256=sha(out/'report.json'),controls=len(checks))))
if __name__=='__main__':main()
