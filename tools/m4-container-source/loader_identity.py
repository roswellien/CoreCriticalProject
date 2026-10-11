"""Authenticate real32 post-DLL-init MFC borrowed data and game ordinals."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(x,w):
 if not x:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh loader identity receipt');out.mkdir(parents=True);files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical loader input');files[str(p)]=v;return p
 probe=BASE/'loader-r1';seen=json.loads(pin(probe/'loader.json').read_text(encoding='utf-8-sig'));need(seen['passed']and seen['process_bits']==32,'Genuine32 post-DllMain observation')
 p=pin(ROOT/'tools/analysis/pe.py');sp=importlib.util.spec_from_file_location('container_loader_pe',p);P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)
 mfcpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');crtpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');gamepath=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');mfc=P.PEImage(mfcpath.read_bytes());game=P.PEImage(gamepath.read_bytes())
 need(Path(seen['MFC_path']).resolve()==mfcpath and Path(seen['CRT_path']).resolve()==crtpath and seen['MFC_base']==mfc.image_base==0x5f400000 and seen['CRT_base']==0x78000000,'Actual exact staged DLL paths and preferred bases')
 need(seen['nil_address']==0x5f4ccb54 and seen['page']==0x5f4cc000 and seen['page_bytes']==4096 and seen['source_allocation_base']==mfc.image_base and seen['source_state']==4096 and seen['source_type']==0x1000000 and seen['source_protect']==4,'Committed initialized data page in exact MFC owning image')
 off,_=mfc.rva_range(0xcc000,4096);raw=mfc.read(off,4096);loaded=pin(probe/'loaded-data-page.bin').read_bytes();need(len(loaded)==4096,'Whole actual loaded page');nil=struct.unpack_from('<I',loaded,0xb54)[0];need(nil==seen['nil_value']==struct.unpack_from('<I',raw,0xb54)[0]==0x5f4cecec,'Source read actual initialized borrowed pointer DWORD equals physical MFC static nil data pointer')
 need(seen['pointee_owner_base']==seen['pointee_allocation_base']==mfc.image_base and Path(seen['pointee_owner_path']).resolve()==mfcpath and seen['pointee_state']==4096 and seen['pointee_type']==0x1000000 and seen['pointee_bytes_read']==0,'Borrowed pointee attributed by memory/module identity only; no pointee read or mapping admission')
 exports={e['ordinal']:e for e in mfc.exports()};imports={game.image_base+s['iat_rva']:dict(library=g['library'],**s)for g in game.imports()for s in g['symbols']};bindings=[]
 for ordinal,slot,target in ((540,0x5bb454,0x5f4020b4),(825,0x5bb4c8,0x5f401782)):
  need(seen['loaded_ordinal'+str(ordinal)]==mfc.image_base+exports[ordinal]['rva']==target,'Actual GetProcAddress ordinal matches physical staged MFC export');imp=imports[slot];need(imp['ordinal']==ordinal and imp['library'].lower()=='mfc42.dll','Exact physical game owning import identity');offset,_=game.rva_range(slot-game.image_base,4);rawiat=struct.unpack_from('<I',game.data,offset)[0];need(rawiat==0x80000000+ordinal,'Exact original ordinal IAT DWORD');bindings.append(dict(ordinal=ordinal,game_IAT=slot,raw_game_IAT=rawiat,actual_loader_export=target,export=exports[ordinal],module_sha256=sha(mfcpath)))
 changes=[dict(offset=i,address=0x5f4cc000+i,raw=a,loaded=b)for i,(a,b)in enumerate(zip(raw,loaded))if a!=b];(out/'page-differences.json').write_text(json.dumps(changes,indent=2)+'\n');pin(out/'page-differences.json');(out/'raw-data-page.bin').write_bytes(raw);pin(out/'raw-data-page.bin')
 for p in(probe/'probe.exe',probe/'probe.obj',probe/'compile.log',ROOT/'tools/m4-container-source/loader_probe.cpp',ROOT/'tools/m4-container-source/build_loader.ps1',Path(__file__),Path(sys.executable)):pin(p)
 report=dict(passed=True,schema='mw34-container-genuine-original32-loader-input-v1',scope='Actual original32 exact staged LoadLibrary initialization, MFC540/825 exported identities, physical game owning ordinal slots, and full source-read page/nil pointer provenance only',MFC_module_sha256=sha(mfcpath),borrowed_data=dict(address=0x5f4ccb54,page=0x5f4cc000,raw_value=nil,post_DllMain_value=nil,raw_page_sha256=hashlib.sha256(raw).hexdigest(),loaded_page_sha256=hashlib.sha256(loaded).hexdigest(),whole_page_changed_bytes=len(changes),pointee_module_base=seen['pointee_owner_base'],pointee_module_sha256=sha(mfcpath),pointee_read=False,pointee_page_admitted=False),bindings=bindings,original_loader_executed=True,MFC_DllMain_initialization_executed=True,game_called=False,constructor_called=False,freeNULL_called=False,root_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),nil=hex(nil),page_changes=len(changes),bindings=bindings)))
if __name__=='__main__':main(sys.argv[1])
