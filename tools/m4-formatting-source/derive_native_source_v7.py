"""Join the inherited literal heap-prefix checkpoints as well as game checkpoints."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v6.py';s=p.read_text()
a="   need(set(index)-set(seen)=={'registry-bootstrap-before'},'Every captured provider checkpoint predicted from bootstrap BEFORE')";assert s.count(a)==1
b="""   for name,phase in machine.bootstrap_prefix['phases'].items():
    if name in index and name not in seen:
     actual=C.checkpoint(reader,index,name);equal(phase['state'],actual['state'],'Whole literal heap-prefix checkpoint State '+name);equal(phase['cpu'],actual['cpu'],'Whole literal heap-prefix checkpoint CPU '+name);equal(phase['fx'],actual['fx'],'Whole literal heap-prefix checkpoint FX '+name)
     for page,raw in actual['memory'].items():
      matches=[(p,b)for p,b in phase['memory'].items()if p<=page and page+len(raw)<=p+len(b)];need(len(matches)==1,'One original heap-prefix BEFORE-backed memory interval');p,b=matches[0];equal(bytes(b[page-p:page-p+len(raw)]),raw,'Whole literal heap-prefix checkpoint page '+name+' '+hex(page))
     seen.append(name);counts['whole_heap_prefix_checkpoints']+=1
   need(set(index)-set(seen)=={'registry-bootstrap-before'},'Every captured provider checkpoint predicted from bootstrap BEFORE '+str(sorted(set(index)-set(seen))))"""
s=s.replace(a,b);target=R/'tools/m4-formatting-source/compare_native_fixture_v7.py';assert not target.exists();target.write_text(s)
