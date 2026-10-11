"""Seal only physically reached109 fixed-page fields requiring typed relations."""
from pathlib import Path
import hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 interface=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());program={r['pc']:r for r in json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes())['instructions']};p=pin(ROOT/'tools/analysis/pe.py');s=importlib.util.spec_from_file_location('field_original_PE',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=m.PEImage(game);fields=[]
 for binding in interface:
  if not binding['publication']:continue
  pc=binding['publication_PC'];row=program[pc];assert row['mnemonic']=='mov';dest,source=row['decoded_operands'];assert dest['kind']=='memory'and dest['bits']==32 and source['kind']=='register';off,_=pe.rva_range(pc-0x400000,row['width']);assert game[off:off+row['width']]==bytes.fromhex(row['bytes_hex']);fields.append(dict(root=binding['root'],CALL_pc=binding['CALL_pc'],field=binding['publication'],width=4,write_PC=pc,object=binding['object'],requested_size=binding['requested_size'],operand=row['operands'],bytes_hex=row['bytes_hex'],decoded_destination=dest,decoded_source=source,activation='After exact root completes; raw pointer from independent actual API/root/CALL identity, then exact carry'))
 assert {r['field']for r in fields}=={0x60b888,0x609990,0x60b520}
 read,write=program[0x4d4914],program[0x4d4922];assert read['mnemonic']==write['mnemonic']=='mov';assert read['decoded_operands'][0]['register']=='al'and read['decoded_operands'][1]['bits']==8 and read['decoded_operands'][1]['displacement']==7;assert write['decoded_operands'][0]['bits']==8 and write['decoded_operands'][0]['displacement']==4 and write['decoded_operands'][1]['register']=='al'
 for row in(read,write):off,_=pe.rva_range(row['pc']-0x400000,row['width']);assert game[off:off+row['width']]==bytes.fromhex(row['bytes_hex'])
 headers=[dict(root=0x4d4830,object=0x60b518,field=0x60b51c,width=1,read_PC=0x4d4914,write_PC=0x4d4922,read_bytes=read['bytes_hex'],write_bytes=write['bytes_hex'],read_operand=read['operands'],write_operand=write['operands'],actual_read_address=0x200017eb,input_provenance='Each branch authentic source BEFORE stack byte at200017EB, with no current-root store before the exact local read; native whole persistent source stack independently computed. Complete raw values and exact carry remain observed.',activation='Only after root4D4830 completes',whole_game_consumer_liveness_claimed=False)]
 pin(__file__);report=dict(passed=True,scope='Static exact three reached fixed-page allocation publications and one literal local-byte copy requiring109 typed relation; no arbitrary page masks or dynamic handler credit',pointer_fields=fields,header_fields=headers,whole_game_liveness_proven=False,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
