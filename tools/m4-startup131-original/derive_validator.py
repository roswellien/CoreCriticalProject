from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
base=R/'tools/m4-startup130-original/validate_v2.py';p=T/'validate.py';assert not p.exists()
s=base.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
one("BASE=ROOT/'reports/m4-startup130-original'","BASE=ROOT/'reports/m4-startup131-original'")
one("sys.path.insert(0,str(Path(__file__).resolve().parent));from family_phase_v2 import observe as observe_family,cleanup as cleanup_family","sys.path.insert(0,str(ROOT/'tools/m4-startup130-original'));from family_phase_v2 import observe as observe_family,cleanup as cleanup_family\nsys.path.insert(0,str(Path(__file__).resolve().parent));from mfc_phase import observe as observe_mfc,constructor as observe_constructor")
one('def main(build,digest,execution,name):','def main(build,digest,execution,preflight_path,preflight_digest,name):')
one("p['original_roots']==130","p['original_roots']==131")
one("len(p['order'])==130 and [r['entry']for r in p['order']if r['entry']not in(0x4b64f0,0x4df610,0x4e0710,0x4e0810,0x4e1ca0)]","len(p['order'])==131 and p['order'][13]['entry']==0x5ae3e4 and [r['entry']for r in p['order']if r['entry']not in(0x5ae3e4,0x4b64f0,0x4df610,0x4e0710,0x4e0810,0x4e1ca0)]")
one("header[:8]==b'MW4J130O'and struct.unpack_from('<6I',header,8)==(1,6,130,780,43,356992)","header[:8]==b'MW4J131O'and struct.unpack_from('<6I',header,8)==(1,6,131,786,43,356992)")
one("prelaunch=read(pin(ROOT/'reports/m4-tree-review/original130-prelaunch-r7/report.json','bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127'));need(prelaunch['passed']and prelaunch['build_sha256']==digest,'Independent final compiled worker observer attribution')","prelaunch=read(pin(preflight_path,preflight_digest));need(prelaunch['passed']and prelaunch['build_sha256']==digest and prelaunch['files'].get(str(build))==digest and prelaunch['files'].get(str(Path(b['worker']).resolve()))==b['worker_sha256'],'Independent current final compiled worker observer attribution');need(run['preflight_sha256']==preflight_digest,'Actual execution bound current independent preflight')\n   for file_,hash_ in prelaunch['files'].items():pin(file_,hash_)")
one("obs=read(ROOT/'reports/m4-tree-review/original130-prelaunch-r7/compiled-observers.json');","obs=read(Path(preflight_path).parent/'compiled-observers.json');")
one('geometry=[];snapshot_rows=[];allowners=[]','geometry=[];snapshot_rows=[];allowners=[];mfc_artifacts=[];constructor_artifacts=[]')
one('     observe_family(records,data,seq,phase,entry,page,formats,mixed,family_artifacts,counts,tid,targets,format_byentry)','     observe_family(records,data,seq,phase,entry,page,formats,mixed,family_artifacts,counts,tid,targets,format_byentry)\n     if entry==0x5ae3e4:observe_mfc(records,data,seq,phase,out,pin,counts,mfc_artifacts)')
one("   need(counts['phases']==780","   observe_constructor(records,out,pin,counts,constructor_artifacts)\n   need(counts['MFC_original_phases']==6 and counts['MFC_full_normal_boundaries']==42 and counts['MFC_full_named_API_pairs']==24 and counts['MFC_true_root_TIB8192_endpoints']==12 and counts['constructor_prerequisite_graph_endpoints']==12,'Complete genuine new six-domain MFC and constructor prerequisite observation extents')\n   for name_,rows_ in [('fresh-MFC-observations.json',mfc_artifacts),('fresh-constructor-prerequisites.json',constructor_artifacts)]:q_=out/name_;q_.write_text(json.dumps(rows_,indent=2)+'\\n');pin(q_)\n   need(counts['phases']==786")
one("counts['extra_whole_page_endpoint_relations']==4680 and counts['exact_format_IAT_endpoint_relations']==4680","counts['extra_whole_page_endpoint_relations']==4716 and counts['exact_format_IAT_endpoint_relations']==4716")
one("pin(ROOT/'tools/m4-startup130-original/family_phase_v2.py');pin(sys.executable)","pin(ROOT/'tools/m4-startup130-original/family_phase_v2.py');pin(Tool_mfc:=Path(__file__).resolve().parent/'mfc_phase.py');pin(sys.executable)")
one("if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])","if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),Path(sys.argv[4]).resolve(),sys.argv[5],sys.argv[6])")
# Labels change only after all finite checked semantic hunks above.
s=s.replace('original130','original131').replace('Original130','Original131').replace('successful130','successful131')
# Keep the actual inherited helper path and ABI proof pinned to its frozen file.
s=s.replace("ROOT/'tools/m4-startup131-original/family_phase_v2.py'","ROOT/'tools/m4-startup130-original/family_phase_v2.py'")
s=s.replace("ROOT/'tools/m4-startup131-original'));from family_phase_v2","ROOT/'tools/m4-startup130-original'));from family_phase_v2")
p.write_text(s)
q=T/'validator-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),new_MFC_observer=str(T/'mfc_phase.py'),new_MFC_observer_sha256=hashlib.sha256((T/'mfc_phase.py').read_bytes()).hexdigest(),changes=['Exact131 physicalorder/header/786phase extent','Externally fixed current preflight and final format targets','Fresh genuine MFC42normal/24APIpairs/12TIB endpoints and observed complete module/backing inputs','Separate actual constructor12graph/whole5F2000/HeapAlloc occurrence joins','Existing complete130 retained family observations remain required, counts only grow at6addedphases'],fixed_record_ABI_unchanged=True,reader_opened=False),indent=2)+'\n')
print(p)
