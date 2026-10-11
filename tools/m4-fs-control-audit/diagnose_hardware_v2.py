"""Authenticate actual failed outside-return samples; no weakened assertions."""
import json,hashlib,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import verify_manifest
def need(x,message):
 if not x:raise ValueError(message)
def main(directory):
 out=Path(directory).resolve();need(out.parent==R/'reports/m4-fs-control-audit' and not out.exists(),'Fresh diagnosis');out.mkdir();files={}
 def pin(path,expected=None):
  path=Path(path).resolve();digest=sha_file(path);need(expected is None or digest==expected,'Frozen actual identity');files[str(path)]=digest;return path
 run=pin(R/'reports/m4-fs-controls/execution-r1/report.json','186c9e37e2ad9eeea5bece4190e8c3962a4f9792b03cf162fde05d3eaf1d5b81');value=json.loads(run.read_bytes());need(not value['passed'],'Failed real controls remain failed');levels={}
 for row in [dict(row,attempt=attempt) for row in value['levels'] for attempt in ('first','retry')]:
  manifest=pin(row['capture'],row['capture_sha256']);meta=json.loads(manifest.read_bytes());need(len(meta['parts'])==1,'Finite failed control part');part=meta['parts'][0];path=pin(manifest.parent/part['bundle'],part['sha256'])
  with CaptureBundle(path,part['sha256'])as owner:
   header=struct.unpack('<6I',owner.read_bytes('header.bin'));sample=owner.read_bytes('case-0/'+row['attempt']+'.bin');need(header==(1,24,48,9968,6,10) and len(sample)==9968,'Exact authored sample ABI')
   tags=struct.unpack_from('<32Q',sample);b=sample[8880:9424];a=sample[9424:9968];different=lambda l,r:[[i,x,y]for i,(x,y)in enumerate(zip(l,r))if x!=y]
   supported=[]
   for lo,hi,name in [(0,5,'CW/SW/FTW'),(24,28,'MXCSR'),(256,416,'XMM6..15')]:
    delta=different(b[lo:hi],a[lo:hi]);supported.append({'field':name,'before':b[lo:hi].hex(),'after':a[lo:hi].hex(),'differences':delta})
   for k in range(8):
    lo=32+16*k;hi=lo+10;delta=different(b[lo:hi],a[lo:hi]);supported.append({'field':'raw80-'+str(k),'before':b[lo:hi].hex(),'after':a[lo:hi].hex(),'differences':delta})
   supported.append({'field':'legacyENV28','before':b[512:540].hex(),'after':a[512:540].hex(),'differences':different(b[512:540],a[512:540])})
   cleaned_before=owner.read_bytes('case-0/'+row['attempt']+'-cleanup-hardware-before.bin');cleaned_after=owner.read_bytes('case-0/'+row['attempt']+'-cleanup-hardware-after.bin');env=owner.read_bytes('case-0/'+row['attempt']+'-causal-guest-ENV.bin')
   for name,data in [('outside-before.bin',b),('outside-after.bin',a),('cleanup-before.bin',cleaned_before),('cleanup-after.bin',cleaned_after)]:dest=out/(row['level']+'-'+row['attempt']+'-'+name);dest.write_bytes(data);pin(dest)
   levels[row['level']+'-'+row['attempt']]={'attempt':row['attempt'],'tags':tags,'source_completed_six':tags[3]==1 and tags[4]==6,'first_retained_failure':owner.read_bytes('FAILURE.txt').decode(),'supported_fields':supported,'cleanup_supported_differences':different(cleaned_before[:5],cleaned_after[:5])+different(cleaned_before[24:28],cleaned_after[24:28])+different(cleaned_before[512:540],cleaned_after[512:540]),'causal_guest_ENV':env.hex(),'only_failed_fields':[x['field']for x in supported if x['differences']]}
 pin(__file__);pin(R/'reports/m4-fs-controls/build-r3/fixture.cpp');pin(R/'reports/m4-fs-controls/build-r3/capture.s');pin(R/'tools/m4-pipeline/capture_bundle.py')
 report={'passed':True,'candidate_passed':False,'initializer_credit':0,'scope':'Complete failed case0 diagnosis: ordinary six-root return is exact, but naked same-finished-Session replay plus caller C++ catch loses actual legacy ENV metadata. This is a fixture/wrapper refusal-boundary issue; no production or initializer acceptance. Later authored outer wrapper may preserve whole attempt explicitly; no retroactive callee-only exception claim.','levels':levels,'files':files,'current_physical_closure':verify_manifest(files)}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'failed_fields':{k:v['only_failed_fields']for k,v in levels.items()}}))
if __name__=='__main__':main(*sys.argv[1:])
