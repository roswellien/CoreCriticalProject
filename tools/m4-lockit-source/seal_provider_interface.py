"""Bind frozen physical provider COFFs, initialized source rows and actual domain."""
from pathlib import Path
import copy,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;need(not out.exists(),'Fresh provider interface');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen provider input');pins[str(p)]=v;return p
 def receipt(p,h):
  p=pin(ROOT/p,h);d=json.loads(p.read_bytes());need(d['passed'],'Passing exact receipt');
  for q,v in d['files'].items():pin(q,v)
  return d
 lift=receipt('reports/m4-lockit-source/provider-lifts-r2/report.json','062caafd46c0e8c174df4a830c052fa405452542139de2cb4a4d244e39d1b0fa');symbols=receipt('reports/m4-lockit-source/provider-symbol-attribution-r1/report.json','3e24737262353534fa11016498adad5deda7f48ed6bdd504e29461ebf50e307c');actual=receipt('reports/m4-lockit-original/probe-validation-r1/report.json','ae8fe51982fbc608fa5b3f3b529acaca67baac508f9539e4ae00cb10be31f9c2');source=receipt('reports/m4-lockit-source/provider-recovery-r1/report.json','3b680223f22d6ac10cf440b885432909bef57b2f697d4df8afecb7f4ef814ad8')
 need(actual['genuine_loaded_domain']and actual['post_DllMain_state']==2 and not actual['state_seeded']and actual['balanced_pairs']==3 and actual['recursive_depth']==2,'Authentic loaded serial and recursive provider domain')
 contract=json.loads(pin(ROOT/'reports/m4-lockit-source/provider-recovery-r1/instruction-contracts.json').read_bytes());need(len(contract['instructions'])==17,'Seventeen admitted literal rows')
 contract['game_scratch_offsets']={str(root):dict(constructor=offset,destructor=offset)for root,offset in((0x411010,0x24),(0x4dc140,0x14),(0x500660,0x24),(0x5968f0,0x14))};contract['game_scratch_offset_basis']='Relative game CALL target entryESP after source RETURN push; before CALL ESP offset is four bytes smaller'
 contract['actual_domain_receipt']=str((ROOT/'reports/m4-lockit-original/probe-validation-r1/report.json').resolve());contract['actual_domain_receipt_sha256']='ae8fe51982fbc608fa5b3f3b529acaca67baac508f9539e4ae00cb10be31f9c2';contract['constructor_and_destructor_source_pointee_writes']=False;contract['guest_CS_structure_transport']=False
 cp=out/'instruction-contracts.json';cp.write_text(json.dumps(contract,indent=2)+'\n');pin(cp)
 physical=json.loads(pin(ROOT/'reports/m4-lockit-source/provider-symbol-attribution-r1/physical-dispatch.json').read_bytes());bodies=copy.deepcopy(lift['source_bodies']);lookup={r['entry']:r for r in physical}
 for b in bodies.values():
  b['manifest_original_symbol']=b['symbol'];b['symbol']=lookup[b['entry']]['source_function_symbol'];b['physical_symbol_metadata_correction_only']=True
 pin(__file__);report=dict(passed=True,scope='Exact initialized-domain provider source and physical AMD64 COFF interface, authentic32-bit provider observations; no initializer/native executioncredit',instruction_contracts=str(cp.resolve()),instruction_contracts_sha256=sha(cp),source_bodies=bodies,entry_objects=lift['entry_objects'],body_count=2,physical_COFF_count=4,admitted_rows=17,admitted_bytes=51,physical_full_source_intervals_retained=True,cold_state0_admitted=False,contended_state1_admitted=False,actual_loaded_state=2,actual_domain_receipt_sha256=contract['actual_domain_receipt_sha256'],provider_lifts_sha256='062caafd46c0e8c174df4a830c052fa405452542139de2cb4a4d244e39d1b0fa',physical_symbol_sha256='3e24737262353534fa11016498adad5deda7f48ed6bdd504e29461ebf50e307c',native_execution=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),contract_sha256=sha(cp))))
if __name__=='__main__':main(sys.argv[1])
