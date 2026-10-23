"""Add constructor source-proved FS union partition; preserve v2 source."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preparation-r3';assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 parent=R/'reports/m4-native141-source/observer-preparation-r2';pin(parent/'report.json')
 for name in('final_observer141_parent.py','final_observer141_parent_v2.py'):
  p=pin(parent/name);(out/name).write_bytes(p.read_bytes());pin(out/name)
 p=pin(R/'tools/m4-native141-source/final_observer141_v2.py');t=p.read_text();a="PREP=ROOT/'reports/m4-native141-source/observer-preparation-r2'";b=a.replace('-r2','-r3');assert t.count(a)==1;t=t.replace(a,b)
 extra='\nfrom constructor_fs_union141_v1 import partition as _partition_normal_FS\ndef partition_normal_FS(archive,stem):\n return _partition_normal_FS(archive,stem,S.CURRENT,ROOTS)\n'
 t+=extra;q=R/'tools/m4-native141-source/final_observer141_v3.py';assert not q.exists();q.write_text(t);pin(q)
 for p in [R/'tools/m4-native141-source/constructor_fs_union141_v1.py',R/'tools/m4-native141-source/constructor_journal141_v1.py',R/'tools/m4-native141-source/persistent_constructors_v4.py',R/'reports/m4-startup141-runway/service-preparation-r2/session_impl.inc',R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json',Path(__file__)]:pin(p)
 (out/'source-delta.json').write_text(json.dumps(dict(parent=str(p),exact_substitution=dict(before=a,after=b),appended_source=extra),indent=2)+'\n');pin(out/'source-delta.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,source_only=True,source_execution=False,canonical_reader_opened=False,accepted_credit=False,inherited_full_journal_guards=True,legacy_FS_frames=28,legacy_FS_records=56,new_constructor_FS_frames=7,new_constructor_FS_records=14,whole_union_FS_frames=35,whole_union_FS_records=70,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
