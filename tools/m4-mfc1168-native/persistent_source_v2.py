"""Same literal142 source, additionally deny undefined architectural consumers."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/m4-mfc1168-native/persistent_source.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='85154776a5e78f9bd8c38dca55f7b08206b54401f601847e5c9e83f54f360c17'
text=source.read_text();assert text.count('domain={};flags=[]')==1;text=text.replace('domain={};flags=[]','domain={};flags=[];consumers=[]')
old="domain=F.advance(m,r,domain);m.step();flags.append(dict(PC=r['pc'],undefined_flags=dict(domain)))"
new="consumer=FC.check(m,r,domain);consumers.extend([consumer]if consumer else []);domain=FC.advance(m,r,domain);m.step();flags.append(dict(PC=r['pc'],undefined_flags=dict(domain)))"
assert text.count(old)==1;text=text.replace(old,new)
assert text.count('flag_lifetimes=flags,source_AFTER_seed=False')==1;text=text.replace('flag_lifetimes=flags,source_AFTER_seed=False','flag_lifetimes=flags,defined_flag_consumers=consumers,final_undefined_flags=domain,source_AFTER_seed=False')
assert text.count('index+=1;domain={}')==1;text=text.replace('index+=1;domain={}','index+=1')
sys.path.insert(0,str(ROOT/'tools/m4-formatting-source'));sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'))
import flag_consumers as FC
exec(compile(text,str(source),'exec'),globals())
