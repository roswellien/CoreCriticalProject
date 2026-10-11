"""Additive correction from actual index4 association evidence."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'tools/m4-lockit-source'
response=BASE/'responses_v3.py';assert not response.exists()
s=(BASE/'responses.py').read_text().replace("self.index==5 and w[:5]==(1,5,0,", "self.index==4 and w[:5]==(1,4,0,")
s+='\n# Preserve the explicit contract interface used by the capture adapter.\nB=PRIOR.B\nNEW_CONTRACTS=PRIOR.NEW_CONTRACTS\n'
response.write_text(s)
paths=[response,BASE/'bridge_v2.py',Path(__file__)]
for prior_name,target_name in (('compare_connected_v5.py','compare_connected_v6.py'),('compare_provider124_v5.py','compare_provider124_v6.py')):
 prior=BASE/prior_name;out=BASE/target_name;assert not out.exists();s=prior.read_text()
 s=s.replace('import responses_v2 as R','import responses_v3 as R\nimport bridge_v2 as B2')
 begin=s.index('     machine,responses=B.bootstrap(')
 end=s.index('     V.configure(machine,',begin)
 seam="""     resource=a.words(stem+'lockit-resource.bin',8,'Q');image_raw=a.data(stem+'lockit-native-images.bin');need(len(image_raw)==320,'Exactly eight genuine native CS40 images');images=[image_raw[n:n+40]for n in range(0,len(image_raw),40)]
     def resource_association(machine,responses):
      machine.snapshot('lockit-resource-association-before')
      for suffix in ('before','after'):
       if suffix=='after':responses.associate_lockit(machine,resource,images,loaded_RW[0x640:0x658]);machine.snapshot('lockit-resource-association-after')
       association=C.checkpoint(a,checkpoint_index,'lockit-resource-association-'+suffix);equal(bytes(machine.state),association['state'],'Explicit resource association preserves whole guest State');equal(B.cpu(machine.state),association['cpu'],'Explicit resource association preserves whole guest CPU');equal(machine.fx,association['fx'],'Explicit resource association preserves whole guest FX')
       for page in PAGES:
        if page in association['memory']:equal(machine.bytes(page,4096),association['memory'][page],'Explicit resource association preserves entire source page'+hex(page))
      counts['actual_native_CS_resource_associations']+=1
     machine,responses=B2.bootstrap(before,facts,heap,material,ObservedMachine,program,callbacks,oldpc,oldsp,resource_association=resource_association)
"""
 s=s[:begin]+seam+s[end:]
 s=s.replace("  passed=True", "  for file in ('responses_v3.py','bridge_v2.py'):pin(ROOT/'tools/m4-lockit-source'/file)\n  passed=True")
 out.write_text(s);paths.extend((prior,out))
receipt=ROOT/'reports/m4-lockit-source/association-preparation-r2';assert not receipt.exists();receipt.mkdir()
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
(receipt/'report.json').write_text(json.dumps(dict(passed=True,scope='Adapter preparation only: actual native lifecycle association index4 after four static locks and before producer HeapAlloc index5; unchanged inherited literal bootstrap plus explicit unchanged-guest resource seam; no new acceptance credit',native_executed=False,initializer_credit=False,actual_evidence='reports/m4-lockit-source/bootstrap-diagnostic-r1/report.json',association_index=4,resource_generation=5,producer_HeapAlloc_index=5,files=files),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((receipt/'report.json').read_bytes()).hexdigest())))
