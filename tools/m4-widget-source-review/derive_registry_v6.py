"""Add the omitted accepted literal onexit source to registry5, immutably."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,label):
 if not v:raise ValueError(label)
def main(name):
 out=R/'reports/m4-widget-source-review'/name;need(not out.exists(),'Fresh source-program merge receipt');out.mkdir(parents=True)
 base=R/'tools/m4-widget-source-review/compare_registry_v5.py';need(sha(base)=='4d37f14eeed7547d31c1734feb3dab3b22ddc776ffa47bf4c0fe7588a5bd1c4a','Exact immutable parser5')
 interface=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json'
 callbacks=R/'reports/m4-onexit-review/callbacks-r1/callbacks.json'
 ih='9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d';ch='3c0a5fab10ec834c8e027ed88a8443b7d63d559c151d40ade6a045a71ce1565d'
 need(sha(interface)==ih and sha(callbacks)==ch,'Exact accepted original-byte provider source and callback interfaces')
 data=json.loads(interface.read_bytes());need(data['schema']=='mw34-onexit-independent-provider-source-v1'and not data['AFTER_machine_seed'],'Original-byte source program only')
 before="  G=C.load(R/'reports/m4-font479590-original/source-preparation-r1/game_model.py','widget_registry_literal');program,callbacks=G.source_program();sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as responses_module"
 after=before+"\n  provider=read(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','"+ih+"');need(provider['schema']=='mw34-onexit-independent-provider-source-v1'and not provider['AFTER_machine_seed'],'Frozen original-byte literal provider closure')\n  for row in provider['instructions']:\n   pc=row['pc'];need(pc not in program or program[pc]==row,'Identical shared literal game/provider row');program[pc]=row\n  provider_callbacks=read(R/'reports/m4-onexit-review/callbacks-r1/callbacks.json','"+ch+"')['State_offsets_by_original_PC']\n  for pc,offsets in provider_callbacks.items():\n   pc=int(pc);offsets=tuple(offsets);need(pc not in callbacks or callbacks[pc]==offsets,'Identical shared provider undefined callback attribution');callbacks[pc]=offsets\n  need(0x78004a36 in program,'Literal onexit source entry exists before interpreter starts')"
 text=base.read_text();need(text.count(before)==1,'One exact source construction site');text=text.replace(before,after,1)
 tool=R/'tools/m4-widget-source-review/compare_registry_v6.py';need(not tool.exists(),'Fresh literal closure6');tool.write_text(text)
 need(tool.read_text().replace(after,before,1)==base.read_text(),'Exact inverse restores all source/API/equality behavior of parser5')
 # Independently bind the 1404 accepted rows to the physical CRT PE again.
 binary=R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=binary.read_bytes();off=struct.unpack_from('<I',pe,0x3c)[0]
 need(pe[off:off+4]==b'PE\0\0','Physical source CRT PE')
 count=struct.unpack_from('<H',pe,off+6)[0];opt=struct.unpack_from('<H',pe,off+20)[0];imagebase=struct.unpack_from('<I',pe,off+24+28)[0]
 sections=[]
 for n in range(count):
  s=off+24+opt+40*n;vs,rva,rs,raw=struct.unpack_from('<4I',pe,s+8);sections.append((rva,rs,raw))
 for row in data['instructions']:
  rva=row['pc']-imagebase;found=[s for s in sections if s[0]<=rva and rva+row['width']<=s[0]+s[1]];need(len(found)==1,'Exact CRT section at '+hex(row['pc']));s=found[0];start=s[2]+rva-s[0];need(pe[start:start+row['width']].hex()==row['bytes_hex'],'Whole original instruction '+hex(row['pc']))
 changes=out/'changes.json';changes.write_text(json.dumps(dict(before=before,after=after),indent=2)+'\n')
 files={str(p.resolve()):sha(p) for p in(base,tool,interface,callbacks,binary,changes,Path(__file__),Path(sys.executable),R/'reports/m4-widget-native/source-registry-r2/report.json',R/'reports/m4-widget-source-review/registry-parser-preparation-r1/report.json')}
 report=dict(passed=True,scope='Exact additive1404-row accepted literal provider/callback merge omitted by original prepared comparer; no response, numerical, AFTER or native resource bytes seed source',
  base_sha256=sha(base),comparison=str(tool),comparison_sha256=sha(tool),provider_instruction_rows=len(data['instructions']),
  provider_callback_PCs=len(json.loads(callbacks.read_bytes())['State_offsets_by_original_PC']),
  exact_inverse_restores_base_source=True,whole_physical_provider_rows_verified=True,
  evaluator_or_equality_changed=False,native_worker_rerun=False,archive_reader_opened=False,execution_claimed=False,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),comparison=str(tool),comparison_sha256=sha(tool),passed=True)))
if __name__=='__main__':main(sys.argv[1])
