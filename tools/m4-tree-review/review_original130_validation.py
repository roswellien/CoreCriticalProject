"""Independent bounded actual original130 export/source review; never opens archives."""
import collections, hashlib, json, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C
R=Path(__file__).resolve().parents[2]
def words(raw):return struct.unpack('<'+'I'*(len(raw)//4),raw)
def main(name):
 out=R/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh bounded review');out.mkdir(parents=True)
 passed=False;counts=collections.Counter();excluded=[]
 try:
  C.pin(__file__);C.pin(C.__file__)
  area=R/'reports/m4-startup130-original';vd=area/'validation-r2'
  v=C.read(vd/'report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca')
  e=C.read(area/'execution-r2/report.json','a22a14bc771d3ed237cee5a6b1cb65e8b0f32777787d93c7782a8abce5934c86')
  b=C.read(area/'build-r2/build.json','3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103')
  p=C.read(area/'preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
  pre=C.read(R/'reports/m4-tree-review/original130-prelaunch-r7/report.json','bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127')
  C.need(all(x['passed']for x in(v,e,b,p,pre))and v['build_sha256']==e['build_sha256']==pre['build_sha256']==C.PINS[str((area/'build-r2/build.json').resolve())]and v['preparation_sha256']==b['preparation_sha256']==pre['preparation_sha256'],'Exact final original130 executed/prelaunch chain')
  for q,h in v['files'].items():
   path=Path(q)
   if path.suffix.lower()in('.mwb','.zip'):excluded.append(dict(path=q,declared_sha256=h));continue
   C.pin(path,h)
  C.need(len(excluded)==1 and Path(excluded[0]['path']).suffix.lower()=='.mwb','Sole archived input explicitly retained without reader')
  C.need(v['original_executed']and not v['native_executed']and not v['state_seeded']and not v['per_phase_reseed']and not v['AFTER_machine_seed']and(v['record_bytes'],v['observed_pages'],v['external_whole_pages'],v['combined_pages'],v['callbacks'])==(356992,43,3,46,101),'Explicit immutable ABI and genuine original-only scope')
  family=C.pin(R/'tools/m4-startup130-original/family_phase_v2.py').read_text();prior=C.pin(R/'tools/m4-startup130-original/family_phase.py').read_text()
  C.need(family==prior.replace('mf[1]==len(filename)+3','mf[1]==len(filename)+4')and family.count('mf[1]==len(filename)+4')==1,'Only failed reviewer request formula corrected; genuine source allocates filename including NUL plus four suffix bytes')
  validate=C.pin(R/'tools/m4-startup130-original/validate_v2.py').read_text()
  C.need("from family_phase_v2 import"in validate and 'finally:records.close()'in validate and "format_cells={0x5bb5a8:"in validate and "before==after==target"in validate and "struct.pack('<101I'"in validate,'Final validator exact compiled entry-IAT, complete callback count and reader closure')
  roots=C.read(R/'reports/m4-formatting-frontier/recovery-r1/roots.json')+C.read(R/'reports/m4-mixed-format-original/recovery-r1/roots.json')
  rootmap={x['entry']:x for x in roots};cdecl=C.read(vd/'fresh-cdecl.json');owner=C.read(vd/'fresh-format_owners.json');mixed=C.read(vd/'fresh-mixed_owners.json')
  groups=collections.defaultdict(list)
  for row in cdecl:
   C.need(len(row['CPU'])==10 and len(bytes.fromhex(row['frame32_hex']))==32 and len(bytes.fromhex(row['FX512_hex']))==512 and len(bytes.fromhex(row['ENV28_hex']))==28 and not row['original_source_cleanup_after_RET_captured'],'Full actual cdecl record retained with original postRET scope excluded')
   groups[row['sequence'],row['phase'],row['root']].append(row);counts['whole_cdecl_records']+=1
  C.need(len(groups)==24 and len(cdecl)==144 and len(owner)==24 and len(mixed)==18,'Exact four-root/fresh six-sequence ownership extents')
  for (seq,phase,root),sides in groups.items():
   C.need([x['index']for x in sides]==list(range(6))and root in rootmap,'Current source root six ordered genuine entry/return observations')
   for i,(call,ret,nargs)in enumerate(((0x4dea15,0x4dea1b,2),(0x4deab1,0x4deab7,1),(0x4dead1,0x4dead7,4))):
    a,z=sides[2*i:2*i+2];ac,zc=a['CPU'],z['CPU'];af,zf=words(bytes.fromhex(a['frame32_hex'])),words(bytes.fromhex(z['frame32_hex']))
    C.need(a['header'][8]==z['header'][8]==call and af[0]==zc[9]==ret and ac[4]+4==zc[4]and af[1:nargs+1]==zf[:nargs]and all(ac[j]==zc[j]for j in(3,5,6,7)),'Independently retained complete cdecl frame/callee saved bytes')
    counts['whole_cdecl_frame_pairs']+=1
   ro=rootmap[root];filename=bytes.fromhex(sides[0]['strings'][0]['bytes_hex']);declared=bytes.fromhex(ro['filename_bytes_hex'])if'filename_bytes_hex'in ro else ro['filename_text'].encode()+b'\0'
   C.need(filename==declared and words(bytes.fromhex(sides[2]['frame32_hex']))[1]==len(filename)+4,'Exact physically reviewed source string/request correspondence')
   m=next(x for x in owner if(x['sequence'],x['phase'],x['root'])==(seq,phase,root));meta=m['meta'];initial=bytes.fromhex(m['initial_hex']);final=bytes.fromhex(m['final_hex']);expected=filename[:-1]+b'.zrd\0'
   C.need(meta[:4]==[1,m['index'],root,0x4deab1]and meta[4]==len(filename)+4 and meta[5]==sides[3]['CPU'][0]and meta[6]==len(initial)==len(final)and final==expected+initial[len(expected):]and sides[5]['CPU'][0]==len(expected)-1 and bytes.fromhex(sides[3]['owned_hex'])==initial and bytes.fromhex(sides[5]['owned_hex'])==final,'Complete actual native input capacity/tail and genuine sprintf result byteflow')
   counts['whole_format_capacity_byteflows']+=1
  for row in mixed:
   a=bytearray.fromhex(row['initial_hex']);z=bytes.fromhex(row['final_hex']);m=row['meta'];C.need(m[:3]==[1,row['index'],0x4e1ca0]and len(a)==len(z)==m[8],'Exact mixed occurrence/full capacity')
   for store in row['stores']:C.need(store['width']==4 and store['offset']+4<=m[4],'Source requested-bound store');struct.pack_into('<I',a,store['offset'],store['value']);counts['mixed_literal_owned_stores']+=1
   C.need(bytes(a)==z,'Whole actual mixed capacity from initial plus only literal stores');counts['whole_mixed_capacity_byteflows']+=1
  fs=C.read(vd/'fresh-mixed_FS.json')
  for row in fs:
   c,d=row['CPU_before'],row['CPU_after'];kind=row['header'][3]
   C.need(len(bytes.fromhex(row['record12_hex']))==12 and row['FX_before_hex']==row['FX_after_hex']and row['ENV_before_hex']==row['ENV_after_hex']and all(c[j]==d[j]for j in range(9)if not(kind==0 and j==0)),'Full normal mixed FS operation architectural conservation');counts['whole_mixed_FS_records']+=1
  cp=C.read(vd/'fresh-mixed_CP.json')
  for row in cp:C.need(len(row['CPU'])==10 and len(bytes.fromhex(row['frame32_hex']))==32 and len(bytes.fromhex(row['CS24_hex']))==24 and len(bytes.fromhex(row['FX512_hex']))==512 and len(bytes.fromhex(row['ENV28_hex']))==28 and len(row['pages_sha256'])==3,'Full bounded original mixed Lockit typed resource/frame fields');counts['whole_mixed_Lockit_records']+=1
  iats=C.read(vd/'format-IAT-relations.json');obs=C.read(R/'reports/m4-tree-review/original130-prelaunch-r7/compiled-observers.json');shims={x['symbol']:x['target']for x in obs if x['family']=='format'};targets={0x5bb5a8:shims['_format_entry_strrchr'],0x5bb664:shims['_format_entry_malloc'],0x5bb658:shims['_format_entry_sprintf']}
  C.need(len(iats)==2340 and len({(x['sequence'],x['phase'],x['cell'])for x in iats})==2340,'Every one of780 phases has three distinct owning import cells')
  for row in iats:C.need(row['actual_before']==row['actual_after']==row['declared_entry_target']==targets[row['cell']],'Every exported full DWORD equals exact uniquely compiled entry shim');counts['exact_IAT_endpoints']+=2
  crt=C.read(vd/'fresh-CRT_pages.json');C.need(len(crt)==1536,'64 whole current CRT pages at every four selected root/sequence')
  for row in crt:C.need(row['whole_bytes_retained']and row['type']==0x1000000 and len(row['BEFORE_sha256'])==len(row['AFTER_sha256'])==64,'Whole loaded image metadata/raw declared SHA endpoint');counts['current_CRT_page_endpoints']+=2
  cosine=C.read(vd/'fresh-cosine.json');C.need(len(cosine)==6,'Six finite hardware observations')
  for row in cosine:C.need(not row['host_cos_expected_used']and not row['AFTER_as_source_seed']and len(row['inputs'])==len(row['results'])==3 and len(bytes.fromhex(row['FX_before_hex']))==len(bytes.fromhex(row['FX_after_hex']))==512,'Retained whole hardware x87 inputs/endpoints no analytic prediction');counts['finite_F32_observations']+=3
  C.need(counts==collections.Counter(whole_cdecl_records=144,whole_cdecl_frame_pairs=72,whole_format_capacity_byteflows=24,mixed_literal_owned_stores=60,whole_mixed_capacity_byteflows=18,whole_mixed_FS_records=36,whole_mixed_Lockit_records=36,exact_IAT_endpoints=4680,current_CRT_page_endpoints=3072,finite_F32_observations=18),'Independent fixed export counts')
  counts['actual_original_phases']=v['counts']['phases'];counts['callback_roots']=v['callbacks'];passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent bounded final original130 producer source, physically pinned receipt lineage and full exported current capacity/cdecl/FS/Lockit/IAT relations; no archive reread or independent new execution',counts=dict(counts),validation_sha256='91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca',prelaunch_sha256='bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127',capture_archives_opened=0,retained_archived_inputs=excluded,compiled_observers_reused=True,original_postRET_capture_claim=False,native_credit=False,initializer_credit=0,files=C.PINS)
  target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counts=dict(counts),sha256=hashlib.sha256(target.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
