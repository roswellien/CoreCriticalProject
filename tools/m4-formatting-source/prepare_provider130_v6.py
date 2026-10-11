"""Freeze complete raw-FS source chronology without opening any capture."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 src=HERE/'compare_provider130_v3.py';dst=HERE/'compare_provider130_v4.py';assert not dst.exists();s=src.read_text()
 a='import formatting_derivations_v2 as FD';assert s.count(a)==1;s=s.replace(a,'import formatting_derivations_v3 as FD')
 a="pin(ROOT/'tools/m4-formatting-source/formatting_derivations_v2.py');";assert s.count(a)==1;s=s.replace(a,a+"pin(ROOT/'tools/m4-formatting-source/formatting_derivations_v3.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v6.py');")
 ast.parse(s);dst.write_text(s)
 files={str(p.resolve()):sha(p)for p in(src,dst,Path(__file__),HERE/'formatting_derivations.py',HERE/'formatting_derivations_v2.py',HERE/'formatting_derivations_v3.py',HERE/'final_observer130.py',HERE/'final_observer130_v2.py',HERE/'continuity130.py',ROOT/'reports/m4-formatting-native/preparation-r19/locale_batch_operations.inc',ROOT/'reports/m4-formatting-native/preparation-r19/fs_operations.inc')}
 report=dict(passed=True,scope='Complete130 combined source/provider preparer with whole32Q frames and whole16Q raw FS chronology',tool=str(dst),whole_FS_raw16Q=True,install_source_index='precommitted source write index',restore_source_index='committed source write index+1',install_active_depth='source frame depth before push',restore_active_depth='source frame depth+1 before pop',FS_expected_head='literal saved predecessor at both retained raw snapshots',files=files,executed=False,capture_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
