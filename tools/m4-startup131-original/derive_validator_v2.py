from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent
base=T/'mfc_phase.py';p=T/'mfc_phase_v2.py';assert not p.exists();s=base.read_text()
old=" values={key:retain(key)for key in keys}\n targets="
new=" values={key:retain(key)for key in keys}\n raw_path=out/'actual-MFC-inputs'/(stem+'.bin');raw_path.parent.mkdir(parents=True,exist_ok=True);raw_path.write_bytes(data);pin(raw_path)\n for address in(0x5cd000,0x5e3000,0x5e9000):\n  for side in('before','after'):retain(stem+f'/extra-{side}/{address}.bin')\n targets="
assert s.count(old)==1;s=s.replace(old,new)
old="row['whole_provider_hex']=raw.hex()";assert s.count(old)==1
s=s.replace(old,"row['whole_provider_hex']=raw.hex();row['whole_provider_before_write_hex']=raw.hex()")
old="FX_before_hex=data[116:628].hex(),FX_after_hex=";assert s.count(old)==1
s=s.replace(old,"raw_phase_record=str(raw_path),raw_phase_record_sha256=pin_digest_placeholder,FX_before_hex=data[116:628].hex(),FX_after_hex=")
s=s.replace('raw_phase_record_sha256=pin_digest_placeholder','raw_phase_record_sha256=__import__(\'hashlib\').sha256(data).hexdigest()')
p.write_text(s)
base2=T/'validate.py';p2=T/'validate_v2.py';assert not p2.exists();s=base2.read_text();assert s.count('from mfc_phase import')==1;s=s.replace('from mfc_phase import','from mfc_phase_v2 import');assert s.count("/'mfc_phase.py'")==1;s=s.replace("/'mfc_phase.py'","/'mfc_phase_v2.py'");p2.write_text(s)
q=T/'validator-v2-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),validator_base=str(base2),validator_base_sha256=hashlib.sha256(base2.read_bytes()).hexdigest(),validator_generated=str(p2),validator_generated_sha256=hashlib.sha256(p2.read_bytes()).hexdigest(),changes=['Retain each current MFC actual phase356992 record and3wholeextraBEFORE/AFTERsourcepages while the same sole reader is open','Expose exact bounded-source-compatible wholeprovider alias field','Pin same current MFC artifact raw record identity'],new_reader_opened=False),indent=2)+'\n')
print(p2)
