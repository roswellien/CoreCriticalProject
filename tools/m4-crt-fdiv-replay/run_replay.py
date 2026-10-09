"""Lossless runner for the additive, original-BEFORE-only native FDIV replay.

Success here means the actual compiled worker completed its observations. It
does not imply source-model or original/native differential acceptance.
"""
import argparse, hashlib, json, pathlib, re, struct, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-fdiv-replay'
BUILD = BASE / 'native-build-r1/build.json'
PREP = BASE / 'preparation-r1/report.json'
PREP_PINS = BASE / 'preparation-r1/pins.json'
GAME = ROOT / 'MW3/Mech3.exe'
PROVIDER = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
PACK = ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin'
EXPECTED = {
    GAME: '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
    PROVIDER: '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
    PACK: 'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80',
    PREP: 'b4e36d5fd4966b4c4e9ab1a5b0564f699e5c6f851cc2e6bbeb643e99dd85ec3f',
    PREP_PINS: '3d543c649cddef572cf3d4d00a40741a3645de5b5d46be7e075b1589824873bb',
}
CW = [0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f]
STRIDE = 107740
def need(v, message):
    if not v: raise ValueError(message)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(p, value):
    with pathlib.Path(p).open('x', encoding='utf-8') as f: f.write(json.dumps(value, indent=2)+'\n')
def blob(p, data):
    with pathlib.Path(p).open('xb') as f: f.write(data)
def admit():
    files = {str(p.resolve()): h for p,h in EXPECTED.items()}
    for p,h in files.items(): need(sha(p)==h, 'Exact replay input association '+p)
    b = read(BUILD); need(b['passed'] and not b['native_replay_executed'], 'Frozen successful build-only manifest')
    files[str(BUILD)] = sha(BUILD)
    for group in ('sources','tools','libraries','compiler_read_headers','artifacts'):
        for p,h in b[group].items():
            need(sha(p)==h, 'Frozen replay build association '+p)
            need(p not in files or files[p]==h, 'Nonconflicting build association '+p)
            files[p] = h
    for p,h in read(PREP_PINS)['files'].items():
        need(sha(p)==h, 'Frozen BEFORE preparation association '+p)
        need(p not in files or files[p]==h, 'Nonconflicting preparation association '+p)
        files[p]=h
    p = read(PREP); inputs = pathlib.Path(p['inputs_path'])
    need(sha(inputs)==p['inputs_sha256']==b['inputs_sha256'], 'Exact compiled BEFORE-only input hash')
    for level, worker in b['workers'].items(): need(worker in b['artifacts'], 'Actual worker artifact association '+level)
    return b, inputs, files
def tooling(b):
    """Bind post-build current tools and the literal evidence declaring them.

    The primary map records the CMake/DevShell/pwsh invocations, not all nested
    executables. Cache/rules declaration alone is not proof of execution.
    """
    result = {'primary_build_path':str(BUILD), 'primary_build_sha256':sha(BUILD),
              'scope':'Supplemental current file hashes after build; no retrospective execution-time tool attestation',
              'primary_direct_tool_count':len(b['tools']), 'levels':{}}
    for level,worker in b['workers'].items():
        directory = pathlib.Path(worker).parent
        cache = directory/'CMakeCache.txt'; rules = directory/'CMakeFiles/rules.ninja'
        values = dict(re.findall(r'^(CMAKE_(?:CXX_COMPILER(?:_AR|_CLANG_SCAN_DEPS|_RANLIB)?|LINKER|MAKE_PROGRAM|MT|RC_COMPILER)):[^=]+=(.+)$', cache.read_text(), re.M))
        tools = {name:{'path':str(pathlib.Path(path).resolve()),'current_sha256':sha(path)} for name,path in values.items()}
        log = BUILD.parent/('build-'+level+'.log'); text = log.read_text(encoding='utf-8-sig')
        need('[1/2]' in text and '[2/2]' in text and 'clang-cl.exe' in text and 'lld-link.exe' in text and 'ninja.exe -v' in text, 'Actual compiler/link/Ninja command evidence')
        result['levels'][level] = {'configured_tools':tools,'cache_path':str(cache),'cache_sha256':sha(cache),
            'rules_path':str(rules),'rules_sha256':sha(rules),'build_log_path':str(log),'build_log_sha256':sha(log),
            'actual_verbose_command_evidence':['Ninja','clang-cl','lld-link','CMake vs_link_exe'],
            'configured_only_without_separate_execution_claim':['llvm-ar','clang-scan-deps','llvm-ranlib','RC','MT'],
            'link_library_names_from_actual_command':'fdiv_registry.lib bcrypt.lib kernel32.lib user32.lib gdi32.lib winspool.lib shell32.lib ole32.lib oleaut32.lib uuid.lib comdlg32.lib advapi32.lib',
            'link_resolution_scope':'Frozen Registry library path/hash is explicit; SDK import library filenames are observed command operands, without a recorded file-open trace for the exact resolution of those names.'}
    return result
def parse(raw, level):
    data = raw.read_bytes()
    need(data[:8]==b'MW4FDRN1' and struct.unpack_from('<4I',data,8)==(1,24,STRIDE,9), 'Actual replay raw schema')
    need(len(data)==24+24*STRIDE+8 and data[-8:]==b'COMPLETE', 'Actual complete replay extent')
    rows=[]
    for i in range(24):
        offset=24+i*STRIDE; r=data[offset:offset+STRIDE]
        tags=dict(zip(('id','repeat','cw','status','events','routes','lookups'), struct.unpack_from('<7I',r)))
        need((tags['id'],tags['repeat'],tags['cw'])==(i,i//12,CW[i%12]), 'Observed replay corpus association')
        need(tags['status']==1 and tags['events']==97 and tags['routes']==tags['lookups']==3, 'Actual completed bounded source/route observations')
        need(r[8060:8572]==r[8572:9084] and r[9084:9112]==r[9112:9140], 'Observed internal restoration checkpoint')
        lookups=[]
        for j in range(3):
            p=88072+j*6556
            kind,token,arg,result,error,host=struct.unpack_from('<5IQ',r,p)
            lookups.append({'kind':kind,'guest_token':token,'argument':arg,'actual_raw_result':result,'last_error':error,'actual_host_result':host})
        rows.append({'level':level,'tags':tags,'raw_offset':offset,'raw_bytes':STRIDE,'raw_sha256':hashlib.sha256(r).hexdigest(),
            'source_written_BOOL':struct.unpack_from('<I',r,46004+6*4096+0xc2c)[0],
            'actual_lookups':lookups,'whole_State_before_sha256':hashlib.sha256(r[28:3532]).hexdigest(),
            'whole_State_after_sha256':hashlib.sha256(r[3532:7036]).hexdigest(),
            'raw_FX_before_sha256':hashlib.sha256(r[7036:7548]).hexdigest(),
            'raw_FX_after_sha256':hashlib.sha256(r[7548:8060]).hexdigest(),
            'host_FP_claim':'Internal Registry restoration checkpoint, not whole C++ caller volatile SIMD equality',
            'source_model_or_original_equivalence_accepted':False})
    return rows
def main(output, execute):
    output=pathlib.Path(output).resolve()
    need(output.parent==BASE and not output.exists() and re.fullmatch('[a-z][a-z0-9-]{0,63}',output.name), 'Fresh immediate private replay report required')
    b, inputs, files=admit(); supplement=tooling(b)
    output.mkdir(); blob(output/'runner-source.py',pathlib.Path(__file__).read_bytes())
    save(output/'tooling-supplement.json',supplement)
    commands={level:[worker,str(GAME),str(PROVIDER),str(PACK),str(inputs),str(output/('native-'+level+'.bin'))] for level,worker in b['workers'].items()}
    recipe={'scope':'Additive before-only replay linked to unchanged FDIV r3; own actual64bit Windows API calls; no original execution or differential acceptance',
        'execute_requested':execute,'commands':commands,'shell':False,'timeout_seconds_per_worker':90,
        'pre_call_files':files,'runner_sha256':sha(__file__),'input_path':str(inputs),'input_sha256':sha(inputs),
        'original_AFTER_used_as_input':False,'raw_output_schema':{'magic':'MW4FDRN1','header':24,'rows':24,'stride':STRIDE,'footer':'COMPLETE'},
        'volatile_scope':'Actual original SIMD differences, Windows service footprint and two ECX residual halfwords remain raw separate observations; no fullFX or whole real-stack portable equality',
        'whole_M4_complete':False}
    save(output/'launch-recipe.json',recipe)
    if not execute:
        save(output/'pins.json',{'files':{**files,**{str(p):sha(p) for p in output.rglob('*') if p.is_file()},str(pathlib.Path(__file__).resolve()):sha(__file__)}})
        print(json.dumps({'planned_only':True,'recipe_sha256':sha(output/'launch-recipe.json'),'build_sha256':sha(BUILD)})); return
    outcomes=[]; rows=[]
    try:
        for level,command in commands.items():
            need(admit()[2]==files and tooling(b)==supplement, 'Immediate pre-call file associations unchanged')
            cp=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
            blob(output/('positive-'+level+'.stdout'),cp.stdout);blob(output/('positive-'+level+'.stderr'),cp.stderr)
            outcomes.append({'level':level,'command':command,'exit_code':cp.returncode,'stdout_path':str(output/('positive-'+level+'.stdout')),'stderr_path':str(output/('positive-'+level+'.stderr'))})
            need(cp.returncode==0, 'Actual replay worker failed; raw prefix retained '+level)
            rows.extend(parse(output/('native-'+level+'.bin'),level))
        need(admit()[2]==files, 'Frozen replay dependencies remain exact after execution')
        save(output/'actual-rows.json',{'rows':rows,'raw_row_bytes_changed':False})
        save(output/'report.json',{'passed':True,'scope':'Actual native BEFORE-only replay observations; independent whole native source model and bounded original comparison remain pending',
            'records':len(rows),'O0_records':24,'O2_records':24,'commands':outcomes,
            'raw_outputs':{level:{'path':str(output/('native-'+level+'.bin')),'sha256':sha(output/('native-'+level+'.bin')),'bytes':(output/('native-'+level+'.bin')).stat().st_size} for level in commands},
            'actual_source_written_BOOL_values':sorted({r['source_written_BOOL'] for r in rows}),
            'original_AFTER_used_as_input':False,'original_executed':False,'native_executed':True,
            'native_source_model_accepted':False,'original_native_equivalence_accepted':False,'whole_M4_complete':False})
    except subprocess.TimeoutExpired as e:
        blob(output/'timeout.stdout',e.stdout or b'');blob(output/'timeout.stderr',e.stderr or b'')
        save(output/'failure.json',{'passed':False,'reason':'Actual bounded native worker timeout','outcomes':outcomes,'observed_raw_prefixes_retained':True}); raise
    except Exception as e:
        save(output/'failure.json',{'passed':False,'reason':str(e),'outcomes':outcomes,'observed_raw_prefixes_retained':True}); raise
    finally:
        save(output/'pins.json',{'files':{**files,**{str(p):sha(p) for p in output.rglob('*') if p.is_file()},str(pathlib.Path(__file__).resolve()):sha(__file__)}})
    print(json.dumps({'passed':True,'records':len(rows),'report_sha256':sha(output/'report.json'),'pins_sha256':sha(output/'pins.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--plan',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args();main(a.output,a.execute)
