"""Join real serial CRT lock counts to API frames already proved by source r9."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_witnesses_v3.py';s=p.read_text()
a="   sections=rows(a,'actual-cleaned/locale-critical-sections.bin',16);need(len(sections)==5 and all(w[0]==1 and w[3:6]==(0,0,0)and w[6:10]==(1,1,1,1)and w[10]and w[11]==40 for w in sections),'All five actual native CS40 lifetimes initialized/deleted exactly once and never held')";assert s.count(a)==1
b="""   static=read(ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json');site_names={r['pc']:r['API']for r in static['API_sites']};enters=collections.Counter();leaves=collections.Counter()
   actual_summary=tuple(struct.unpack('<32I',a.data('actual-cleaned/locale-summary.bin')))
   for i in range(actual_summary[18]):
    w=a.words('actual-cleaned/locale-api-'+str(i)+'-witness.bin',32,'Q')
    if not w[31]and site_names.get(w[2])in('EnterCriticalSection','LeaveCriticalSection'):
     need(w[2]in {pc for row in sources if row['level']==level for pc in row['source_PCs']},'Actual serial lock API site was executed by literal selected source')
     (enters if site_names[w[2]]=='EnterCriticalSection'else leaves)[w[20]]+=1
   equal(enters,leaves,'All independently source-joined serial API pairs balance')
   sections=rows(a,'actual-cleaned/locale-critical-sections.bin',16);need(len(sections)==5 and all(w[0]==1 and w[3:6]==(enters[w[1]],leaves[w[1]],0)and w[6:10]==(1,1,1,1)and w[10]and w[11]==40 for w in sections),'All five actual native CS40 lifetimes match genuine source-joined enter/leave counts and one initialize/delete')"""
s=s.replace(a,b);target=R/'tools/m4-formatting-source/compare_native_witnesses_v4.py';assert not target.exists();target.write_text(s)
