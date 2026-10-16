"""Literal MSVCRT DLL-attach lifts for the heap carry: _CRTDLL_INIT through its _mtinit call
site, _mtinit, _mtinitlocks, calloc and _initptd. Source-only (no execution).

Each span is cut from the exact staged MSVCRT.DLL (SHA pinned) at whole-instruction
boundaries and lifted with the same remill lifter, semantics and lowering as
tools/m4-crt-allocation/lift.py (namespace mw34_attach_ only).
Usage: python -B lift_attach.py lifts-rN
"""
import os,ctypes as c, hashlib, json, re, subprocess, sys, struct
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
PROVIDER=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
IMAGES={'msvcrt':(PROVIDER,PROVIDER_SHA),'game':(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),
        'mfc42':(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),
        'msvcp50':(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),
        'mech3msg':(ROOT/'MW3/Mech3Msg.dll','8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c'),
        # staged Indeo IV50 codec rebased to 0x11000000 (rebase_image.py)
        'ir50':(ROOT/'local/mw3-staged/derived/Ir50_32.base11000000.dll','9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f')}
# (component, first byte, end byte): end is the first byte NOT lifted (an instruction start).
SPANS=(('attach',0x780017fd,0x7800187d),('mtinit',0x78003b98,0x78003bf4),('mtinitlocks',0x78003bf4,0x78003c1d),
       ('calloc',0x780018f9,0x780019de),('initptd',0x780019de,0x780019f1),
       # _CRTDLL_INIT continuation from the _ioinit CALL up to the environment-strings CALL.
       ('attach2',0x7800187d,0x78001882),('ioinit',0x78003c1d,0x78003cf1),('ioinit_cold',0x7800e4ad,0x7800e4cf),
       # The cold GetFileType path re-enters the handle loop at 78003CAC/78003CB0; these
       # tail objects lift the loop bytes 78003C8C..78003CF1 with those entries.
       ('ioinit_tail_cac',0x78003c8c,0x78003cf1,0x78003cac),('ioinit_tail_cb0',0x78003c8c,0x78003cf1,0x78003cb0),
       # Environment strings CALL and _aenvptr store, up to the _acmdln writer the carry runs; __crtGetEnvironmentStringsA.
       ('attach3',0x78001882,0x7800188c),('envstrings',0x78003cf1,0x78003d9a),
       # Part B after the carry's _acmdln writer: wide command line CALL and _wcmdln store.
       ('attachb1',0x78001897,0x780018a1),('wcmdln',0x78003d9a,0x78003dd2),
       # __initmbctable -> _setmbcp(-3): lazy _lock(25), GetACP, GetCPInfo, setSBUpLow with __crtGetStringTypeA/__crtLCMapStringA.
       ('attachb2',0x780018a1,0x780018a6),('initmbctable',0x78003dd2,0x78003ddb),('setmbcp',0x78003ddb,0x78003e84),('getsyscp',0x78003e84,0x78003eb1),
       ('setsbuplow',0x78003eb1,0x78003fba),('lcmapa',0x78003fba,0x78004187),('gettypea',0x78002e20,0x78002f32),
       ('lock',0x78001055,0x78001080),('lock_tail',0x78001080,0x780010b0),('lock_enter',0x7800106d,0x78001078),('unlock',0x7800129e,0x780012b3),('memset',0x78001000,0x78001055),('strncnt',0x7800415d,0x78004187),
       # _setenvp CALL, _setenvp, strlen; strcpy shares strcat's copy tail, so its bytes span 78002FAB..780036BE (only code reachable from the entry is lifted).
       ('attachb3',0x780018a6,0x780018ab),('setenvp',0x78004187,0x78004227),('strlen',0x78002f32,0x78002fab),('strcpy',0x78002fab,0x780036be),
       # _cinit CALL, proc_attached increment and attach epilogue; _cinit, _initterm and MSVCRT's four initializers.
       ('attachb4',0x780018ab,0x780018bb),('attach_epilogue',0x7800181b,0x78001823),('cinit',0x78004227,0x78004254),('initterm',0x780014f8,0x78001514),
       ('initstdio',0x78004410,0x78004482),('initstdio_cold',0x7800f945,0x7800f952),('initstdio_tail_471',0x78004451,0x78004482,0x78004471),('initstdio_tail_474',0x78004451,0x78004482,0x78004474),
       ('onexitinit',0x78004482,0x780044a8),('inittime',0x780044a8,0x780044dd),('allmul',0x780044dd,0x7800450c),('setfilter',0x7800450c,0x7800451d),
       # Main initializer root 1 (40FFE0) closure: MSVCRT _onexit/_lockexit/_msize/_unlockexit, game code, MFC42 operator new (ordinal 823).
       ('onexit',0x78004a36,0x78004a7b),('lockexit',0x78001514,0x7800151d),('msize',0x7800151d,0x780015c8),('unlockexit',0x78003041,0x7800304a),
       ('g_thunk_initterm',0x5ac598,0x5ac59e,0x5ac598,'game'),('g_root1',0x40ffe0,0x40ffea,0x40ffe0,'game'),('g_root1_ctor',0x40fff0,0x40fffa,0x40fff0,'game'),
       ('g_ctor',0x4c7b80,0x4c7ba9,0x4c7b80,'game'),('g_thunk_new',0x5abd26,0x5abd2c,0x5abd26,'game'),('g_root1_atexit',0x410000,0x41000e,0x410000,'game'),
       ('g_atexit',0x5ac140,0x5ac155,0x5ac140,'game'),('g_onexit',0x5ac110,0x5ac140,0x5ac110,'game'),('m_new',0x5f401ea0,0x5f401ec9,0x5f401ea0,'mfc42'),
       # Roots 2..7: the same CALL ctor-thunk / JMP atexit-thunk shape on five objects with ctor 4D8540.
       ('g_r410030_a',0x410030,0x41003a,0x410030,'game'),('g_r410030_b',0x410040,0x41004a,0x410040,'game'),('g_r410030_c',0x410050,0x41005e,0x410050,'game'),('g_r410080_a',0x410080,0x41008a,0x410080,'game'),('g_r410080_b',0x410090,0x41009a,0x410090,'game'),('g_r410080_c',0x4100a0,0x4100ae,0x4100a0,'game'),('g_r4100d0_a',0x4100d0,0x4100da,0x4100d0,'game'),('g_r4100d0_b',0x4100e0,0x4100ea,0x4100e0,'game'),('g_r4100d0_c',0x4100f0,0x4100fe,0x4100f0,'game'),('g_r410120_a',0x410120,0x41012a,0x410120,'game'),('g_r410120_b',0x410130,0x41013a,0x410130,'game'),('g_r410120_c',0x410140,0x41014e,0x410140,'game'),('g_r410170_a',0x410170,0x41017a,0x410170,'game'),('g_r410170_b',0x410180,0x41018a,0x410180,'game'),('g_r410170_c',0x410190,0x41019e,0x410190,'game'),('g_r4101c0_a',0x4101c0,0x4101ca,0x4101c0,'game'),('g_r4101c0_b',0x4101d0,0x4101da,0x4101d0,'game'),('g_r4101c0_c',0x4101e0,0x4101ee,0x4101e0,'game'),('g_ctor_4d8540',0x4d8540,0x4d856f,0x4d8540,'game'),
       # Roots 8..13: derived ctors over the base ctor 4C8600 (no allocation).
       ('g_r410210_a',0x410210,0x41021a,0x410210,'game'),('g_r410210_b',0x410220,0x41022a,0x410220,'game'),('g_r410210_c',0x410230,0x41023e,0x410230,'game'),('g_r410260_a',0x410260,0x41026a,0x410260,'game'),('g_r410260_b',0x410270,0x41027a,0x410270,'game'),('g_r410260_c',0x410280,0x41028e,0x410280,'game'),('g_r4102b0_a',0x4102b0,0x4102ba,0x4102b0,'game'),('g_r4102b0_b',0x4102c0,0x4102ca,0x4102c0,'game'),('g_r4102b0_c',0x4102d0,0x4102de,0x4102d0,'game'),('g_r410300_a',0x410300,0x41030a,0x410300,'game'),('g_r410300_b',0x410310,0x41031a,0x410310,'game'),('g_r410300_c',0x410320,0x41032e,0x410320,'game'),('g_r410350_a',0x410350,0x41035a,0x410350,'game'),('g_r410350_b',0x410360,0x41036a,0x410360,'game'),('g_r410350_c',0x410370,0x41037e,0x410370,'game'),('g_r4103a0_a',0x4103a0,0x4103aa,0x4103a0,'game'),('g_r4103a0_b',0x4103b0,0x4103ba,0x4103b0,'game'),('g_r4103a0_c',0x4103c0,0x4103ce,0x4103c0,'game'),('g_ctor_4105d0',0x4105d0,0x4105e2,0x4105d0,'game'),('g_ctor_410610',0x410610,0x410622,0x410610,'game'),('g_ctor_410630',0x410630,0x410642,0x410630,'game'),('g_ctor_4c8750',0x4c8750,0x4c8762,0x4c8750,'game'),('g_ctor_410650',0x410650,0x410662,0x410650,'game'),('g_ctor_410680',0x410680,0x410692,0x410680,'game'),('g_ctor_4c8600',0x4c8600,0x4c8619,0x4c8600,'game'),
       # Roots 14..15: ID-registered objects (4C0310/4C0570 over base 4BF910) and their helpers; MFC42 operator delete.
       ('g_r4103f0_a',0x4103f0,0x4103fa,0x4103f0,'game'),('g_r4103f0_b',0x410400,0x41040a,0x410400,'game'),('g_r4103f0_c',0x410410,0x41041e,0x410410,'game'),('g_r410440_a',0x410440,0x41044a,0x410440,'game'),('g_r410440_b',0x410450,0x41045a,0x410450,'game'),('g_r410440_c',0x410460,0x41046e,0x410460,'game'),('g_f4c0310',0x4c0310,0x4c0512,0x4c0310,'game'),('g_f4c0570',0x4c0570,0x4c0772,0x4c0570,'game'),('g_f4bf910',0x4bf910,0x4bfb90,0x4bf910,'game'),('g_f58b1c0',0x58b1c0,0x58b21c,0x58b1c0,'game'),('g_f58b160',0x58b160,0x58b1c0,0x58b160,'game'),('g_f4d5120',0x4d5120,0x4d5139,0x4d5120,'game'),('g_f58aec0',0x58aec0,0x58afe0,0x58aec0,'game'),('g_f4d5110',0x4d5110,0x4d5119,0x4d5110,'game'),('g_f475bf0',0x475bf0,0x475c1e,0x475bf0,'game'),('g_f475c20',0x475c20,0x475c43,0x475c20,'game'),('g_f40baf0',0x40baf0,0x40baf3,0x40baf0,'game'),('g_f4fd1c0',0x4fd1c0,0x4fd1d3,0x4fd1c0,'game'),('g_f5abd1a',0x5abd1a,0x5abd20,0x5abd1a,'game'),('m_delete',0x5f401782,0x5f40178e,0x5f401782,'mfc42'),('g_f40a850',0x40a850,0x40a854,0x40a850,'game'))
# Direct calls whose target symbol another linked object already defines: renamed so the call
# stays inside the heap Stage (llvm-objcopy --redefine-sym, recorded in the report).
RENAMES={'cinit':{'sub_780014f8':'mw34_attach_cinit_initterm'}}
# Tolerant mode (lift_closure.py only): a component whose lift/lowering fails is recorded in the
# report's 'failed' map and skipped; reaching it at run time stops typed. Default off.
TOLERANT=False
# Optional lowering extension (lift_closure.py only): (old, new) replacements applied to the lowering
# source and an LLVM API class override. Defaults leave the lowering unchanged.
LOWER_PATCHES=[];LLVM_CLASS=None;GUEST_IR_HOOK=None  # optional guest-IR rewrite before lowering (lift_closure.py)
BRIDGES={'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_read_memory_8','__remill_read_memory_16','__remill_write_memory_16',
         '__remill_function_call','__remill_function_return','__remill_jump','__remill_missing_block'}
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def span_bytes(data,start,end):
    pe=struct.unpack_from('<I',data,0x3c)[0];n=struct.unpack_from('<H',data,pe+6)[0];opt=pe+24;so=struct.unpack_from('<H',data,pe+20)[0];base=struct.unpack_from('<I',data,opt+28)[0]
    for i in range(n):
        o=opt+so+i*40;vs,va,rs,rp=struct.unpack_from('<IIII',data,o+8);flags=struct.unpack_from('<I',data,o+36)[0]
        lo=base+va
        if lo<=start and end<=lo+rs:need(flags&0x20000000,'Executable source section');return data[rp+start-lo:rp+end-lo]
    raise ValueError('Span outside one raw section')
def main(name, *, output_root=None):
    need(re.fullmatch('lifts-r[1-9][0-9]*(-p[0-9]+)?',name),'lifts-rN or a lift_closure.py partition lifts-rN-pK')
    out=(Path(output_root) if output_root is not None else ROOT/'reports/m4-crt-attach')/name;need(not out.exists(),'Fresh lift output');need(sha(PROVIDER)==PROVIDER_SHA,'Exact staged provider')
    data=PROVIDER.read_bytes()
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    lifter=ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe'
    # MW34_SEMANTICS=mmx selects the repaired semantics plus the MMX PADDUSB/PADDUSW encodings
    # (local/tools/remill-mmx-build; same lifter, a strict addition of four instruction forms).
    if os.environ.get('MW34_SEMANTICS')=='mmx':sem=ROOT/'local/tools/remill-mmx-build/semantics/x86.bc';need(sha(sem)=='af3747462df075eed7a06ae078b3ff961da9a24f970856653746086abf3caf91','Exact MMX semantics')
    else:sem=ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc';need(sha(sem)=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca','Exact semantics')
    dll=llvm/'LLVM-C.dll';upstream=(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
    lower_source=(ROOT/'tools/m4-crt-mainargs-recovery/recover.py').read_text()
    body=lower_source[lower_source.index('def lower('):lower_source.index("if __name__ == '__main__':")]
    body=body.replace('mw34_mainargs_','mw34_attach_').replace("and '__remill_missing_block' not in text",'')
    for old,new in LOWER_PATCHES:need(body.count(old)==1,'Exact lowering patch site');body=body.replace(old,new)
    sys.path.insert(0,str(ROOT/'tools/lifting'))
    from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
    ns=dict(c=c,re=re,sha=sha,LLVM=LLVM_CLASS(LLVM) if LLVM_CLASS else LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES)
    exec(compile(body,'recover.py:lower','exec'),ns)
    out.mkdir(parents=True);report=dict(provider=str(PROVIDER),provider_sha256=PROVIDER_SHA,components={})
    def run(program,args,label):
        cp=subprocess.run([str(program),*map(str,args)],capture_output=True,timeout=120)
        (out/(label+'.stdout')).write_bytes(cp.stdout);(out/(label+'.stderr')).write_bytes(cp.stderr)
        need(cp.returncode==0,'Tool failed '+label);return cp.stdout
    images={k:(path.read_bytes(),digest) for k,(path,digest) in IMAGES.items()}
    for k,(blob,digest) in images.items():need(hashlib.sha256(blob).hexdigest()==digest,'Exact pinned source image '+k)
    for component,start,end,*rest in SPANS:
      try:
        entry=rest[0] if rest else start;image=rest[1] if len(rest)>1 else 'msvcrt';need(start<=entry<end,'Entry inside lifted bytes')
        code=span_bytes(images[image][0],start,end);(out/(component+'-source.bin')).write_bytes(code)
        run(lifter,['--arch=x86','--os=windows','--address='+str(start),'--entry_address='+str(entry),'--bytes='+code.hex(),
            '--semantics_dir='+str(sem.parent),'--ir_out='+str(out/(component+'-guest.ll'))],component+'-lift')
        text=(out/(component+'-guest.ll')).read_text()
        if GUEST_IR_HOOK:text=GUEST_IR_HOOK(text);(out/(component+'-guest.ll')).write_text(text)
        calls=[dict(kind='direct',target=int(a,16)) for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',text,re.M)]
        native=ns['lower'](out,component,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm)
        for old,new in RENAMES.get(component,{}).items():
            for level,info in native['objects'].items():
                run(llvm/'llvm-objcopy.exe',['--redefine-sym',old+'='+new,info['path']],component+'-rename-'+level);info['sha256']=sha(info['path'])
            native['bridges']=sorted(new if b==old else b for b in native['bridges']);native.setdefault('renames',{})[old]=new
        native.update(entry=entry,start=start,end=end,source_bytes=len(code),source_sha256=hashlib.sha256(code).hexdigest(),direct_targets=[hex(x['target']) for x in calls])
        report['components'][component]=native
        print(json.dumps(dict(component=component,entry=hex(entry),bytes=len(code),direct=native['direct_targets'],bridges=native['bridges'])),flush=True)
      except Exception as e:
        if not TOLERANT:raise
        report.setdefault('failed',{})[component]=repr(e)[:400];print(json.dumps(dict(component=component,failed=repr(e)[:200])),flush=True)
    (out/'report.json').write_text(json.dumps(report,indent=1)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
