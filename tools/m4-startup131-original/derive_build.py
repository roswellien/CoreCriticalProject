from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
base=R/'tools/m4-startup130-original/build.ps1';p=T/'build.ps1';assert not p.exists()
s=base.read_text()
assert s.count("reports/m4-startup130-original")==1
s=s.replace('reports/m4-startup130-original','reports/m4-startup131-original')
assert s.count('phases=780;roots=130')==1
s=s.replace('phases=780;roots=130','phases=786;roots=131')
assert s.count('combined_pages=46;direct_primary')==1
s=s.replace('combined_pages=46;direct_primary','combined_pages=46;MFC_domain_extra_regions=12;constructor_prerequisite_pages=1;direct_primary')
p.write_text(s)
q=T/'build-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes=['Assigned additive full131 namespace','131 roots /786 phases metadata','Separate measured MFC/constructor export extent metadata'],compiler_and_flags_unchanged=True),indent=2)+'\n')
print(p)
