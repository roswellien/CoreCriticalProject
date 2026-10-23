from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-141-consumer-review/root_admit_source_v1.py';s=p.read_text()
for old,new in [('root-source-admission-r1','root-source-admission-r2'),('preparation-r4','preparation-r5'),('2a95f9bcbf1374bd6594685ffa690d995582c00cb1e58fd6c45da0d4dfcd5d58','30cf99256ebbc7584f6e1b15b73d15e76ac029809dda675d89749916b7dae9c9')]:
 assert old in s;s=s.replace(old,new)
anchor="  # Re-execute inspected failure controls"
added="""  receipt('reports/m4-141-consumer-review/FS-domain-preparation-r1/report.json','2683770625edcbf5f8c4af497bf51510013c93b2c983a4cab392c8ed2f4aadb6')
  receipt('reports/m4-141-consumer-review/FS-domain-controls-r1/report.json','92091445b9ca694179e9cfaaed47f27c6c9daafe43d0f1d399c7abad2692790b')
  diagnostic=R/'reports/m4-141-consumer-review/root-FS-diagnostic-r2/report.json'
  raw=json.loads(pin(diagnostic,'a5a5319dba8c8b7c107e50afd876a3567e5111c64c3780dacaa749d895ba7f2d').read_bytes())
  assert raw['passed']and raw['reader_closed']and raw['actual_global_frames']==28 and raw['actual_global_records']==56 and raw['constructor_frames_in_global_journal']==0
  for value in raw['logical_outputs'].values():pin(value['file'],value['sha256'])
  edits=json.loads(pin(R/'reports/m4-141-consumer-review/FS-domain-preparation-r1/observer-deltas.json').read_bytes())
  observer=pin(prep['observer']).read_text()
  for row in reversed(edits):
   assert observer.count(row['new'])==row['count'];observer=observer.replace(row['new'],row['old'])
  assert observer==pin(R/'tools/m4-native141-source/final_observer141_v7.py').read_text()
  checks.append('Actual normal28/56 and source-derived constructor7/21/14 separate journals; entire observer7 body retained')
"""
assert s.count(anchor)==1;s=s.replace(anchor,added+anchor)
start=s.index("  source=pin(R/'tools/m4-141-consumer-review/closure_controls_v2.py')")
end=s.index('  for p,h in tuple(pins.items()):',start)
s=s[:start]+"""  source=pin(R/'tools/m4-141-consumer-review/FS_domain_controls_v1.py')
  old="out=R/'reports/m4-141-consumer-review/FS-domain-controls-r1'"
  new="out=R/'reports/m4-141-consumer-review/root-FS-domain-controls-r1'"
  code=source.read_text();assert code.count(old)==1
  derivative=out/'FS-controls.py';derivative.write_text(code.replace(old,new));pin(derivative)
  ns={'__name__':'root_FS_controls','__file__':str(source)}
  exec(compile(derivative.read_text(),str(derivative),'exec'),ns);ns['main']()
  controls=receipt('reports/m4-141-consumer-review/root-FS-domain-controls-r1/report.json')
  assert controls['controls']==10
  checks.append('Fresh10 controls reject wrong record bytes/handler/depth, missing events, fake normal rows and unreturned scopes')
"""+s[end:]
q=p.with_name('root_admit_source_v2.py');assert not q.exists();q.write_text(s)
