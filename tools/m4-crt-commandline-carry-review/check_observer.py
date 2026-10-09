"""Additive adversarial checks of the independent direct-hardware observer."""
import hashlib, importlib.util, json, pathlib, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/m4-crt-commandline-carry'
OBSERVER_SHA = '0c2f00ee443de979a5a3afb49d53b6450f4ca34aa4840afdb28a497df5f539da'

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(path):
    with pathlib.Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main(build, output):
    need(output.parent == BASE and output.name.startswith('independent-compiled-') and not output.exists(), 'Fresh additive independent observer-controls output')
    output.mkdir(parents=True)
    observer = ROOT/'tools/m4-crt-commandline-carry-review/review.py'
    need(sha(observer) == OBSERVER_SHA, 'Exact sealed independently authored host observer')
    spec = importlib.util.spec_from_file_location('independent_control_host_observer', observer)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    compiled_report = json.loads((build/'build.json').read_text(encoding='utf-8-sig'))
    need(compiled_report['passed'], 'Fresh actual independent compiled build passed')
    # Carry exact expected bindings forward, then physically verify each unique
    # file once after all semantic controls. No metadata cache is involved.
    for category in ('sources', 'source_files', 'tools', 'tool_files', 'libraries',
                     'entry_objects', 'matherr_objects', 'control_objects',
                     'initterm_objects', 'mainargs_objects', 'normal_argv_objects',
                     'commandline_objects', 'producer_objects', 'compiler_read_headers', 'artifacts'):
        for path, digest in compiled_report.get(category, {}).items():
            key = str(pathlib.Path(path).absolute())
            need(key not in module.PINS or module.PINS[key] == digest, 'Unambiguous compiled physical binding')
            module.PINS[key] = digest

    def validate(before, after, scenario):
        domain = module.host_pair(before, after, scenario)
        value = before.read_bytes()
        for i in range(8):
            expected = struct.pack('<QH', 0x8000000000000000+i*0x0101010101010101, 0x3fff+i)
            need(value[32+16*i:42+16*i] == expected, 'Direct hardware BEFORE has every deliberately distinct raw80 register')
        tag = 0xffff
        for i in range(domain['depth']): tag &= ~(3 << (2*((domain['TOP']+i)&7)))
        need(struct.unpack_from('<H', value, 512)[0] == 0xa7f and
             struct.unpack_from('<H', value, 516)[0] == domain['TOP']*2048+0x20 and
             struct.unpack_from('<H', value, 520)[0] == tag,
             'Direct hardware legacy CW/SW/full physical tags match seeded live caller')

    actual = 0
    for level in ('O0', 'O2'):
        for row in sorted((build/level/'actual').glob('case-*'), key=lambda p:int(p.name.split('-')[-1])):
            scenario = int(row.name.split('-')[-1])
            for name in ('writer', 'entry'):
                validate(row/(name+'-host-before.bin'), row/(name+'-host-after.bin'), scenario); actual += 1
    need(actual == 4*json.loads((build/'O0/actual/controls.json').read_text())['scenarios'], 'All rich actual writer/root hardware before fixtures inspected')
    baseline = build/'O0/actual/case-1'
    before = (baseline/'entry-host-before.bin').read_bytes(); after = (baseline/'entry-host-after.bin').read_bytes()
    preservation = list(range(0,5))+list(range(24,28))
    preservation += [32+16*i+k for i in range(8) for k in range(10)]
    preservation += [160+16*i+k for i in range(6,16) for k in range(16)]
    preservation += list(range(512,540))
    before_fixture = list(range(0,5))+list(range(24,28))
    before_fixture += [32+16*i+k for i in range(8) for k in range(10)]
    before_fixture += [160+16*i+k for i in range(6,16) for k in range(16)]
    before_fixture += [512,513,516,517,520,521]+list(range(524,538))
    denials = 0; tests = []
    for direction, offsets in (('after', preservation), ('coherent_wrong_before_fixture', before_fixture)):
        for offset in offsets:
            directory = output/('mutation-'+str(denials)); directory.mkdir()
            b = bytearray(before); a = bytearray(after)
            a[offset] ^= 1
            if direction != 'after': b[offset] ^= 1
            pb = directory/'before.bin'; pa = directory/'after.bin'; pb.write_bytes(b); pa.write_bytes(a)
            rejected = False; message = ''
            try: validate(pb,pa,1)
            except ValueError as error: rejected=True; message=str(error)
            need(rejected, 'Meaningful actual host observer corruption rejected: '+direction+' '+str(offset))
            denials += 1; tests.append({'direction':direction,'offset':offset,'denied':True,'reason':message})
    for size in (543,545):
        directory = output/('mutation-'+str(denials)); directory.mkdir()
        pb = directory/'before.bin'; pa = directory/'after.bin'; pb.write_bytes(before[:size] if size<544 else before+b'\0'); pa.write_bytes(after)
        rejected=False
        try: validate(pb,pa,1)
        except ValueError: rejected=True
        need(rejected, 'Host record extent corruption rejected'); denials+=1
        tests.append({'direction':'wrong_extent','bytes':size,'denied':True})
    files = dict(module.PINS)
    files[str(observer)] = sha(observer); files[str(pathlib.Path(__file__).resolve())] = sha(__file__)
    files[str((build/'build.json').resolve())] = sha(build/'build.json')
    for path,digest in files.items(): need(sha(path)==digest,'Final exact observer-control binding')
    report = {'passed':True,'actual_hardware_raw80_before_fixtures':actual,
              'actual_complete_legacy_tag_before_fixtures':actual,'meaningful_corruption_denials':denials,
              'unique_physical_bindings_verified':len(files),'metadata_only_cache_used':False,
              'observer_path':str(observer),'observer_sha256':OBSERVER_SHA,
              'compiled_build_path':str(build/'build.json'),'tests':tests,'files':files,
              'new_native_executions':False,'guest_result_inferred_from_AFTER':False,
              'volatile_XMM0_5_equality_claimed':False,'whole_M4_complete':False}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key]for key in ('passed','actual_hardware_raw80_before_fixtures','meaningful_corruption_denials')}))

if __name__ == '__main__':
    try:
        need(len(sys.argv)==3,'check_observer.py actual-independent-compiled-build fresh-output')
        main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
    except Exception:
        traceback.print_exc();sys.exit(1)
