from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
base=T/'prepare.py';target=T/'prepare_v2.py'
assert not target.exists()
s=base.read_text()
old="  found=re.findall(r'\\{(0x[0-9a-f]+),(\\d+),',m[1]);need(found,'Concrete patch rows '+field)\n  inherited.extend(dict(PC=int(pc,16),size=int(n),family=field)for pc,n in found)"
new="  if field=='null_hooks':\n   found=[(pc,'5')for pc in re.findall(r'\\{(0x[0-9a-f]+),&nullfree_',m[1])]\n   need(len(found)==2,'Exact two fixed-five-byte NULL-free hooks')\n  else:found=re.findall(r'\\{(0x[0-9a-f]+),(\\d+),',m[1])\n  need(found,'Concrete patch rows '+field)\n  inherited.extend(dict(PC=int(pc,16),size=int(n),family=field)for pc,n in found)"
assert s.count(old)==1
target.write_text(s.replace(old,new))
failed=R/'reports/m4-startup131-original/preparation-r1/generation-failure.json'
assert not failed.exists()
failed.write_text(json.dumps(dict(passed=False,stage='additive source-family metadata extraction after worker preparation',reason='NULL-free actual rows use fixed raw[5] rather than an explicit size field; generic metadata regex rejected them',generator=str(base),generator_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),worker_executed=False,capture_reader_opened=False,preserved=True),indent=2)+'\n')
print(target)
