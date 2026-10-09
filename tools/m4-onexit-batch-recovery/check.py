"""Check current static preparation against actual admitted image bytes."""
from pathlib import Path
import argparse, hashlib, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage

def require(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('report');ap.add_argument('expected_sha');ap.add_argument('output');a=ap.parse_args()
 p=Path(a.report).resolve();d=p.parent;o=Path(a.output).resolve()
 require(sha(p)==a.expected_sha,'Exact preparation report identity')
 require(o.parent==ROOT/'reports/m4-onexit-batch-recovery' and not o.exists(),'Fresh check output')
 report=load(p);pins=load(d/'pins.json')['files']
 for file,h in pins.items():require(sha(file)==h,'Pinned current physical artifact/source changed')
 require(report['passed_static_recovery'] and report['root_count']==26 and report['callback_targets']==26 and report['roots_admitted']==0 and not report['native_executed'] and not report['game_launched'],'Static scope must not credit execution')
 game=PEImage((ROOT/'MW3/Mech3.exe').read_bytes());crt=PEImage((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
 counts={};checked=0
 for name,image in [('game-normal-graphs.json',game),('callback-graphs.json',game),('provider-graphs.json',crt)]:
  graphs=load(d/name);unique={}
  for node in graphs.values():
   rows=node['instructions'];require(node['execution_or_admission'] is False,'Graph execution admission must remain false')
   for r in rows:
    raw=bytes.fromhex(r['bytes']);off,_=image.rva_range(r['pc']-image.image_base,len(raw))
    require(raw==image.read(off,len(raw)) and len(raw)==r['size'],'Exact literal original row bytes')
    if r['pc']in unique:require(unique[r['pc']]==r,'Overlapping entry body row disagreement')
    unique[r['pc']]=r;checked+=1
   require(hashlib.sha256(b''.join(bytes.fromhex(r['bytes'])for r in rows)).hexdigest()==node['instruction_bytes_sha256'],'Body byte census changed')
   bypc={r['pc']:r for r in rows}
   for call in node['direct_calls']:
    r=bypc[call['site']];raw=bytes.fromhex(r['bytes']);require(len(raw)==5 and raw[0]==0xe8,'Exact normal CALL encoding')
    require((r['pc']+5+struct.unpack('<i',raw[1:])[0])&0xffffffff==call['target'],'Encoded direct CALL destination')
    require(r['pc']+5==call['return_pc'],'Real source CALL return PC')
  counts[name]=dict(entries=len(graphs),unique_instructions=len(unique),unique_bytes=sum(r['size']for r in unique.values()))
 roots=load(d/'registration-roots.json');normal=load(d/'game-normal-graphs.json');callbacks=load(d/'callback-graphs.json')
 require(len({r['entry']for r in roots})==26 and [r['slot']for r in roots]==sorted(r['slot']for r in roots),'26 distinct actual table roots in relative order')
 for root in roots:
  off,_=game.rva_range(root['slot']-game.image_base,4);require(game.read(off,4)==struct.pack('<I',root['entry']),'Original table slot/root')
  reg=root['registration'];require(str(reg['callback'])in callbacks,'Registered callback has separate static dependency record')
  rows={r['pc']:r for e in root['normal']['local_entries']for r in normal[str(e)]['instructions']}
  prior=rows[reg['push_pc']];require(bytes.fromhex(prior['bytes'])==b'\x68'+struct.pack('<I',reg['callback']),'Literal PUSH code-address callback')
  call=rows[reg['CALL_pc']];require(prior['pc']+prior['size']==call['pc'],'Actual literal passed immediately to wrapper')
  require((call['pc']+5+struct.unpack('<i',bytes.fromhex(call['bytes'])[1:])[0])&0xffffffff==0x5ac140,'Actual registry wrapper destination')
  require(not root['callback_execution_claimed'] and not root['normal']['FS_sites'] and not root['normal']['unresolved_controls'],'Normal root scope and callback separation')
 inp=load(d/'registry-inputs.json');require(inp['provider_table_slot']['va']==0x78037c18 and inp['provider_table_slot']['initial_hex']==struct.pack('<I',0x78004482).hex(),'Exact initialized-table producer cell')
 require([r['pc']for r in inp['game_sentinel_rows']]==[0x5ac3d8,0x5ac3e2],'Original sentinel source origins')
 apis=load(d/'new-api-contracts.json');require([(x['name'],x['pc'],x['slot'],x['argc'])for x in apis]==[('HeapSize',0x780015b5,0x7802e1dc,3),('HeapReAlloc',0x78011c27,0x7802e0b4,4)],'New actual API caller contracts')
 term=load(d/'termination-frontier.json');require(any(r['pc']==0x78005560 and r['row']['operands']=='eax'for r in term['core']['unresolved_controls']),'Actual unresolved reverse callback CALL remains open')
 plan=load(d/'whole-batch-contract.json');require(plan['roots']==26 and not plan['native_execution'] and not plan['initializer_count_credit'] and not plan['full_startup'],'No invented native/root/attach credit')
 o.mkdir(parents=True);result=dict(passed=True,scope='Static preparation physical source/table/callback separation check only',preparation=dict(path=str(p),sha256=a.expected_sha),
  physical_pins_rehashed=len(pins),literal_rows_checked=checked,graph_counts=counts,roots=26,callback_targets=26,native_executed=False,roots_admitted=0,source=dict(path=str(Path(__file__).resolve()),sha256=sha(Path(__file__).resolve())))
 (o/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 (o/'pins.json').write_text(json.dumps(dict(files={**pins,str(d/'pins.json'):sha(d/'pins.json'),str(Path(__file__).resolve()):result['source']['sha256'],str(o/'report.json'):sha(o/'report.json')}),indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(passed=True,report_sha256=sha(o/'report.json'),literal_rows_checked=checked,physical_pins_rehashed=len(pins))))

if __name__=='__main__':main()
