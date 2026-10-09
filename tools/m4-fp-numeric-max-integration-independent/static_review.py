"""Independent source/ABI review of shared numeric-max routing derivatives.

Imports only frozen root-owned metadata/layout reviewers. Author preparation,
comparators, fixture models and execution code are never imported.
"""
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
ANCESTORS={'4c19f0':'567fff4bf65edcc13b496194d46801282ce51fa5bc28b591fbf25e9b2c4ebc04','4c1a00':'3c30058705539810e74ae72a032c7e0146e02460de03a929f15bb679df7878d1','780c10f0':'b40b744f1d8b4930171878a93f723ec1571453d4f1dc938899ed771f2d3bf1f9'}
ALIASES={'__remill_read_memory_32':'mw34_nmx_read32','__remill_write_memory_32':'mw34_nmx_write32','__remill_read_memory_f32':'mw34_nmx_readf32','__remill_write_memory_f32':'mw34_nmx_writef32','__remill_function_call':'mw34_nmx_call','__remill_function_return':'mw34_nmx_return','__remill_fpu_exception_clear':'mw34_nmx_clear','__remill_fpu_exception_test':'mw34_nmx_test','mw34_numeric_body_entry':'mw34_nmx_body_entry','mw34_numeric_fld_commit':'mw34_nmx_fld_commit','mw34_numeric_fstp_commit':'mw34_nmx_fstp_commit'}

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);need(want is None or h==want,'Exact source identity '+str(p));need(str(p) not in PINS or PINS[str(p)]==h,'Conflicting identity');PINS[str(p)]=h;return p

def own(path,name,h):
    p=pin(path,h);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def reverse(text,entry):
    result=text
    for old,new in ALIASES.items():result=result.replace('@'+new+'(','@'+old+'(')
    result=result.replace('@mw34_nmx_entry_'+entry+'(','@mw34_numeric_entry_'+entry+'(')
    if entry=='4c19f0':
        need(result.count('call ptr @mw34_nmx_dispatch_body(')==1 and result.count('declare ptr @mw34_nmx_dispatch_body(')==1,'One actual wrapper CALL plus declaration routed')
        result=result.replace('@mw34_nmx_dispatch_body(','@sub_4c1a00(')
    need('@mw34_nmx_' not in result,'No unreviewed new native boundary')
    return result

def main(preparation,out):
    need(preparation.is_relative_to(ROOT/'reports/m4-fp-numeric-max-integration') and out.is_relative_to(ROOT/'reports/m4-fp-numeric-max-integration') and not out.exists(),'Private exact derivative input and fresh review output')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        pe=own(ROOT/'tools/analysis/pe.py','root_numeric_integration_pe','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        layout=own(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','root_numeric_existing_layout','6837acea5209e45ac6f2821b37f4d941bdd522c9ddbe320c9184378d609a5643')
        game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
        game=pe.PEImage(game_path.read_bytes());provider=pe.PEImage(provider_path.read_bytes())
        need(game.image_base==0x400000 and provider.image_base==0x780c0000,'Actual PE bases')
        def at(image,address,n):return image.read(image.rva_range(address-image.image_base,n)[0],n)
        owner=[(lib['library'],s) for lib in game.imports() for s in lib['symbols'] if s['iat_rva']+game.image_base==0x5bb4fc]
        symbol='?max@?$numeric_limits@M@std@@SAMXZ'
        need(len(owner)==1 and owner[0][0].casefold()=='msvcp50.dll' and owner[0][1]['name']==symbol and owner[0][1]['hint']==1544,'Exact game named MSVCP50 import')
        export=[e for e in provider.exports() if symbol in e['names']]
        need(len(export)==1 and export[0]['ordinal']==1545 and export[0]['rva']==0x10f0 and 'forwarder' not in export[0],'Exact named nonforwarded export')
        need(struct.unpack('<I',at(game,0x5e016c,4))[0]==0x4c19f0 and struct.unpack('<I',at(provider,0x78115004,4))[0]==0x7f7fffff,'Actual initializer table and binary32 constant')
        sources=[]
        for address,n,h in ((0x4c19f0,10,'1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc'),(0x4c1a00,117,'642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5')):
            need(hashlib.sha256(at(game,address,n)).hexdigest()==h,'Exact complete game source span');sources.append(dict(address=address,bytes=n,sha256=h))
        body=at(provider,0x780c10f0,7)
        need(body[0]==0xd9 and body[1]==5 and struct.unpack_from('<I',body,2)[0]==0x78115004 and body[6]==0xc3,'Actual FLD m32/RET operand and complete length')
        for address,filename,perm in ((0x780c1000,'provider-code-page.bin',0x60000000),(0x78115000,'provider-data-page.bin',0x40000000)):
            need(pin(preparation/filename).read_bytes()==at(provider,address,4096),'Whole actual provider owned page')
            need(any(s['virtual_address']<=address-provider.image_base and address-provider.image_base+4096<=s['virtual_address']+s['raw_size'] and s['characteristics']&0xe0000000==perm for s in provider.sections),'Actual source page permissions')
        decoder=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        command=[str(decoder),'-d','--x86-asm-syntax=intel','--start-address=0x780c10f0','--stop-address=0x780c10f7',str(provider_path)]
        decoded=subprocess.run(command,capture_output=True);need(decoded.returncode==0 and not decoded.stderr,'Fresh provider instruction decode')
        (out/'provider-decode.txt').write_bytes(decoded.stdout);pin(out/'provider-decode.txt')
        rows=[]
        for line in decoded.stdout.decode().splitlines():
            m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
            if m:
                pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(at(provider,pc,len(raw))==raw,'Fresh decode equals exact bytes');rows.append((pc,len(raw),m[3],m[4].strip()))
        need(rows==[(0x780c10f0,6,'fld','dword ptr [0x78115004]'),(0x780c10f6,1,'ret','')],'Complete actual provider leaf decode')
        irs=[];mutations=[]
        for entry,h in ANCESTORS.items():
            old=pin(ROOT/'reports/m4-fp-numeric-max/repaired-r2'/f'{entry}-repaired.ll',h).read_text()
            path=pin(preparation/f'{entry}-runtime.ll');new=path.read_text()
            need(reverse(new,entry)==old,'Entire derivative reverses to accepted literal IR '+entry)
            types,cache=layout.layout_model(new);oldtypes,oldcache=layout.layout_model(old)
            need(cache['%struct.State'][:2]==(3504,8),'Whole independently computed State ABI')
            need(len(types)==34 and types==oldtypes and all(cache[t]==oldcache[t] for t in types),'All34 named layouts unchanged')
            irs.append(dict(entry=entry,path=str(path),sha256=sha(path),named_layouts=len(types),complete_literal_inverse=True))
            for before,after in (("%struct.State = type", "%struct.State = BAD"),("target datalayout", "WRONG datalayout")):
                bad=new.replace(before,after,1)
                need(bad!=new and reverse(bad,entry)!=old,'Own coherent static corruption must reject');mutations.append(dict(entry=entry,change=before,rejected=True))
        for p,h in ((ROOT/'tools/m4-runtime/runtime.hpp','41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536'),(ROOT/'tools/m4-runtime/runtime.cpp','48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')):pin(p,h)
        # The imported frozen root reviewer pins its own oracle/tool identities.
        for p,h in layout.PINS.items():pin(p,h)
        report=dict(passed=True,scope='Independent exact source/import/export/page/layout/IR derivative review only; native execution and connected admission pending',game_import=owner[0],raw_game_IAT=struct.unpack('<I',at(game,0x5bb4fc,4))[0],provider_export=export[0],source_spans=sources,provider_leaf_sha256=hashlib.sha256(body).hexdigest(),complete_derivatives=irs,own_static_corruption_controls=mutations,shared_r9_unchanged=True,original_process_executed=False,author_executor_or_model_imported=False,whole_M4_complete=False)
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'),native_admitted=False)))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
