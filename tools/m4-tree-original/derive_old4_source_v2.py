"""Seal every recursively read workspace source input in the fresh proof."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];p=Path(__file__).with_name('old4_source.py');s=p.read_text()
anchor="PREP_SHA='6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1'"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
AUDITED_READS=set()
def audit_workspace_read(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 path=Path(args[0]).resolve()
 if not path.is_relative_to(ROOT):return
 mode=args[1]if len(args)>1 else None
 flags=args[2]if len(args)>2 else 0
 reading=isinstance(mode,str)and'r'in mode or(mode is None and isinstance(flags,int)and not(flags&3))
 if not reading:return
 if path.suffix.lower()=='.mwb':need(path.is_relative_to(ROOT/'reports/m4-tree-original/original125-execution-r1'),'No inherited or native capture in audited original source gate')
 AUDITED_READS.add(str(path))
sys.addaudithook(audit_workspace_read)
""")
old="pin(__file__);pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source.py');passed=True"
new="""pin(__file__);pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source.py');pin(ROOT/'tools/m4-tree-original/old4_source.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source_v2.py')
  for path in sorted(AUDITED_READS):pin(path)
  dependency_paths=sorted(AUDITED_READS)
  (out/'audited-workspace-reads.json').write_text(json.dumps(dependency_paths,indent=2)+'\\n');pin(out/'audited-workspace-reads.json');passed=True"""
assert s.count(old)==1;s=s.replace(old,new)
old="independent_compiled_original_sha256='a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260',reader_closed=True"
new="independent_compiled_original_sha256='a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260',recursive_workspace_source_reads_sealed=True,audited_input_paths=len(AUDITED_READS),reader_closed=True"
assert s.count(old)==1;s=s.replace(old,new)
out=p.with_name('old4_source_v2.py');assert not out.exists();out.write_text(s);print(json.dumps(dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
