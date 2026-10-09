"""Additive canonical-byte admission derivative; all ancestors remain literal."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
carry=BASE/'native-preparation-repair-r2';host=ROOT/'reports/m4-fp-numeric-max-host-boundary/derivation-r4'
assert sha(carry/'preparation.json')=='228869addb39a6e7436e0f7e2c035e929d985dad3e190a63f6cfda6370470703'
assert sha(BASE/'pre-boolean-domain-repair-r1/manifest.json')=='41dde192802e2626ce33f5a1d138500ca72a3eb664551fa347b4242ac7c4d612'
pins={}
for p in (carry/'preparation.json',carry/'pins.json',BASE/'pre-boolean-domain-repair-r1/manifest.json'):
 pins[str(p)]=sha(p)
oldpins=json.loads((carry/'pins.json').read_text())['files']
for name in ('session.hpp','native.cpp'):
 p=carry/name;assert sha(p)==oldpins[str(p)];q=out/(name+'.carry-ancestor');q.write_bytes(p.read_bytes());pins[str(p)]=sha(p);pins[str(q)]=sha(q)
seal=ROOT/'reports/m4-fp-numeric-max-host-boundary/author-review-r1'
assert sha(seal/'report.json')=='efe696cfa1cf4927aa6a4dc3846be956d7caf6bbc8d8e3e2a30bc8267af3912a'
hpins=json.loads((seal/'pins.json').read_text())['files']
p=host/'native.cpp';assert sha(p)==hpins[str(p)];q=out/'native.cpp.host-ancestor';q.write_bytes(p.read_bytes());pins[str(p)]=sha(p);pins[str(q)]=sha(q)
s=(carry/'session.hpp').read_text();needle='void admit_fp(){auto sw=status(s_),top=(sw>>11)&7;';assert s.count(needle)==1
guard='void admit_fp(){for(const auto byte:std::array<std::uint8_t,11>{s_.sw.ie,s_.sw.de,s_.sw.ze,s_.sw.oe,s_.sw.ue,s_.sw.pe,s_.sw.sf,s_.sw.c0,s_.sw.c1,s_.sw.c2,s_.sw.c3})if(byte>1)deny("Noncanonical FP shadow flag byte rejected");auto sw=status(s_),top=(sw>>11)&7;'
s=s.replace(needle,guard);(out/'session.hpp').write_text(s);pins[str(out/'session.hpp')]=sha(out/'session.hpp')
template=Path(__file__).with_name('canonical_controls.inc');pins[str(template)]=sha(template)
pins[str(Path(__file__))]=sha(__file__)
report=dict(passed=True,changes=[
 'Separate canonical admission: all eleven FP shadow bytes must be 0 or 1 before any status projection in admit_fp; malformed values are rejected, never normalized',
 'Inherited separately measured incoming PE/C1 domain extension',
 'Inherited separately measured typed FLD no-overflow C1=0 commit'],
 unchanged='Required Session.invoke numerical boundary, exact guest IR, arithmetic, original/runtime/provider sources, checked memory, State/routes/events/source ownership',
 controls='11 fields x values2/3/255 x coherent/incoherent softwareFX =66 malformed admissions and66 corrected poisoned retries per optimization; numerical captures precede cleanup',
 scope='Native unit and offline frozen ORIGINAL BEFORE replay only. No original process execution or connected27/full startup admission',files=pins,original_executed=False,whole_M4_complete=False)
(out/'preparation.json').write_text(json.dumps(report,indent=2)+'\n');gate=sha(out/'preparation.json');pins[str(out/'preparation.json')]=gate
n=(carry/'native.cpp').read_text();oldgate=json.loads((carry/'preparation.json').read_text())
carry_gate=sha(carry/'preparation.json');assert n.count(carry_gate)==1;n=n.replace(carry_gate,gate)
start=n.index('int main(int argc,char**argv)');n=n[:start]+template.read_text()+'\n'+n[start:]
needle='schema(dir);';assert n.count(needle)==1;n=n.replace(needle,needle+'canonical_controls(std::as_bytes(std::span{game}),std::as_bytes(std::span{provider}),ni::Proof{old::sha256(object),"'+gate+'"},dir);')
(out/'native.cpp').write_text(n);pins[str(out/'native.cpp')]=sha(out/'native.cpp')
legacy=(host/'native.cpp').read_text();needle='73a4fa0b37415a7510775d4a1939872a598168b92cc4f9b5bcf581f97e5f312e';assert legacy.count(needle)==1;legacy=legacy.replace(needle,gate)
(out/'legacy.cpp').write_text(legacy);pins[str(out/'legacy.cpp')]=sha(out/'legacy.cpp')
(out/'generator-source.py').write_bytes(Path(__file__).read_bytes());pins[str(out/'generator-source.py')]=sha(out/'generator-source.py')
(out/'canonical_controls.inc').write_bytes(template.read_bytes());pins[str(out/'canonical_controls.inc')]=sha(out/'canonical_controls.inc')
(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps({'preparation_sha256':gate,'pins_sha256':sha(out/'pins.json')}))
