"""Check the enlarged suffix against the old SPI volatile-field policy."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 interface=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes());order=interface['selected_order'];index=next(i for i,r in enumerate(order)if r['entry']==0x482cf0);assert index==25 and order[index+1]['entry']==0x49d5c0
 program={r['pc']:r for r in interface['instructions']}
 exact=[(0x49d5d0,'push','ecx'),(0x49d5d1,'mov','al, byte ptr [esp + 0x3]'),(0x49d5d5,'mov','byte ptr [0x6099e8], al')]
 for pc,op,args in exact:assert (program[pc]['mnemonic'],program[pc]['operands'])==(op,args)
 PE_path=pin(ROOT/'tools/analysis/pe.py');sp=importlib.util.spec_from_file_location('suffix_source_PE',PE_path);PE=importlib.util.module_from_spec(sp);sp.loader.exec_module(PE);image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(image)
 for pc,_,_ in exact:
  r=program[pc];off,_=pe.rva_range(pc-0x400000,r['width']);assert image[off:off+r['width']]==bytes.fromhex(r['bytes_hex'])
 dpath=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');s=importlib.util.spec_from_file_location('suffix_archive',dpath);D=importlib.util.module_from_spec(s);s.loader.exec_module(D);report=json.loads(pin(ROOT/'reports/m4-onexit-source/original-run-r4/report.json','da0fd8d0bd3c1c0b4e57bc7a8b33875d33020aa8ab240cfd5d011b247620fe0e').read_bytes());reader=D.DirectSet(report['original_capture'],pin)
 facts=[]
 try:
  for sequence in range(6):
   spi=reader.data(f'phase/{sequence}/{index}.bin');consumer=reader.data(f'phase/{sequence}/{index+1}.bin');ecx=struct.unpack_from('<I',spi,80)[0];assert struct.unpack_from('<I',consumer,40)[0]==ecx
   # Original page order: 609000 is extra page index22, AFTER memory121060.
   actual=consumer[121060+22*4096+0x9e8];assert actual==ecx>>24
   service=spi[240564:241776];assert struct.unpack_from('<I',service,44)[0]==ecx
   facts.append(dict(sequence=sequence,actual_SPI_return_ECX=ecx,carried_constructor_ECX=ecx,source_byte=(ecx>>24),actual_whole_page_byte=actual,native_representative_ECX=0,native_source_derived_byte=0))
 finally:reader.close()
 out.mkdir(parents=True);pin(__file__)
 result=dict(passed=False,inspection_complete=True,scope='Enlarged selected28-root suffix after SPI; old no-consumer representative policy fails at a literal new constructor',
             SPI_phase=index,suffix_roots=28,first_consumer_root=0x49d5c0,source_flow=[program[p]for p,_,_ in exact],destination=0x6099e8,
             original_facts=facts,consumer_type='High ECX byte copied through a source PUSH/local-byte read into a global byte',
             actual_original_retained=True,blanket_mask_allowed=False,source_or_native_modified=False,whole_game_liveness=False,
             required_resolution='Explicit consumed volatile-field/derived-byte contract or corrected service compatibility; the previous 13-root no-consumer finding cannot widen to54',files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(inspection_complete=True,policy_passed=False,report_sha256=sha(out/'report.json'),root=hex(0x49d5c0),byte=hex(facts[0]['source_byte']))))
if __name__=='__main__':main(sys.argv[1])
