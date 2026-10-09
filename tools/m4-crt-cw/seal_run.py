"""Seal original hardware-only CW research; no native acceptance inferred."""
from pathlib import Path
import hashlib,json,platform,winreg
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def need(ok,why):
 if not ok:raise ValueError(why)
def main():
 out=ROOT/'reports/m4-crt-cw/closure-r1';need(not out.exists(),'Fresh CW closure required');files={}
 def add(p,h=None):q=Path(p).resolve();s=sha(q);need(h is None or s==h,'Exact CW physical bytes');files[str(q)]=s
 build=ROOT/'reports/m4-crt-cw/build-r1/build.json';m=json.loads(build.read_text(encoding='utf-8-sig'));need(m['passed'],'Exact CW build passed')
 for group in ('source_files','tool_files','artifacts'):
  for path,h in m[group].items():add(path,h)
 for c in m['literal_source_copies']:add(c['preserved_path'],c['sha256'])
 for name in ('build-r1','run-r1','analysis-r1'):
  for p in (ROOT/'reports/m4-crt-cw'/name).rglob('*'):
   if p.is_file():add(p)
 for p in (ROOT/'tools/m4-crt-cw').iterdir():
  if p.is_file():add(p)
 add(ROOT/'docs/m4-crt-cw-research.md');add(build)
 run=json.loads((ROOT/'reports/m4-crt-cw/run-r1/report.json').read_text());analysis=json.loads((ROOT/'reports/m4-crt-cw/analysis-r1/report.json').read_text());need(run['passed'] and analysis['passed'] and analysis['records']==131072 and len(analysis['observer_controls'])==62 and analysis['hardware_faults']==0,'Exact complete CW observations/control counts');need(analysis['normalization']['keep_mask']==0x1f3f and analysis['normalization']['forced_one_mask']==0x40,'Exact measured all-word policy');need(run['worker']['sha256']==m['artifacts'][run['worker']['path']],'Actual compiled CW worker association')
 out.mkdir();info={'timing':'Collected after the hardware run; not an execution-time attestation','platform':platform.platform(),'python_process_machine':platform.machine()}
 try:
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
   info['processor']={n:winreg.QueryValueEx(key,n)[0] for n in ('ProcessorNameString','Identifier','VendorIdentifier')}
 except OSError as e:info['processor_unavailable']=str(e)
 (out/'hardware-information.json').write_text(json.dumps(info,indent=2)+'\n');add(out/'hardware-information.json');report={'passed':True,'scope':'Author original hardware CW normalization research only; independent review pending, native bridge/full CRT/menu incomplete','analysis':bind(ROOT/'reports/m4-crt-cw/analysis-r1/report.json'),'build':bind(build),'source_tool_artifact_counts':{k:len(m[k]) for k in ('source_files','tool_files','artifacts')},'records':131072,'actual_16bit_inputs':65536,'exact_repeats':65536,'hardware_faults':0,'actual_host_restore_captures':131072,'actual_worker_controls':5,'observer_controls':62,'normalization':analysis['normalization'],'physical_bindings_before_report':len(files),'vendor_or_game_code_executed':False,'native_bridge_admitted':False,'whole_M4_complete':False,'limits':analysis['limits']};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');add(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('CW hardware research sealed:',len(files),'physical files',sha(out/'report.json'),sha(out/'pins.json'))
if __name__=='__main__':main()
