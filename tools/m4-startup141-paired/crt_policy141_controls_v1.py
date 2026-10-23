"""Adverse controls for the current141 CRT policy evaluation (one real domain).

Uses actual O0 sequence0 inputs and requires crt_page_policy141_v1 to REFUSE:
inherited restore phase 13, inherited lock13 [108,108], a dropped import cell,
a flipped unused CRT data byte, shifted registry metadata, a native lock25
change, and a shim left installed at phase 15. Also confirms the unmodified
domain is admitted at those same endpoints. No credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
IAT,DATA=0x7802e000,0x78037000
TYPED=set(range(0x8c,0x90))|set(range(0x130,0x148))|set(range(0x888,0x890))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins.setdefault(str(p),v);return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(__file__);D=load('ordinary_entries',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');P=load('policy141',R/'tools/m4-startup141-paired/crt_page_policy141_v1.py')
 E=json.loads(pin(R/'reports/m4-startup141-paired/crt-policy141-eval-r1/report.json').read_bytes());assert E['passed']is True
 C=json.loads(pin(R/'reports/m4-original141-source/configuration-preparation-r3/configuration.json','451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0').read_bytes());V=json.loads(pin(C['validation']['path'],C['validation']['sha256']).read_bytes())
 patches=[p for p in json.loads(pin(C['current_transition_patches']['path'],C['current_transition_patches']['sha256']).read_bytes())if IAT<=p['pc']<IAT+4096]
 I=json.loads(pin(R/'reports/m4-startup141-paired/import-cells141-r1/report.json').read_bytes());cells=json.loads(pin(I['output']['path'],I['output']['sha256']).read_bytes())['cells']
 rows=[dict(offset=c['offset'],library=c['library'],name=c['name'],native_raw_thunk=c['native_raw_thunk'],original_real_target=c['original_real_target'],original_installed_target=c['observer_shim_target']if c['observer_shim_target']is not None else c['original_real_target'],observer_shim=c['observer_shim_target']is not None,physical_export_chain=c['physical_export_chain'])for c in cells]
 G=json.loads(pin(R/'reports/m4-startup141-paired/registry-output141-r1/report.json').read_bytes());reg={(r['sequence'],r['phase']):r for r in json.loads(pin(G['output']['path'],G['output']['sha256']).read_bytes())}
 N=json.loads(pin(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json').read_bytes())
 orow=next(e for e in V['paired_exports']if e['branch']=='original');oes=D.entries(pin(orow['index_path'],orow['index_sha256']),re.compile(r'phase/0/(?:0|15|47)/CRT-(?:before|after)/(?:2013454336|2013491200)\.bin'))
 nrow=next(e for e in N['paired_exports']if e['branch']=='O0');nes=D.entries(pin(nrow['index_path'],nrow['index_sha256']),re.compile(r'sequence-0/(?:phase-(?:0|15|47)-(?:before|after)-page-(?:2013454336|2013491200)|phase-(?:14|15|46|47)-after-registry|selected/locale-critical-sections)\.bin'))
 def rd(path,es,k):
  z=es[k]
  with Path(path).open('rb')as f:f.seek(z['offset']);b=f.read(z['bytes'])
  assert hashlib.sha256(b).hexdigest()==z['sha256'];return b
 o=lambda k:rd(orow['payload_path'],oes,k);n=lambda k:rd(nrow['payload_path'],nes,k)
 ao={IAT:o(f'phase/0/0/CRT-before/{IAT}.bin'),DATA:o(f'phase/0/0/CRT-before/{DATA}.bin')};bo={IAT:n(f'sequence-0/phase-0-before-page-{IAT}.bin'),DATA:n(f'sequence-0/phase-0-before-page-{DATA}.bin')}
 unused=sorted({i for i in range(4096)if ao[DATA][i]!=bo[DATA][i]}-TYPED);sec=next(v for v in struct.iter_unpack('<16Q',n('sequence-0/selected/locale-critical-sections.bin'))if v[1]==0x78037130)
 lock13=lambda c:[dict(offset=0x130,size=24,role='initialized_lock13_opaque_API_resource',guest_address=0x78037130,original_initial_hex=ao[DATA][0x130:0x148].hex(),native_initial_hex=bo[DATA][0x130:0x148].hex(),native_resource_extent=sec[11],native_resource_pointer=sec[10],original_enter_leave=c,native_enter_leave=list(sec[3:5]),native_initializations=sec[6],opaque_API_internals_equivalent=False)]
 loader=[dict(offset=0x8c,role='initialized_lock25',original_target=struct.unpack_from('<I',ao[DATA],0x8c)[0],native_target=struct.unpack_from('<I',bo[DATA],0x8c)[0])]
 def build(restore=15,counts=[111,111],r=rows,ld=loader):return P.Policy(ao,bo,patches,unused,r,ld,lock13(counts),restore,counts)
 def nmeta(ph):q=struct.unpack('<32Q',n(f'sequence-0/phase-{ph}-after-registry.bin'));return[q[6],q[7]]
 def check(policy,ph,side,page,a=None,b=None,om=None,nm=None):
  a=a or o(f'phase/0/{ph}/CRT-{side}/{page}.bin');b=b or n(f'sequence-0/phase-{ph}-{side}-page-{page}.bin')
  om=om or reg[(0,ph)]['source_before_metadata'if side=='before'else'source_computed_after_metadata'];nm=nm or(nmeta(ph-1)if side=='before'else nmeta(ph))
  policy.page(ph,side,page,a,b,om,nm)
 good=build();check(good,15,'before',IAT);check(good,47,'after',DATA);check(good,47,'before',IAT)
 controls=[]
 def refuse(label,fn):
  try:fn()
  except(ValueError,AssertionError,KeyError):controls.append(label);return
  raise AssertionError('Admitted adverse '+label)
 refuse('inherited_restore_phase13',lambda:check(build(restore=13),15,'before',IAT))
 refuse('inherited_lock13_108',lambda:build(counts=[108,108]))
 refuse('dropped_import_cell',lambda:build(r=rows[:-1]))
 bad=bytearray(o('phase/0/47/CRT-after/2013491200.bin'));bad[unused[0]]^=1;bad2=bytearray(n('sequence-0/phase-47-after-page-2013491200.bin'));bad2[unused[0]]^=1
 refuse('flipped_unused_data_byte_both_branches',lambda:check(good,47,'after',DATA,a=bytes(bad),b=bytes(bad2)))
 refuse('shifted_original_registry_metadata',lambda:check(good,47,'after',DATA,om=[reg[(0,47)]['source_computed_after_metadata'][0],reg[(0,47)]['source_computed_after_metadata'][1]+4]))
 refuse('native_lock25_changed',lambda:build(ld=[dict(loader[0],native_target=loader[0]['native_target']^1)]))
 stale=bytearray(o('phase/0/15/CRT-before/2013454336.bin'));sh=next(r for r in rows if r['observer_shim']);struct.pack_into('<I',stale,sh['offset'],sh['original_installed_target'])
 refuse('shim_left_installed_at_phase15',lambda:check(good,15,'before',IAT,a=bytes(stale)))
 out_q=out/'report.json';out_q.write_text(json.dumps(dict(passed=True,domain='O0 sequence0 actual inputs',admitted_unmodified_endpoints=3,adverse_controls=controls,accepted_function_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(report=str(out_q),sha256=sha(out_q),controls=controls)))
if __name__=='__main__':main(sys.argv[1])
