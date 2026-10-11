"""Refresh accepted four-root source proof for genuine original125 process."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-lockit-paired-provider/original_v2.py'
s=p.read_text();changes=[]
def one(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b);changes.append(dict(before=a,after=b))
one("BASE=ROOT/'reports/m4-lockit-paired-provider'", "BASE=ROOT/'reports/m4-tree-original'")
one("VALIDATION=ROOT/'reports/m4-lockit-original/original-validation-r2/report.json'", "VALIDATION=ROOT/'reports/m4-tree-original/original125-validation-r1/report.json'")
one("VALIDATION_SHA='4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3'", "VALIDATION_SHA='5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'")
one("PREP=ROOT/'reports/m4-lockit-original/original-preparation-r4'", "PREP=ROOT/'reports/m4-tree-original/original125-preparation-r1'")
one("PREP_SHA='6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b'", "PREP_SHA='6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1'")
one("p=read(PREP/'report.json',PREP_SHA);pages=p['observed_pages'];need(len(pages)==43,'Exact original43 pages')", """p=read(PREP/'report.json',PREP_SHA)
 inherited=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b')
 p['Lockit_roots']=inherited['Lockit_roots'];p['Lockit_allocations']=inherited['Lockit_allocations'];p['order']=p['selected_order'];pages=p['observed_pages'];need(len(pages)==43 and len(p['order'])==125,'Exact original125 order and43 pages')
 review=read(ROOT/'reports/m4-tree-original/full-original-review-r3/report.json','a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260');need(review['passed']and review['original_validation_sha256']==VALIDATION_SHA,'Fresh complete final linked observer gate')""")
one("build=read(ROOT/'reports/m4-lockit-original/original-build-r3/build.json','3a2214354b280439342e5b128bf48d980d9f3fb8ac9aab88ac8d8e570ed693a6')", "build=read(ROOT/'reports/m4-tree-original/original125-build-r1/build.json','e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585')")
one("hooks=read(PREP/'lockit-hook-bindings.json')", "hooks=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json')")
one("index=len(owners);meta=words(reader.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin'),0,9)", """candidates=[]
     for name in reader.entries:
      if not(name.startswith(f'phase/{seq}/{phase}/lockit-allocation/')and name.endswith('/meta.bin')):continue
      candidate=words(reader.data(name),0,9)
      if candidate[2:5]==(entry,frame[3],request)and candidate[6:8]==(ai,pointer):candidates.append((int(name.split('/')[-2]),candidate))
     need(len(candidates)==1,'One actual current source CALL/API/generation owner metadata row');index,meta=candidates[0]""")
one("pin(__file__);passed=True", "pin(__file__);pin(ROOT/'tools/m4-lockit-paired-provider/original_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source.py');passed=True")
one("carried across124 phases", "carried across125 phases")
one("Original postRET is source-derived only.',original_validation_sha256", "Original postRET is source-derived only.',original_build_sha256='e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585',original_preparation_sha256=PREP_SHA,independent_compiled_original_sha256='a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260',reader_closed=True,original_validation_sha256")
out=Path(__file__).with_name('old4_source.py');assert not out.exists();out.write_text(s)
print(json.dumps(dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest(),changes=len(changes))))
