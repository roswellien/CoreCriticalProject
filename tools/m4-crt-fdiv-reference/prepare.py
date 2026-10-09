"""Read-only source admission for an original real-thread-stack FDIV probe.

This preparation never executes provider instructions or a reference worker.
"""
import argparse,hashlib,json,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv-reference'
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh immediate private reference preparation');files={}
    def bind(p,expected=None):
        p=pathlib.Path(p).resolve();h=sha(p);need(expected is None or h==expected,'Exact original source association '+str(p));files[str(p)]=h;return h
    recovery=ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json';bind(recovery,'c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd');m=read(recovery);provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';bind(provider,'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    packpath=ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin';bind(packpath,'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80');pack=packpath.read_bytes();need(len(pack)==28740 and pack[:8]==b'MW4FDIP1'and struct.unpack_from('<I',pack,8)[0]==7,'Exact unchanged seven-page source pack')
    bases=[]
    for i in range(7):
        address,permissions=struct.unpack_from('<2I',pack,12+i*4104);bases.append({'address':address,'permissions':permissions,'source_page_sha256':hashlib.sha256(pack[20+i*4104:20+i*4104+4096]).hexdigest()})
    need([x['address']for x in bases]==[0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000],'Exact RX/RO/RW page identity');need(m['unique_writer_dependency_instructions']==204,'Complete source dependency graph')
    # Reuse the admitted admission/parser path solely for static original byte
    # checks; it contributes no computational expected result or execution.
    import sys;sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'tools/m4-crt-control-integration'))
    from prepare import PE
    pe=PE(provider,files[str(provider.resolve())],0x78000000)
    for graph in m['complete_graphs']:
        for ins in graph['instructions']:need(pe.bytes(ins['address'],ins['size'],True).hex()==ins['bytes_hex'],'Every retained complete dependency instruction matches original bytes')
    for p in(ROOT/'tools/m4-crt-control-integration/prepare.py',ROOT/'tools/m4-crt-control-integration/original_broker.hpp',ROOT/'tools/m4-crt/probe_common.hpp',ROOT/'tools/m4-crt/probe_io.hpp',pathlib.Path(__file__).resolve()):bind(p)
    out.mkdir(parents=True);(out/'pack.bin').write_bytes(pack);bind(out/'pack.bin');(out/'prepare-source.py').write_bytes(pathlib.Path(__file__).read_bytes());bind(out/'prepare-source.py')
    spec='#pragma once\nnamespace mw34::m4_fdiv_reference {\ninline constexpr char pack_sha[]="'+files[str(packpath.resolve())]+'";\ninline constexpr unsigned pack_bytes=28740,writer=0x78004254,capture=0x10000100;\n}\n';(out/'spec.hpp').write_text(spec);bind(out/'spec.hpp')
    report={'passed':True,'scope':'Static preparation only for a bounded complete original writer on the real Windows x86 thread stack','original_executed':False,'native_executed':False,'worker_built':False,'provider_path':str(provider),'provider_sha256':files[str(provider.resolve())],'pack_path':str(out/'pack.bin'),'pack_sha256':sha(out/'pack.bin'),'pages':bases,'original_dependency_PCs':204,'writer_entry':0x78004254,'actual_source_import_cells':[0x7802e098,0x7802e0d0],'actual_source_return_PCs':[0x780042ae,0x780042c2,0x780042ce],'source_raw_import_words':[0x345d2,0x346ac],'reservation_bases':[0x78000000,0x78010000,0x78020000,0x78030000,0x10000000],'reservation_bytes':65536,'stack_policy':'Create a real Windows x86 reference thread with 64 KiB initial committed stack. Assembly uses its natural CALL frame; no fixed guest ESP, TEB rewrite, pointer parity fabrication, or service gateway. Capture every actual committed RW stack page from NT_TIB StackLimit to StackBase after complete VirtualQuery admission, bounded 1 MiB; exclude guard and uncommitted pages. Record actual before/after extents and reject extent growth for initial comparison scope.','source_transport':'Only two private owning IAT DWORDs become actual associated 32-bit API pointers. Source bytes, source return words and returned FARPROC remain untouched. Outer authored capturePC is explicit.','debug_policy':'Separate debug-off and debug-on records. Hardware execute breakpoints at three actual source return PCs capture Exception/CONTEXT verbatim; exact RF and DR6 continuation edits recorded separately. No debugFP fields counted when context flags omit them. No claim OS contextFP is direct FNSTENV.','capture_policy':'Direct assembly entry/return full CPU, FXSAVE512 and FNSTENV28 plus complete provider/source/import/data and full admitted committed actual stack pages before C++ cleanup; actual API volatile ECX/EDX/flags retained in debug observations; W-34..-32 and W-42..-40 residual high halves retained raw.','initial_domain':'12 normalized masked IC0 CW, empty TOP0/SW0, two fresh repeats, actual source query BOOL; unsupported/non-null lookup admission is explicit.','launch_admission':'Original execution requires parent review of concrete compiled scaffold/recipe/identity and ownership proof. Preparation alone grants no run or original comparison credit.','whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print(json.dumps({'passed':True,'static_only':True,'bindings':len(files),'report_sha256':sha(out/'report.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');a=p.parse_args();main(a.output)
