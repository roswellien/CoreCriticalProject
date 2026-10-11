"""Bounded current52 source result/provenance review; no archive or worker."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
FILES={};CHECKS=[]
def need(v,label):
 if not v:raise ValueError(label)
 CHECKS.append(label)
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No canonical capture input');b=p.read_bytes();v=hashlib.sha256(b).hexdigest();need(h is None or h==v,'Exact current file '+str(p));need(str(p)not in FILES or FILES[str(p)]==v,'Stable bounded source file');FILES[str(p)]=v;return b
def read(p,h=None):return json.loads(pin(p,h))
def main(name):
 out=R/'reports/m4-widget-source-review'/name;need(not out.exists(),'Fresh independent source outcomes');out.mkdir(parents=True)
 reviews=[('preparation-r1','2735874186cda744c1989f4f3e2f318593768ee9ce55a263d36531a1992f10b4'),('registry-parser-preparation-r1','e22b51c32e25ca88861bc8465db696ebf35c7851dd9e243f553df4e4f1af0c3a'),('registry-source-preparation-r1','8ef71e65337965c3c67df83165d1a744f985434a1527f8530df9e682532e20d6'),('registry-serialization-preparation-r1','9ebd18323adf86226fa0de7257a61022a7c050ff32ccad0b398195ff65ae65db')]
 for directory,h in reviews:
  receipt=read(R/'reports/m4-widget-source-review'/directory/'report.json',h);need(receipt['passed'],'Passed exact additive preparation '+directory)
  for p,v in receipt['files'].items():pin(p,v)
 execution_sha='1b7f14c5b68f43df3389b9d6cddbbf9dd594c794b4420e002349188313a7a12c'
 e=read(R/'reports/m4-widget-native/fixture-execution-r4/report.json',execution_sha);need(e['passed']and e['all_workers_terminal'],'Exact actual52 workers closed')
 pp=R/'reports/m4-widget-native/source-prefix-r1/report.json';rp=R/'reports/m4-widget-native/source-registry-r4/report.json'
 p=read(pp,'38986acdc2600a5f9207d6724ff237beca57fd3facd7d2d3dbb89fffef15088b')
 r=read(rp,'ef11e37177594ded312110b2efc4ae6c4939b15d23e89563bc4ba2a050ffc737')
 need(p['passed']and r['passed']and p['execution_sha256']==r['execution_sha256']==execution_sha,'Both passed source passes bind exact current worker')
 need(r['prefix_source_sha256']=='38986acdc2600a5f9207d6724ff237beca57fd3facd7d2d3dbb89fffef15088b','Registry entry binds actual prefix result')
 need(not p['AFTER_State_or_memory_seed']and not r['AFTER_machine_or_memory_seed']and
      not p['archive_reader_opened']and not r['archive_reader_opened']and
      p['successful_read_chain_physically_pinned']and r['successful_read_chain_pinned'],
      'Complete successful read chain and explicit source-only scope')
 expected_p={'literal_prefixes':12,'exact_prefix_operand_rows':49250,'actual_GDI_scalar_response_joins':294,'whole_API_frame64_joins':294,'FS_source_relations':1158,'virtual_source_relations':1010,'array_source_relations':150,'whole_State3504_entry_joins':12,'whole_stack4096_relations':12,'whole_game_bytes_compared':74956800}
 expected_r={'literal_provider_operands':804,'actual_source_API_joins':36,'whole_provider_page_or_capacity_relations':720,'literal_tail_instructions':120,'literal_tail_RET_operand_relations':36,'whole_source_root_State3504_relations':12,'whole_source_root_stack4096_relations':12,'unmodeled_cleanup_after_interval_joins':60}
 for k,v in expected_p.items():need(p['counts'][k]==v,'Exact prefix extent '+k)
 for k,v in expected_r.items():need(r['counts'][k]==v,'Exact provider/tail extent '+k)
 # These small derivations are retained source results, not machine seeds or
 # duplicate raw equality runs. The actual source comparers own raw equality.
 pd=read(pp.parent/'source-derivations.json',p['files'][str((pp.parent/'source-derivations.json').resolve())]);rd=read(rp.parent/'source-derivations.json',r['files'][str((rp.parent/'source-derivations.json').resolve())])
 need(len(pd)==len(rd)==12,'Twelve both-level actual source result rows')
 contract=read(R/'reports/m4-font479590-original/source-preparation-r1/source-contracts.json');program={x['pc']:x for x in contract['instructions']}
 provider=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d')
 provider_program={x['pc']:x for x in provider['instructions']}
 roots=[0x40e250,0x40ef50,0x5a3c30,0x5a3ff0,0x5a66f0,0x479590];seen=set();PC_count=snapshots=0;SETE_count=0;rows=[]
 for a,b in zip(pd,rd):
  key=(a['level'],a['phase']);need(key not in seen and key==(b['level'],b['phase'])and a['root']==b['root']==roots[a['phase']],'Whole current level/root/phase identity');seen.add(key)
  need(a['source_PCs'][-1]==0x5ac11e and b['source_PCs'][0]==0x78004a36,'Literal owning CALL to provider source entry')
  need(all(pc in program for pc in a['source_PCs']),'All reached widget prefix PCs are independently matched physical rows')
  need(all(pc in program or pc in provider_program for pc in b['source_PCs']),'Every reached registry/tail PC is an authenticated literal source row')
  need(len(b['provider_source_accesses'])==67 and len(b['tail_source_accesses'])==3 and len(b['source_API_indices'])==3,'Exact per-root source provider and final RET operands')
  for phase,value in b['source_API_phases'].items():
   state=bytes.fromhex(value['state']);fx=bytes.fromhex(value['fx']);need(len(state)==3504 and len(fx)==512 and len(value['CPU'])==10,'Full reversible computed source snapshot '+phase);snapshots+=1
  current_SETE=[pc for pc in a['source_PCs'] if program[pc]['mnemonic']=='sete'];SETE_count+=len(current_SETE)
  need(not a['original_output_input']and not a['registration_provider_executed_by_model']and not b['AFTER_machine_seed']and not b['bootstrap_source_execution_modeled'],'Explicit input/model provenance retained')
  PC_count+=len(a['source_PCs'])+len(b['source_PCs']);rows.append(dict(level=a['level'],phase=a['phase'],root=a['root'],prefix_PCs=len(a['source_PCs']),provider_and_tail_PCs=len(b['source_PCs']),SETE_reached=current_SETE,computed_entry_State_sha256=a['computed_provider_entry_State_sha256'],computed_final_State_sha256=b['source_computed_final_State_sha256']))
 need(seen=={(level,phase)for level in('O0','O2')for phase in range(6)},'Complete both-level six-root outcomes')
 need(PC_count==42404 and snapshots==84 and SETE_count==0,'Exact complete literal instruction/snapshot extent; omitted SETE guard dormant in actual finite domain')
 q=out/'source-result-joins.json';q.write_text(json.dumps(rows,indent=2)+'\n');pin(q);pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Independent bounded current52 result identity/physical source coverage/provenance and exact additive repair closure; actual raw equality is owned by pinned prefix4/registry7 source runs',
  execution_sha256=execution_sha,prefix_sha256='38986acdc2600a5f9207d6724ff237beca57fd3facd7d2d3dbb89fffef15088b',registry_sha256='ef11e37177594ded312110b2efc4ae6c4939b15d23e89563bc4ba2a050ffc737',
  counts=dict(root_results=12,total_literal_instructions=PC_count,computed_whole_State_FX_CPU_snapshots=snapshots,SETE_reached=SETE_count,checks=len(CHECKS)),
  workers_and_file_handles_closed=True,archive_reader_opened=False,worker_launched=False,AFTER_machine_seed=False,bootstrap_or_cleanup_source_claimed=False,initializer_credit=0,
  pending=['Actual native GDI API physical export/resource/caller/private observer lifecycle proof and causal refusals','Persistent full initializer schedule source/paired/equality integration'],checks=CHECKS,files=FILES)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),passed=True,counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
