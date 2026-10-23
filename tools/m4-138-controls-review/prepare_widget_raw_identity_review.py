"""Add whole retained raw GDI identities and source/manual records."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-138-controls-review/review_source6_widgets_v4.py';original=p.read_text();text=original;changes=[]
def one(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
addition="""   try:
    for seq in range(6):
     current=next(c for c in cleanup if(c['level'],c['sequence'])==(level,seq));prefix=f'sequence-{seq}/Widget/';manual=[];names=set()
     for generation in current['font_generations']:
      stem=prefix+'manual-font-cleanup/'+str(generation);manual.append((facade.data(stem+'-row.bin'),facade.data(stem+'-hardware.bin')));names.update((stem+'-row.bin',stem+'-hardware.bin'))
     need({name for name in facade.entries if name.startswith(prefix+'manual-font-cleanup/')}==names,'All and only15 complete actual owned font cleanup observations')
     source_records=facade.data(prefix+'root-'+str(ROOTS[-1])+'/after/APIs.bin')
     raw=G.verify(facade.data,pin,prefix=prefix,source_records=source_records,manual_records=manual,logical_names=facade.entries,expected_thread=current['physical_GDI']['host_thread'])
     need(json.loads(json.dumps(raw,sort_keys=True))==current['physical_GDI'],'Whole independently repeated raw physical identity/named export/source/manual proof correspondence')
     parsed=G.parse_source_records(source_records)
     for rootrow in rows:
      if(rootrow['level'],rootrow['sequence'])!=(level,seq):continue
      for response in rootrow['GDI_source']['API_response_derivations']:
       serial=response['serial'];record=source_records[serial*1488:(serial+1)*1488];argc=14 if response['service']=='CreateFontA'else 1
       need(hashlib.sha256(record).hexdigest()==response['API_record_sha256']and parsed[serial]['record_sha256']==response['API_record_sha256'],'Whole actual API1488 digest joins source response')
       need(list(struct.unpack_from('<14I',record,208)[:argc])==response['source_arguments'],'Every typed actual source argument DWORD joins source computation')
     counts['independently_authenticated_raw_GDI_calls']+=164;counts['independent_complete_raw_GDI_cases']+=1
    for row in rows:
""";
one("   try:\n    for row in rows:\n",addition)
one("independent_raw_identity_equality=False", "independent_raw_identity_equality=passed")
inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==original;ast.parse(text);q=R/'tools/m4-138-controls-review/review_source6_widgets_v5.py';assert not q.exists();q.write_text(text)
out=R/'reports/m4-138-controls-review/source6-widget-raw-identity-preparation-r1';assert not out.exists();out.mkdir(parents=True)
paths=(p,q,Path(__file__),R/'reports/m4-138-controls-review/source6-widget-complete-memory-preparation-r1/report.json',R/'tools/m4-widget-growth-review/gdi_identity.py')
r=dict(passed=True,scope='Unexecuted additive full raw GDI1968calls/identity/named entry64 records + actual API1488/arguments/manual hardware correspondence via current unchanged sealed ordinary Facade. Full84 own memory byteflow retained; no archive/native/source machine execution.',changes=changes,inverse_restores_entire_parent=True,files={str(p.resolve()):sha(p)for p in paths},reviewer_executed=False,capture_archives_opened=0,full_source_widget_acceptance_closed=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),tool_sha256=sha(q))))
