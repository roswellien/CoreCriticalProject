"""Extend pre-CRT reservations from physical sparse inventory; retain failed worker."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r8/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=T/'prepare_v7.py';d=json.loads(P.read_bytes())
if sha(P)!='feda3945939789097f4327d14b9e45230abf9d108c7ef202975301871d04dbca'or sha(p)!=d['files'][str(p)]:raise ValueError('Immutable source')
s=p.read_text();a=' for p in out.iterdir():pin(p)'
b=''' # Every expanded sparse page requires a pre-CRT64KiB reservation.
 bp=out/'original_broker.hpp';broker=bp.read_text();m=re.search(r'inline constexpr std::array<std::uint32_t,(\\d+)> bases\\{([^}]+)\\};',broker)
 need(m is not None,'Exact inherited reservation inventory');reserved=[int(v,16)for v in m[2].split(',')];need(len(reserved)==int(m[1]),'Exact declared reservation count')
 additions=sorted({p&~65535 for p in records}-set(reserved));need(additions==[0x5d0000],'One physical newly needed base');reserved+=additions
 broker=broker[:m.start()]+f'inline constexpr std::array<std::uint32_t,{len(reserved)}> bases'+ '{'+','.join(hex(v)for v in reserved)+'};'+broker[m.end():];bp.write_text(broker)
 need(all(p&~65535 in reserved for p in records),'Every actual sparse page reserved before CRT')
 rp=out/'reference.cpp';reference=rp.read_text();a='        require(pages[i]==reinterpret_cast<void*>(page_bases[i]),"Exact page commit failed");'
 b='        if(pages[i]!=reinterpret_cast<void*>(page_bases[i]))std::cerr<<"Source page commit address="<<std::hex<<page_bases[i]<<" Win32="<<GetLastError()<<std::dec<<"\\\\n";'+a
 reference=one(reference,a,b);rp.write_text(reference)
 for p in out.iterdir():pin(p)'''
if s.count(a)!=1:raise ValueError('Exact generated reservation stage')
s=s.replace(a,b,1);a=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v7.py');";b=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v8.py');pin(R/'tools/m4-widget-original/prepare_v7.py');pin(R/'reports/m4-widget-original/preparation-r8/report.json','feda3945939789097f4327d14b9e45230abf9d108c7ef202975301871d04dbca');pin(R/'tools/m4-widget-original/derive_prepare_v7.py');"
if s.count(a)!=1:raise ValueError('Exact lineage')
s=s.replace(a,b,1);q=T/'prepare_v8.py'
if q.exists():raise ValueError('Fresh source')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
