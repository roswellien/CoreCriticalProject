"""Lossless original observation supplement; no numerical expected outputs."""
import argparse,hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-reference'
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,m):
 if not v:raise ValueError(m)
def main(out):
 out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private observation supplement');source=BASE/'run-normal-r1';report=read(source/'report.json');need(report['passed']and report['records']==48,'Actual successful original observations');files={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact original association '+str(p));files[str(p)]=v
 for p,h in read(source/'pins.json')['files'].items():bind(p,h)
 for name in('report.json','pins.json'):bind(source/name)
 review=BASE/'root-pre-execution-review-r2'
 for p,h in read(review/'pins.json')['files'].items():bind(p,h)
 bind(review/'report.json','1ad3d36de177a8c3a54ee49e52b1ee4a64ce280bcba098b892abaa188787c83a');bind(review/'pins.json');bind(__file__)
 rows=read(source/'actual-rows.json')['rows'];b=(source/'original.bin').read_bytes();need(sha(source/'original.bin')=='cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2','Exact first original primary')
 def raw(row):
  start=row['raw_offset_including_row_length']+4;return b[start:start+row['raw_bytes_including_row_length']-4]
 findings=[];pairs=[]
 for i in range(24):
  direct,instrumented=rows[i],rows[i+24];d,z=raw(direct),raw(instrumented);need(direct['tags']['cw']==instrumented['tags']['cw']and direct['tags']['repeat']==instrumented['tags']['repeat'],'Measured debug pair association')
  original_fx_before=d[188:700];original_fx_after=d[700:1212];original_env_before=d[2236:2264];original_env_after=d[2264:2292];debug_env_after=z[2264:2292]
  variable=91348+40*(direct['tags']['stack_pages_before']+direct['tags']['stack_pages_after']);n=direct['tags']['stack_bytes'];sb=d[variable:variable+n];sa=d[variable+n:variable+2*n]
  changed=[j for j in range(n)if sb[j]!=sa[j]];relative=[direct['tags']['stack_base']+j-direct['tags']['writer_sp']for j in changed]
  fx_diff=[j for j in range(512)if original_fx_before[j]!=original_fx_after[j]];env_diff=[j for j in range(28)if original_env_after[j]!=debug_env_after[j]]
  pairs.append({'direct_id':i,'debug_id':i+24,'CW':direct['tags']['cw'],'repeat':direct['tags']['repeat'],'actual_direct_ENV_before_hex':original_env_before.hex(),'actual_direct_ENV_after_hex':original_env_after.hex(),'actual_debug_ENV_after_hex':debug_env_after.hex(),'direct_before_after_FX_changed_offsets':fx_diff,'direct_vs_debug_ENV_changed_offsets':env_diff,'direct_nonzero_legacy_metadata_preserved':original_env_before[12:26]==original_env_after[12:26]and any(original_env_after[12:26]),'debug_legacy_metadata_zero':debug_env_after[12:26]==bytes(14),'direct_FX_metadata_zero':original_fx_after[6:24]==bytes(18),'direct_guest_CPU_equal_debug_except_real_ESP':{k:v for k,v in direct['after_CPU'].items()if k!='esp'}=={k:v for k,v in instrumented['after_CPU'].items()if k!='esp'},'direct_stack_changed_bytes':len(changed),'direct_stack_change_min_max_relative_W':[min(relative),max(relative)]if relative else None,'original_service_implementation_stack_footprint_is_native_defined':False,'actual_debug_feature_return':instrumented['debug_events'][2]['before'],'direct_source_written_BOOL':direct['source_written_adjust_fdiv']})
 out.mkdir();result={'passed':True,'scope':'Actual original-only observations and explicit instrumentation effects; native comparison absent','original_report':str(source/'report.json'),'primary_raw_sha256':sha(source/'original.bin'),'direct_rows':24,'debug_rows':24,'direct_retained_legacy_metadata_rows':sum(x['direct_nonzero_legacy_metadata_preserved']for x in pairs),'debug_zeroed_legacy_metadata_rows':sum(x['debug_legacy_metadata_zero']for x in pairs),'direct_zero_FX_metadata_rows':sum(x['direct_FX_metadata_zero']for x in pairs),'CPU_equal_after_debug_except_ESP_rows':sum(x['direct_guest_CPU_equal_debug_except_real_ESP']for x in pairs),'actual_feature_results':sorted({x['actual_debug_feature_return']['eax']for x in pairs}),'actual_feature_ECX_EDX':sorted({(x['actual_debug_feature_return']['ecx'],x['actual_debug_feature_return']['edx'])for x in pairs}),'actual_stack_extents':sorted({(r['tags']['stack_base'],r['tags']['stack_bytes'],r['tags']['writer_sp'],r['tags']['base_before'])for r in rows}),'actual_thread_ID_count':len({r['tags']['thread_id']for r in rows}),'pairs':pairs,'projection_policy':['Direct debug-off CPU/FX/ENV BEFORE is the only future architectural replay input.','Debug-on source-return CONTEXT is a separate measured ABI boundary observation; it cannot replace direct hardware FP metadata.','Original whole Windows stack and API implementation footprint remain raw. No whole-stack portable equality or normalization is asserted.','Source API ECX/EDX/flags are ABI unspecified; original high halves W-34..W-32 and W-42..W-40 remain observed. Native preserved-volatiles representative is distinct.','The real original source BOOL was observed; no initialized file-zero inference or invented host lookup result.'],'native_execution_or_equivalence_accepted':False,'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print(json.dumps({'passed':True,'bindings':len(files),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
