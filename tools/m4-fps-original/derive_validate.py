"""Additive actual FPS sides to frozen genuine font6 observer validator."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact validator hunk '+a[:100])
 return s.replace(a,b,1)
def main():
 source=R/'tools/m4-font479590-original/validate_v2.py';s=source.read_text(encoding='utf-8-sig');pins={str(source):sha(source)}
 parent=R/'reports/m4-font479590-original/validation-r1/report.json';p=json.loads(parent.read_bytes())
 if not p['passed']or p['files'][str(source)]!=pins[str(source)]:raise ValueError('Frozen actual font validator')
 pins[str(parent)]=sha(parent)
 s=one(s,"BASE=R/'reports/m4-font479590-original'","BASE=R/'reports/m4-fps-original'")
 s=one(s,'input_index=[];font_domains=[];source_inputs=[]','input_index=[];font_domains=[];source_inputs=[];fps_events=[];fps_domains=[]')
 s=one(s,'==(1,6,6,356992)','==(1,7,7,356992)')
 s=one(s,"prep['snapshot_bytes']==266964 and prep['combined_source_pages']==64","prep['snapshot_bytes']==266964 and prep['fps_snapshot_bytes']==529700 and prep['combined_source_pages']==64")
 s=one(s,"pin(__file__);pin(R/'tools/m4-font479590-original/derive_validate_v2.py')","pin(__file__);pin(R/'tools/m4-fps-original/derive_validate.py');pin(R/'tools/m4-fps-original/fps_validation.inc');pin(R/'tools/m4-font479590-original/validate_v2.py');pin(R/'tools/m4-font479590-original/derive_validate_v2.py')")
 s=one(s,"(1,1,6,6,43,356992)","(1,1,7,7,43,356992)")
 s=one(s,'source_returns=[0x5a0142,0x5a0645,0x5a0751];','fps_identity=words(capture.data(\'fps/identity.bin\'),0,4);need(fps_identity[0]==0x5bb53c and fps_identity[1]==0x780230dd and fps_identity[2]!=0 and fps_identity[3]==0x78000000,\'Actual named stagedvsprintf owning IAT identity\');source_returns=[0x5a0142,0x5a0645,0x5a0751];')
 inc=T/'fps_validation.inc';pins[str(inc)]=sha(inc)
 s=one(s,"   fcount=words(capture.data(stem+'fs-event-count.bin'))[0];",inc.read_text()+"   fcount=words(capture.data(stem+'fs-event-count.bin'))[0];")
 s=one(s,"counts['actual_root_phases']==6 and len(font_domains)==1","counts['actual_root_phases']==7 and len(font_domains)==len(fps_domains)==1")
 s=one(s,"if logical_name.endswith('widget-snapshots.bin'):continue","if logical_name.endswith(('widget-snapshots.bin','fps-snapshots.bin')):continue")
 s=one(s,"('actual-root-endpoints.json',roots)","('actual-FPS-boundaries.json',fps_events),('actual-FPS-domain.json',fps_domains),('actual-root-endpoints.json',roots)")
 s=one(s,'current_font_domain_observed=True,','current_font_domain_observed=True,current_nonnull_fps_domain_observed=True,')
 s=s.replace('Complete actual six-root plus new current-instance domain extent','Complete actual seven-root plus current font and nonnull fps extent')
 q=T/'validate.py'
 if q.exists():raise ValueError('Fresh derivative actual FPS validator')
 q.write_text(s);pins[str(Path(__file__).resolve())]=sha(__file__);(T/'validation-lineage.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
if __name__=='__main__':main()
