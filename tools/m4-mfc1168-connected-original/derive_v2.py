"""Fix physical read-only IAT binding timing and full MFC image observation."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-mfc1168-connected-original';P=R/'reports/m4-mfc1168-connected-original/preparation-r2/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact source hunk '+a[:70])
 return s.replace(a,b,1)
if sha(P)!='addde3696b11b5ed366d3391804cb096ebd0998e5b1c3e70bb3547c9be9b77a1':raise ValueError('Parent receipt')
r=json.loads(P.read_bytes());p=T/'prepare.py';tail=T/'main_tail.inc'
for q in [p,tail]:
 if sha(q)!=r['files'][str(q)]:raise ValueError('Parent source')
s=p.read_text();t=tail.read_text()
a='    const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");require(reinterpret_cast<unsigned>(service)==0x5f401083&&reinterpret_cast<unsigned>(mbcp)==0x78003ddb,"Physical current1168 and setmbcp exports");require(dword(0x5bb210)==0x80000490,"Physical game ordinal1168 import");*reinterpret_cast<unsigned*>(0x5bb210)=reinterpret_cast<unsigned>(service);*reinterpret_cast<unsigned*>(0x5bb674)=reinterpret_cast<unsigned>(mbcp);\n'
t=one(t,a,'')
x=t.index('    // Writable reset includes the owning source IAT page;');y=t.index('    mixed_input=',x)
t=t[:x]+'    // The source IAT page is physically read-only and excluded from writable reset.\n'+t[y:]
t=t.replace('0xd0000);','0xed000);')
q=T/'main_tail_v2.inc'
if q.exists():raise ValueError('Fresh tail')
q.write_text(t)
needle=" start=re.sub(r'std::array<void\\*,132> pages',f'std::array<void*,{len(records)}> pages',start)\n"
insert=" start=one(start,'    for(unsigned i=0;i<pages.size();++i){\\n        protect',"+repr(a)+"+'    for(unsigned i=0;i<pages.size();++i){\\n        protect')\n"
s=one(s,needle,needle+insert)
s=one(s,"text(R/'tools/m4-mfc1168-connected-original/main_tail.inc')","text(R/'tools/m4-mfc1168-connected-original/main_tail_v2.inc')")
s=one(s,'whole_MFC_pages=[0x5f400000,0x5f4d0000]','whole_MFC_pages=[0x5f400000,0x5f4ed000]')
s=one(s,' for p in [Path(__file__),R/'," pin(T/'derive_v2.py')\n pin(T/'prepare.py')\n pin(T/'main_tail.inc')\n pin(P,'addde3696b11b5ed366d3391804cb096ebd0998e5b1c3e70bb3547c9be9b77a1')\n for p in [Path(__file__),R/")
s=one(s,"R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-connected-original'","R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-connected-original';T=R/'tools/m4-mfc1168-connected-original';P=B/'preparation-r2/report.json'")
q=T/'prepare_v2.py'
if q.exists():raise ValueError('Fresh preparation tool')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
