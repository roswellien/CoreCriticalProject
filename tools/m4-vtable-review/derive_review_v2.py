"""Correct a review-only digest copied from the parent file's LF representation."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=H/'provider_review.py';new=H/'provider_review_v2.py';assert not new.exists()
equal=H/'exact_equal.py';parent=R/'tools/m4-container-review/exact_equal.py'
assert sha(equal)=='cc048da31a6624cef4292c20d801b3ec39450208f6ba3df67fb222f3c63a4925'
assert sha(parent)=='7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97'
assert equal.read_bytes().replace(b'\r\n',b'\n')==parent.read_bytes()
assert ast.dump(ast.parse(equal.read_text()))==ast.dump(ast.parse(parent.read_text()))
out=R/'reports/m4-vtable-review/provider-review-r1';assert out.exists()and not(out/'report.json').exists()
(out/'report.json').write_text(json.dumps(dict(passed=False,scope='Review-only expected digest mismatch; completed provider-source-r1 remains passed and unchanged',reason='The copied exact_equal.py has CRLF line endings, while the reviewer expected the parent LF file SHA. Preparation and source proof correctly pinned the new physical bytes.',expected_sha256=sha(parent),actual_sha256=sha(equal),source_execution_repeated=False,files={str(old.resolve()):sha(old),str(equal.resolve()):sha(equal),str(parent.resolve()):sha(parent)}),indent=2)+'\n')
s=old.read_text().replace("pin(H/'exact_equal.py','7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97')","pin(H/'exact_equal.py','cc048da31a6624cef4292c20d801b3ec39450208f6ba3df67fb222f3c63a4925')")
anchor=" eq=load('unchanged_complete_equality120'";assert s.count(anchor)==1
proof=" need(pin(H/'exact_equal.py').read_bytes().replace(b'\\r\\n',b'\\n')==pin(R/'tools/m4-container-review/exact_equal.py','7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97').read_bytes(),'Only CRLF serialization differs; every equality source byte is retained')\n"
s=s.replace(anchor,proof+anchor).replace('complete_equality_cases=eq,','complete_equality_cases=eq,equality_physical_change_only_CRLF=True,')
ast.parse(s);new.write_text(s);print(json.dumps(dict(passed=True,reviewer_sha256=sha(new))))
