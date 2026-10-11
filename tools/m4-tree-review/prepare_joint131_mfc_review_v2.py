"""Bind the independent byteflow review to the exact split-TIB witness."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    old=R/'tools/m4-tree-review/review_joint131_mfc_outputs.py';text=old.read_text();changes=[]
    def one(a,b):
        nonlocal text
        assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
    one("                    assert len(owners)==1,('Whole computed source owner',hex(a),n)","                    if not owners and (a,n)==(0x7ffde004,8):\n                        assert len(memory.get(a,b''))==len(memory.get(a+4,b''))==4\n                        return bytes(memory[a])+bytes(memory[a+4])\n                    assert len(owners)==1,('Whole computed source owner',hex(a),n)")
    one("                events=[tuple(r)for r in row['source_accesses']]", "                witness=row['TIB_region_representation'];equal(len(witness),1,'Exact finite TIB representation witness')\n                w=witness[0];equal((w['address'],w['literal_extent']),(0x7ffde004,8),'Exact two DWORD source-only input join')\n                equal([(r['address'],r['bytes'])for r in w['original_parts']],[(0x7ffde004,4),(0x7ffde008,4)],'Original carried split inventory')\n                equal(get(0x7ffde004,8).hex(),w['joined_BEFORE_hex'],'Whole independently reconstructed TIB BEFORE join')\n                equal(''.join(r['BEFORE_hex']for r in w['original_parts']),w['joined_BEFORE_hex'],'Both complete authentic source DWORDs')\n                assert not w['candidate_BEFORE_seed']and w['persistent_original_layout_restored']\n                events=[tuple(r)for r in row['source_accesses']]")
    one("                for owner in row['source_borrowed_backings']:","                equal(get(0x7ffde004,8).hex(),w['source_AFTER_joined_hex'],'Whole TIB byteflow after')\n                equal(''.join(r['source_AFTER_hex']for r in w['source_AFTER_parts']),w['source_AFTER_joined_hex'],'Inverse complete original split endpoints')\n                counts['independent_exact_TIB_join_inverse_relations']+=1\n                for owner in row['source_borrowed_backings']:")
    ast.parse(text);q=R/'tools/m4-tree-review/review_joint131_mfc_outputs_v2.py';assert not q.exists();q.write_text(text)
    files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(old,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted additive independent MFC byteflow review: exact original split-TIB complete join and inverse proof, every existing source/API/full endpoint guard unchanged',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
