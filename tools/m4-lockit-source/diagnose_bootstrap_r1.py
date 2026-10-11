"""Bounded diagnostic only: inspect pinned entry bytes, without acceptance credit."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_responses_v2 as R
base=ROOT/'reports/m4-joint-startup124-root/execution-r2/O0'
transport=json.loads((base/'transport.json').read_bytes())
wanted={f'sequence-0/cleaned/locale-api-{n}-witness.bin'for n in range(6)}
found={}
for part in transport['parts']:
 with (base/part['bundle']).open('rb')as f:
  magic,n,digest=struct.unpack('<8sQ32s',f.read(48));assert magic==b'MW34CAP1'
  raw=f.read(n);assert hashlib.sha256(raw).digest()==digest
  index=json.loads(raw)
  for entry in index['files']:
   if entry['path']not in wanted:continue
   f.seek(48+n+entry['offset']);value=f.read(entry['size']);assert hashlib.sha256(value).hexdigest()==entry['sha256']
   found[entry['path']]=list(struct.unpack('<32Q',value))
 if len(found)==len(wanted):break
assert len(found)==len(wanted)
contracts=R.B.contracts();contracts.update(R.NEW_CONTRACTS)
rows=[dict(logical=k,words=v,contract=contracts.get(v[2]))for k,v in sorted(found.items())]
out=ROOT/'reports/m4-lockit-source/bootstrap-diagnostic-r1';assert not out.exists();out.mkdir()
(out/'report.json').write_text(json.dumps(dict(scope='Small index/entry diagnostic only; no whole archive validation, no source/native acceptance credit',rows=rows),indent=2)+'\n')
print(json.dumps(rows,indent=2))
