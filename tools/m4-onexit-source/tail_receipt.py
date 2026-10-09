"""Independent physical attribution and source interface for one additive tail."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(name,p):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-onexit-source'/name;need(not out.exists(),'Fresh supplemental receipt');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Pinned tail input '+str(p));pins[str(p)]=v;return p
 lift=ROOT/'reports/m4-onexit-source/tail-lift-r1';d=json.loads(pin(lift/'report.json','58085b78a8c4b646bf6bda9b65f870bff626a438b6ae965ee8cc06d9f7a9d845').read_bytes());need(d['passed'],'Tail compiled')
 iface=json.loads(pin(ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json','3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3').read_bytes());rows={r['pc']:r for r in iface['instructions'] if 0x42a570<=r['pc']<0x42a586};need(len(rows)==10,'Exact recovered contract rows')
 C=load('tail_original_callbacks',pin(ROOT/'tools/m4-crt-locale-batch-recovery/callbacks.py'))
 S=load('tail_physical_coff',pin(ROOT/'tools/m4-onexit-source/symbol_attribution_v2.py'))
 b=d['source_bodies']['f_42a570'];entry=b['entry'];host=pin(lift/'f_42a570-host.ll',b['host_sha256']);symbol='mw34_onexit_game_f_42a570_body'
 need(re.search(r'^define ptr @'+symbol+r'\(ptr noalias %state, i32 %program_counter, ptr noalias %memory\)',host.read_text(),re.M),'Actual i32PC body signature')
 pre=pin(lift/'f_42a570-pre.ll');guest=pin(lift/'f_42a570-baseline.ll');calls,mapping=C.recover(C.function(pre.read_text(),entry),C.function(guest.read_text(),entry),entry,rows)
 need([(c['pc'],c['State_offsets'])for c in calls]==[(0x42a579,[2069])],'Literal tail XOR undefined AF')
 objects={};argv=[]
 for level in ('O0','O2'):
  obj=pin(b['objects'][level]['path'],b['objects'][level]['sha256']);objects[level]=dict(path=str(obj),sha256=sha(obj),**S.coff_definition(obj,symbol));argv.append(str(obj))
 nm=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-nm.exe');r=subprocess.run([str(nm),'--format=posix','--print-file-name','--defined-only',*argv],capture_output=True,timeout=30,creationflags=0x08000000);need(r.returncode==0,'Physical tail nm');(out/'physical-defined-symbols.txt').write_bytes(r.stdout)
 for level,o in objects.items():need(sum(x.startswith(o['path']+': '+symbol+' T ')for x in r.stdout.decode().splitlines())==1,'Independent nm confirms tail')
 old=ROOT/'reports/m4-onexit-source/lifts-r4';old_d=json.loads(pin(old/'report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e').read_bytes());preserved=[]
 for key in ('f_586d70','f_586db0'):
  oldbody=old_d['source_bodies'][key];source=pin(old/(key+'-source.bin'),oldbody['source_sha256']);exact=b''.join(bytes.fromhex(x['bytes'])for x in oldbody['instructions'] if x['pc']>=oldbody['entry']);need(source.read_bytes()[:len(exact)]==exact,'Old reachable entry mov+jump bytes exact')
  for level in ('O0','O2'):pin(oldbody['objects'][level]['path'],oldbody['objects'][level]['sha256'])
  preserved.append(dict(entry=oldbody['entry'],entry_bytes=exact.hex(),entry_span=len(exact),lift_input_bytes=len(source.read_bytes()),tail_target=entry,reachable_entry_bytes_unchanged=True,lower_shared_tail_not_in_entry_relative_input=True))
 manifest=[dict(entry=entry,symbol=symbol,objects=objects,bridges=b['bridges'],undefined_calls=len(calls),FP=False,research_terminal=None)]
 (out/'dispatch.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'declarations.hpp').write_text('#pragma once\nextern "C" void* '+symbol+'(void*, unsigned int, void*);\n')
 (out/'instruction-contracts.json').write_text(json.dumps(dict(instructions=list(rows.values())),indent=2)+'\n');(out/'callbacks.json').write_text(json.dumps(dict(State_offsets_by_original_PC={str(c['pc']):c['State_offsets']for c in calls},bodies={'f_42a570':dict(entry=entry,callback_sites=calls,source_marker_map=mapping)}),indent=2)+'\n')
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():
  if p.is_file():pin(p)
 report=dict(passed=True,scope='One additive22-byte shared tail AMD64 body and source contract; no initializer credit',tail_entry=entry,tail_end=0x42a586,instructions=10,source_bytes=22,body_count=1,physical_COFF_count=2,dispatch_manifest=manifest,original64_preserved=True,old_reachable_entry_witnesses=preserved,metadata_source_contains_negative_offset_slices=True,whole_M4_complete=False,native_execution=False,initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),dispatch_sha256=sha(out/'dispatch.json'),callbacks_sha256=sha(out/'callbacks.json'))))
if __name__=='__main__':main(sys.argv[1])
