"""Generate parallel-capable versioned copies with exact, checked deltas."""
from pathlib import Path
R=Path(r'D:\Projects\MW34Recomp')
def patch(src,dst,deltas,doc_old,doc_new):
    b=(R/src).read_bytes();crlf=b.count(b'\r\n')==b.count(b'\n')and b'\r\n'in b
    s=b.decode().replace('\r\n','\n')
    assert s.count(doc_old)==1,(src,'doc');s=s.replace(doc_old,doc_new)
    for a,c in deltas:assert s.count(a)==1,(src,a[:70],s.count(a));s=s.replace(a,c)
    inv=s.replace(doc_new,doc_old)
    for a,c in reversed(deltas):assert inv.count(c)==1,(src,'inverse',c[:60]);inv=inv.replace(c,a)
    assert (inv.replace('\n','\r\n')if crlf else inv).encode()==b,('exact inverse',src)
    out=R/dst;assert not out.exists(),dst;out.write_bytes((s.replace('\n','\r\n')if crlf else s).encode())
    import ast;ast.parse(s);print('wrote',dst)

# 1. Composite expander v4: optional ordered mapper for the per-row measurement loop.
patch('tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py','tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py',[
 ("def validate(connection,physical_rows,raw_rows,current_counts,legacy_counts,measure,register,register_edge,progress=None):",
  "def validate(connection,physical_rows,raw_rows,current_counts,legacy_counts,measure,register,register_edge,progress=None,mapper=None):"),
 (" count=0;size_total=0\n for path,folded,h,size,seen in connection.execute('SELECT path,folded,sha,size,seen FROM physical ORDER BY path'):\n"
  "  need(type(path)is str and str(Path(path).resolve())==path and Path(path).is_absolute()and folded==path.casefold(),'Canonical exact folded physical identity')\n"
  "  need(Path(path).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.7z')and Path(path).name!='transport.json','Ordinary physical union only')\n"
  "  need(type(h)is str and HEX.fullmatch(h)and type(size)is int and size>=0 and type(seen)is int and seen==1,'Every sealed row typed and seen')\n"
  "  measure(path,h,size);register(path,h);count+=1;size_total+=size\n",
  " count=0;size_total=0\n def check(row):\n  path,folded,h,size,seen=row\n"
  "  need(type(path)is str and str(Path(path).resolve())==path and Path(path).is_absolute()and folded==path.casefold(),'Canonical exact folded physical identity')\n"
  "  need(Path(path).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.7z')and Path(path).name!='transport.json','Ordinary physical union only')\n"
  "  need(type(h)is str and HEX.fullmatch(h)and type(size)is int and size>=0 and type(seen)is int and seen==1,'Every sealed row typed and seen')\n"
  " def serial(work,rows,prepare):\n  for row in rows:prepare(row);yield row,work(row)\n"
  " for(path,folded,h,size,seen),_ in(mapper or serial)(lambda row:measure(row[0],row[2],row[3]),connection.execute('SELECT path,folded,sha,size,seen FROM physical ORDER BY path'),prepare=check):\n"
  "  register(path,h);count+=1;size_total+=size\n"),
 ("def expand(report_path,expected_sha,register,*,register_edge,progress=None):","def expand(report_path,expected_sha,register,*,register_edge,progress=None,mapper=None):"),
 ("  result=validate(connection,p['physical_rows'],d['counts']['whole_export_targets_authenticated'],cc,lc,measured,register,register_edge,progress)",
  "  result=validate(connection,p['physical_rows'],d['counts']['whole_export_targets_authenticated'],cc,lc,measured,register,register_edge,progress,mapper)"),
],'"""Distinct closed builder7 union expansion: actual bytes and scoped edges."""\n',
 '"""Distinct closed builder7 union expansion: actual bytes and scoped edges (v4).\n\n'
 'v4 adds only an optional ordered ``mapper`` (tools/m4-parallel-measure/ordered_pool)\n'
 'for the per-row whole-byte measurement loop. Row checks still run before a file\n'
 'is opened, in order; registration and counters stay in the calling thread.\n"""\n')

# 2. Raw16 proof expander v2: same pattern for its per-row loop.
patch('tools/m4-138-controls-review/expand_proof_inventory.py','tools/m4-138-controls-review/expand_proof_inventory_v2.py',[
 ("def expand(report_path,expected_sha,register,progress=None):","def expand(report_path,expected_sha,register,progress=None,mapper=None):"),
 ("  previous=None\n  for k,path,h,rawcase,n,size,mtime,ctime,seen in connection.execute('SELECT k,path,sha,rawcase,bytes,size,mtime,ctime,seen FROM physical ORDER BY k'):\n"
  "   need(isinstance(k,str)and(previous is None or previous<k),'Unique ordered physical identity');previous=k\n",
  "  previous=[None]\n  def check(row):\n   k,path,h,rawcase,n,size,mtime,ctime,seen=row\n"
  "   need(isinstance(k,str)and(previous[0] is None or previous[0]<k),'Unique ordered physical identity');previous[0]=k\n"),
 ("   if rawcase is not None:need(type(rawcase)is int and 0<=rawcase<16 and n==size,'Exact rawcase/length');cases[rawcase]+=1\n"
  "   else:need(n is None,'Nonraw dependency schema')\n"
  "   measured(target,h,size);register(path,h);count+=1\n",
  "   if rawcase is not None:need(type(rawcase)is int and 0<=rawcase<16 and n==size,'Exact rawcase/length')\n"
  "   else:need(n is None,'Nonraw dependency schema')\n"
  "  def serial(work,rows,prepare):\n   for row in rows:prepare(row);yield row,work(row)\n"
  "  for(k,path,h,rawcase,n,size,mtime,ctime,seen),_ in(mapper or serial)(lambda row:measured(Path(row[1]),row[2],row[5]),connection.execute('SELECT k,path,sha,rawcase,bytes,size,mtime,ctime,seen FROM physical ORDER BY k'),prepare=check):\n"
  "   if rawcase is not None:cases[rawcase]+=1\n"
  "   register(path,h);count+=1\n"),
],'"""Stream sealed controls proof rows into a fresh acceptance dependency union.\n',
 '"""Stream sealed controls proof rows into a fresh acceptance dependency union (v2).\n\n'
 'v2 adds only an optional ordered ``mapper`` for the per-row measurement loop; row\n'
 'checks run before each file is opened, registration stays in the calling thread.\n')
