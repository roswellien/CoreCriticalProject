"""Read-only root review of concrete joint27 build before any capture."""
import argparse,hashlib,importlib.util,json,pathlib,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=pathlib.Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(out):
    assert out.parent==ROOT/'reports/m4-joint27-startup' and not out.exists();out.mkdir();(out/'review-source.py').write_bytes(pathlib.Path(__file__).read_bytes())
    try:
        build=read(pin(ROOT/'reports/m4-joint27-startup/build-only-r1/build.json','695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5'))
        assert build['passed'] and not build['worker_executed'] and not build['original_executed']
        for prior in sorted(out.parent.glob('root-preflight-r*')):
            if prior==out:continue
            for p in prior.iterdir():
                if p.is_file():pin(p)
        for group in ('sources','tools','artifacts'):
            for p,h in build[group].items():pin(p,h)
        for item in build['literal_sources']:
            assert pin(item['original_path'],item['sha256']).read_bytes()==pin(item['preserved_path'],item['sha256']).read_bytes()
        for level,objects in build['objects'].items():
            assert level in ('O0','O2') and len(objects)==12
            for p,h in objects.items():pin(p,h)
        generation=read(pin(build['generation'],build['generation_sha256']))
        for item in generation['literal_sources']:
            assert pin(item['original_path'],item['sha256']).read_bytes()==pin(item['preserved_path'],item['sha256']).read_bytes()
        accepted=ROOT/'reports/m4-fp-numeric-max-carry/root-component-acceptance-r2'
        gate=read(pin(accepted/'report.json','fe713df4600d61acb3ac1eb6ea80963c1dc225d5e73fa3032795dc1905ca7706'));assert gate['component_accepted']
        pins=read(pin(accepted/'pins.json','1bc0128a56213ba02858c90ee8588371f41445ac32ec559bc48f13afcc5ec953'))
        for p,h in pins['files'].items():pin(p,h)
        canonical=pin(ROOT/'reports/m4-fp-numeric-max-carry/native-preparation-canonical-r1/session.hpp','22bef4a73a171b9900b0376d7d2c3022d208b5e8b2c6159ccad2d060834da9b1').read_text()
        candidate=pin(ROOT/'reports/m4-joint27-startup/derived-r1/session.hpp','45afbdcf745ebf9e529444d5858388d30225881fd8f554f4205e6cfe19020457').read_text()
        expected=canonical.replace('try{source_check();admit_fp();auto token=', 'try{source_check();admit_fp();if(observe_root_entry)observe_root_entry(*this);auto token=')
        expected=expected.replace('public:\n void(*test_after_event)', 'public:\n void(*observe_root_entry)(Session&){}; // New observational hook, null outside joint27 records.\n void(*test_after_event)')
        assert candidate==expected,'Only the default-null admitted-entry observation hook differs'
        for name in ('4c19f0-runtime.ll','4c1a00-runtime.ll','780c10f0-runtime.ll'):
            before=pin(ROOT/'reports/m4-fp-numeric-max-integration/preparation-r4'/name)
            after=pin(ROOT/'reports/m4-joint27-startup/derived-r1/numeric-ir'/name)
            assert before.read_bytes()==after.read_bytes(),'Numerical translated guest IR unchanged'
        worker=pin(ROOT/'tools/m4-joint27-startup/native_main.cpp','b9b3980be51a2dafbc5032d69d52539747b9b465ba3163d270d519b717930511').read_text()
        assert 'bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept' in worker
        body=worker.split('bool invoke_selected_table',1)[1].split('void snapshot_numeric',1)[0]
        assert body.index('ni::NumericHostBoundary boundary(admitted_cw_)')<body.index('try{')<body.index('ni::Session::Borrow borrow(*session_)')<body.index('for(const auto&item:ledger.items())')<body.index('r_.call_direct')<body.index('}catch(...)')<body.rindex('return ok;')
        assert 'observation=nullptr;failed_=true' in body and 'phase==27&&r_.calls().size()==29&&r_.translation_count()==28' in body
        assert worker.index('context.invoke_selected_table(seq,repeat,top,records)')<worker.index('caller.capture()')<worker.index('summary.host_before=')
        protocol=pin(ROOT/'reports/m4-joint27-startup/derived-r1/joint_protocol.hpp','c70995e26ecd79607d22fbe3efabceaf16391268474c00a88197ab7158326b51').read_text()
        entries=[int(x,16) for x in re.search(r'entries\{([^}]+)\}',protocol)[1].split(',')]
        assert len(entries)==27 and len(set(entries))==27 and entries.count(0x4c19f0)==1
        pe_path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638');spec=importlib.util.spec_from_file_location('root_joint27_pe',pe_path);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
        image=pe.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());offset,_=image.rva_range(0x5e0000-image.image_base,0x244)
        table=struct.unpack_from('<145I',image.data,offset);selected=[(0x5e0000+4*i,target) for i,target in enumerate(table) if target in entries]
        assert len(selected)==27 and {target for _,target in selected}==set(entries)
        numeric_index=next(i for i,row in enumerate(selected) if row[1]==0x4c19f0)
        assert selected[numeric_index][0]==0x5e016c and selected[numeric_index-1][1]==0x4b7020 and selected[numeric_index+1][1]==0x4c78f0
        dump=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a');decoded=[]
        for level in ('O0','O2'):
            obj=next(pathlib.Path(p) for p in build['artifacts'] if p.endswith('native_main.cpp.obj') and f'-{level}' in p)
            command=[str(dump),'--disassemble','--reloc','--unwind-info','--syms','--demangle',str(obj)]
            r=subprocess.run(command,capture_output=True,timeout=60);assert r.returncode==0
            path=out/f'outer-{level}.coff.txt';path.write_bytes(r.stdout);(out/f'outer-{level}.stderr').write_bytes(r.stderr)
            text=r.stdout.decode('utf-8',errors='strict')
            assert 'file format coff-x86-64' in text and 'fxsave64' in text and 'fnstenv' in text and 'fldenv' in text and 'fxrstor64' in text
            assert 'invoke_selected_table' in text and ('__CxxFrameHandler3' in text or '__CxxFrameHandler4' in text)
            if level=='O0':assert 'NumericHostBoundary' in text and 'Session::Borrow' in text
            decoded.append({'level':level,'object':str(obj),'object_sha256':sha(obj),'command':command,'decoded_path':str(path),'decoded_sha256':sha(path),'scope':'Fresh COFF outer guard/Borrow and actual EH associations; source ordering reviewed separately.'})
        result={'passed':True,'scope':'Concrete root source/identity/COFF pre-execution review of bounded joint27 research only',
                'build_manifest_sha256':sha(ROOT/'reports/m4-joint27-startup/build-only-r1/build.json'),'actual_joint27_executed':False,'selected_roots':27,
                'actual_table_order':selected,'numeric_slot':0x5e016c,'numeric_guest_IR_unchanged':True,'numeric_header_delta':'Default-null admitted-entry observation hook only',
                'numerical_boundary_scope':'One Context invoke_selected_table boundary spans all27calls, Session::Borrow, observations, internal catches and cleanup; noexcept status return. Raw Runtime calls have no independent host restoration claim.',
                'direct_outside_return_capture':True,'compiled_evidence':decoded,'current_physical_bindings':len(PINS),'whole_M4_complete':False}
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(__file__)
        for path in out.iterdir():
            if path.is_file():pin(path)
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'bindings':len(PINS),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=pathlib.Path);main(parser.parse_args().output.resolve())
