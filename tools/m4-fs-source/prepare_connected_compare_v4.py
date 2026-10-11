"""Add complete original CALL/RET/saved-load PC metadata to FS source proof."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];t=(ROOT/'tools/m4-fs-source/compare_connected_v3.py').read_text()
a="before_head=prior,after_head=value if write else prior,entry_ESP=";assert t.count(a)==1;t=t.replace(a,"source_call_frame=list(model.call_stack[-1])if kind==0 else None,"+a)
a="need(f[15]==f[19]==f[21]==1 and f[17]==f[8]==f[22]and f[24:26]==(0x7ffde000,0xffffffff),'All normal frame installs/saved-load/restores/RET with explicit runtime sentinel');";assert t.count(a)==1
b=a+"call=event['source_call_frame'];spec={0x4e78d0:(0x4e78de,0x4e7997,0x4e799f,0x4e79aa),0x48f290:(0x48f29e,0x48f353,0x48f360,0x48f36b),0x4d48f0:(0x4d48fe,0x4d492a,0x4d4948,0x4d4953)}[event['group_entry']];need((f[4],f[5],f[6],f[23])==(call[3],call[1],call[2],call[0]),'Actual original source CALL site/frame/return and retained tail-entry metadata');need((f[14],f[16],f[18],f[20])==spec,'Exact actual source install/saved-load/restore/RET PCs');"
t=t.replace(a,b);p=ROOT/'tools/m4-fs-source/compare_connected_v4.py';assert not p.exists();p.write_text(t)
