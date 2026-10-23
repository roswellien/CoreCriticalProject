"""Bounded actual-read manifest and independently observed source-program closure.

The producing consumer's audit is retained as its evidence. This tool observes
only its own bounded source_program construction; it never reopens a capture.
"""
from pathlib import Path
import collections,hashlib,importlib.util,inspect,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reopened');v=sha(p);need(h is None or h==v,'Physical source dependency '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical dependency');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh closure supplement');out.mkdir(parents=True);passed=False;counts=collections.Counter();observations=[];retained={};raw_read=Path.read_bytes;text_read=Path.read_text
 try:
  p=Path(sys.argv[2]).resolve();source=read(p,sys.argv[3]);need(source['passed']and source['reader_closed']and source['source_and_provider_combined'],'Actual final one-pass consumer sealed/closed')
  pre=read(R/'reports/m4-formatting-source/provider130-preflight-r4/report.json','b50869b5af5beae7db10c9996d5b88601ffd6fde9c3e57031b47ae43812a313b');need(pre['passed']and pre['capture_reader_opened']is False,'Frozen final bounded import/row preflight')
  current_preparation=read(R/'reports/m4-joint-startup131-source/preparation-r6/report.json','fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8');current_preflight=read(R/'reports/m4-tree-review/joint131-source-preflight-r4/report.json','efba70d0a02bb89fd95f87eb4707f138e48444b4cb8cc076389c80bec32ad2f2')
  need(current_preparation['passed']and current_preflight['passed']and current_preflight['capture_reader_opened']is False,'Exact current reader6 representation repair independently admitted')
  for record in(current_preparation,current_preflight):
   for q,h in record['files'].items():pin(q,h)

  source6_preparation=read(R/'reports/m4-joint-startup138-source/preparation-r11/report.json','addd156cf83cf33776395bc55e958af83a1cdbca61ebcfc2af2d07ad9c821d72');need(source6_preparation['passed']and source6_preparation['archive_reader_opened']is False and source6_preparation['source_execution_performed']is False,'Exact current source6 prepared reader')
  for q,h in source6_preparation['files'].items():pin(q,h)
  for q,h in source['files'].items():
   if Path(q).suffix.lower()in('.mwb','.zip'):retained[q]=h;counts['retained_capture_parts_not_reopened']+=1
   else:pin(q,h);counts['physically_verified_consumer_noncapture_inputs']+=1
  for q,h in pre['files'].items():pin(q,h);counts['physically_verified_final_preflight_inputs']+=1
  entry=R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py';code=pin(entry,source['files'][str(entry.resolve())]).read_text()
  need("for source_path in READS-set(PINS):pin(source_path)"in code and "need(READS<=set(PINS)"in code,'Actual producing read audit is fully sealed')
  for guard in ('per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','canonical_reader_changed','duplicate_selected_source_reader'):need(source[guard]is False,'No alternate machine/capture reseeding')
  for q,h in source['files'].items():
   if Path(q).suffix.lower()=='.py':counts['physically_verified_executed_python_inputs']+=1
   elif Path(q).suffix.lower()=='.json':counts['physically_verified_consumer_JSON_inputs']+=1
  model_receipt=read(R/'reports/m4-formatting-source/persistent-family-model-r1/report.json','53c2a9f6dc3ede4ed5b089ff7c92490bbcdd4113679fc35ba830a4e359f50887');inherited_model=pin(model_receipt['model'],model_receipt['model_sha256']);model=R/'reports/m4-fps-original/source-preparation-r4/game_model.py';pin(model,source['files'][str(model.resolve())])
  def observed(path,method,args,kwargs):
   path=Path(path).resolve();need(path.is_relative_to(R)and path.suffix.lower()in('.json','.py')and path.stat().st_size<=16*1024*1024,'Only bounded source-program inputs')
   data=raw_read(path);digest=hashlib.sha256(data).hexdigest();frame=inspect.currentframe().f_back.f_back;caller=Path(frame.f_code.co_filename).resolve();caller_digest=hashlib.sha256(raw_read(caller)).hexdigest()
   need(source['files'].get(str(path))==digest and source['files'].get(str(caller))==caller_digest,'Every independent source read and caller physically equals the actual final consumer audit identity')
   observations.append(dict(path=str(path),sha256=digest,caller=str(caller),caller_sha256=caller_digest,caller_line=frame.f_lineno,function=frame.f_code.co_name,read_method=method,bytes=len(data)));PINS[str(path)]=digest;PINS[str(caller)]=caller_digest
   return data if method=='read_bytes'else text_read(path,*args,**kwargs)
  def read_bytes(path):return observed(path,'read_bytes',(),{})
  def read_text(path,*args,**kwargs):return observed(path,'read_text',args,kwargs)
  Path.read_bytes=read_bytes;Path.read_text=read_text
  spec=importlib.util.spec_from_file_location('independent_current131_bounded_source',model);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);program,callbacks=module.source_program()
  Path.read_bytes=raw_read;Path.read_text=text_read
  need(pre['physical_source_rows']==4637 and pre['source_callback_PC_count']==195 and len(program)==5728 and len(callbacks)==255 and all(pc in program for pc in(0x4b7f70,0x4e1ca0,0x4dea15,0x7810a290,0x7810a350)),'Independent complete current source program/root/callback inventory')
  counts['observed_independent_bounded_read_occurrences']=len(observations);counts['complete_consumed_source_program_JSON_inputs']=len({r['path']for r in observations});counts['independently_constructed_program_rows']=len(program);counts['independently_constructed_callback_PC_rows']=len(callbacks);counts['consumer_declared_actual_dependency_reads']=source['actual_dependency_reads']
  need(source['counts']['persistent_phases']==1656 and source['counts']['whole_page_BEFORE']==source['counts']['whole_page_AFTER']==114264 and source['counts']['literal_widget_roots']==84,'Exact complete persistent138 source coverage')
  need(observations and counts['physically_verified_consumer_noncapture_inputs']+len(retained)==len(source['files']),'Exact complete consumer file map partition')
  q=out/'source-program-read-correspondence.json';q.write_text(json.dumps(observations,indent=2)+'\n');pin(q);pin(__file__);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  Path.read_bytes=raw_read;Path.read_text=text_read
  result=dict(passed=passed,source_provider_path=str(p.resolve()),source_provider_sha256=sha(p),scope='Every actual final consumer declared noncapture input physically verified, archive identities retained for final full union rehash, plus independent bounded source_program read/caller correspondence; no repeated producing capture read trace',counts=dict(counts),complete_actual_consumer_noncapture_map_physically_sealed=passed,independent_bounded_source_program_reads_observed=passed,producing_native_consumer_runtime_read_tracing=False,capture_archives_opened=0,retained_capture_inputs=retained,full_dependency_union_rehashed=False,initializer_credit=0,files=PINS)
  q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
