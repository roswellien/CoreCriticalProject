"""Refresh bounded four-root source proof for current original130 process."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-tree-original/old4_source_v3.py';s=p.read_text();changes=[]
def one(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'before':a,'after':b})
one("BASE=ROOT/'reports/m4-tree-original'","BASE=ROOT/'reports/m4-startup130-original'")
one("VALIDATION=ROOT/'reports/m4-tree-original/original125-validation-r1/report.json'","VALIDATION=ROOT/'reports/m4-startup130-original/validation-r2/report.json'")
one("VALIDATION_SHA='5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'","VALIDATION_SHA='91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca'")
one("PREP=ROOT/'reports/m4-tree-original/original125-preparation-r1'","PREP=ROOT/'reports/m4-startup130-original/preparation-r2'")
one("PREP_SHA='6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1'","PREP_SHA='8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'")
one("ROOT/'reports/m4-tree-original/original125-execution-r1'","ROOT/'reports/m4-startup130-original/execution-r2'")
one("len(p['order'])==125,'Exact original125 order and43 pages'","len(p['order'])==130,'Exact original130 order and43 fixed pages plus3 external whole pages'")
one("review=read(ROOT/'reports/m4-tree-original/full-original-review-r3/report.json','a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260');need(review['passed']and review['original_validation_sha256']==VALIDATION_SHA,'Fresh complete final linked observer gate')", """review=read(ROOT/'reports/m4-tree-review/original130-prelaunch-r7/report.json','bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127');validation=read(VALIDATION,VALIDATION_SHA)
 need(review['passed']and review['build_sha256']==validation['build_sha256']=='3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'and review['preparation_sha256']==validation['preparation_sha256']==PREP_SHA,'Fresh complete final linked observer gate and actual process validation')
 extra_pages=p['extra_whole_source_pages'];need(extra_pages==[0x5cd000,0x5e3000,0x5e9000],'Three complete physical additional source pages')
 iat_path=Path(VALIDATION).parent/'format-IAT-relations.json';read(iat_path,validation['files'][str(iat_path.resolve())])""")
one("build=read(ROOT/'reports/m4-tree-original/original125-build-r1/build.json','e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585')","build=read(ROOT/'reports/m4-startup130-original/build-r2/build.json','3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103')")
one("owners={};previous=None", "owners={};previous=None;previous_extra={}")
one("   previous=b\n   if entry in roots:", """   previous=b
   before_extra={a:reader.data(f'phase/{seq}/{phase}/extra-before/{a}.bin')for a in extra_pages};after_extra={a:reader.data(f'phase/{seq}/{phase}/extra-after/{a}.bin')for a in extra_pages}
   for a in extra_pages:
    need(len(before_extra[a])==len(after_extra[a])==4096,'Complete external source page endpoints')
    if previous_extra:equal(before_extra[a],previous_extra[a],'Complete original external source page carry')
   previous_extra=after_extra
   if entry in roots:""")
one("    memory[0x7ffde000]=bytearray", "    memory.update({a:bytearray(v)for a,v in before_extra.items()});after.update(after_extra)\n    memory[0x7ffde000]=bytearray")
one("    for page in pages:\n     if page==0x20001000:continue", "    for page in pages+extra_pages:\n     if page==0x20001000:continue")
one("  pin(__file__);pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');", "  pin(__file__);pin(ROOT/'tools/m4-startup130-original/derive_old4_source.py');pin(ROOT/'tools/m4-tree-original/old4_source_v3.py');pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');")
one("carried across125 phases", "carried across130 phases; all46 current source pages supplied from own genuine BEFORE")
one("original_build_sha256='e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585'", "original_build_sha256='3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'")
one("independent_compiled_original_sha256='a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260'", "independent_compiled_original_sha256='bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127'")
out=Path(__file__).with_name('old4_source.py');assert not out.exists();out.write_text(s)
print(json.dumps({'source':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':len(changes)}))
