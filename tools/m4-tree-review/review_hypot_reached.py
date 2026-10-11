"""Independent finite source/IR/COFF preparation review; never a native run."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}

def need(value, why):
    if not value: raise ValueError(why)

def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(path, expected=None):
    path = Path(path).resolve()
    need(path.suffix.lower() not in ('.mwb', '.zip'), 'No archive consumer')
    digest = sha(path)
    need(expected is None or digest == expected, 'Physical identity ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'Immutable physical identity')
    PINS[str(path)] = digest
    return path

def read(path, expected=None): return json.loads(pin(path, expected).read_text(encoding='utf-8-sig'))

def module(path, name):
    s = importlib.util.spec_from_file_location(name, pin(path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main(name):
    out = R/'reports/m4-tree-review'/name
    need(re.fullmatch('hypot-reached-r[1-9][0-9]*', name) and not out.exists(), 'Fresh owned revision')
    area = R/'reports/m4-hypot-native'
    digests = {'lifts-r4': 'fff190c4797cc82c018982c5c247b652cc6e307c2e184953dc620275f133b9f3',
               'lifts-r5': 'fd5186d1619078be2d03c3e05bf7ec1b251190e3af58d12f15d25b331b1ea01f',
               'reached-domain-r1': '3c47c52775937a8831ca4ef3642e4d48d28ab4c4f4f6302fce58888e7edadcc2'}
    reports = {k: read(area/k/'report.json', h) for k,h in digests.items()}
    for j in reports.values():
        need(j['passed'] is True and j['source_after_seed'] is False and j['numerical_expected_seed'] is False
             and j['initializer_credit'] == 0, 'Preparation only, no numeric/AFTER seed')
        for p,h in j['files'].items():
            if Path(p).suffix.lower() not in ('.mwb','.zip'): pin(p,h)
    domain = reports['reached-domain-r1']
    for k in ('native_linked','native_executed','source_native_equivalence','cold_source_domain_admitted'):
        need(domain[k] is False, 'No ' + k + ' claim')
    trace_path = R/'reports/m4-hypot-original/trace-validation-r2/report.json'
    trace = read(trace_path, 'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')
    independent_path = R/'reports/m4-tree-review/hypot-trace-actual-r1/report.json'
    independent = read(independent_path, '92c18c03c0b24c9f4c8aeccea8c4efbdcfea8c864e744415c09b70605a3e2421')
    need(trace['passed'] and trace['reader_closed'] and independent['passed']
         and not trace['canonical_debugger_FIP_FDP_claimed'], 'Current genuine trace and separate bounded review')
    observations = read(trace_path.parent/'actual-source-traces.json')
    need(len(observations)==6 and all(o['event_count']==1007 for o in observations), 'Six complete finite traces')
    reached = set(map(int, observations[0]['actual_reached_PC_counts']))
    need(len(reached)==439 and all(set(map(int,o['actual_reached_PC_counts']))==reached for o in observations), 'Shared actual PC domain')
    PE = module(R/'tools/analysis/pe.py','hypot_reached_PE')
    images = {'game': PE.PEImage(pin(R/'MW3/Mech3.exe').read_bytes()),
              'crt': PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())}
    recovery = R/'reports/m4-hypot-original/recovery-r1'
    graph_maps = {owner: read(recovery/file) for owner,file in
                  [('game','game-graphs.json'),('crt','CRT-provider-graphs.json')]}
    physical_source = {}
    for owner,graphs in graph_maps.items():
        for g in graphs.values():
            for row in g['instructions']:
                pc=row['pc']; raw=bytes.fromhex(row['bytes']); image=images[owner]
                offset,_=image.rva_range(pc-image.image_base,len(raw))
                need(image.data[offset:offset+len(raw)]==raw and len(raw)==row['size'], 'Literal source PE bytes')
                identity=(owner,row['bytes'],row['size'],row['mnemonic'],row['operands'])
                need(pc not in physical_source or physical_source[pc]==identity, 'Shared decode identity')
                physical_source[pc]=identity
    C = module(R/'tools/m4-tree-review/amd64_coff.py','hypot_reached_coff')
    control = module(R/'tools/m4-hypot-native/control_ir.py','hypot_reached_control')
    helper = module(R/'tools/m4-widget-source/lift.py','hypot_reached_FP')
    bodies = {}; owners=collections.defaultdict(list); previous=set(); new=set(); bytes_new=set()
    object_rows=[]; repaired=[]; padding_rows=[]
    expected_new={0x7802c2aa,0x7802cdf1,0x7802d089,0x7802d29b,0x7802d303,0x7802c277}
    need({b['entry'] for b in reports['lifts-r5']['bodies'].values()}==expected_new, 'Exact six additional source entries')
    for revision in ('lifts-r4','lifts-r5'):
        report=reports[revision]; folder=area/revision
        for symbol,b in report['bodies'].items():
            need(symbol not in bodies and b['execution_admitted'] is False and b['initializer_credit']==0, 'Distinct unadmitted source bodies')
            need(b['layouts']['struct.State']['size']==3504 and set(b['objects'])=={'O0','O2'}, 'Exact State and two compiler levels')
            rows=b['physical_instructions']; need(rows and rows[0]['pc']==b['entry'], 'Literal entry owns first source row')
            source=pin(folder/(symbol+'-source.bin')).read_bytes(); assigned={}
            for row in rows:
                pc=row['pc']; need(physical_source[pc]==(b['owner'],row['bytes'],row['size'],row['mnemonic'],row['operands']), 'Every compiled instruction matches physical recovery')
                raw=bytes.fromhex(row['bytes']); need(source[pc-b['entry']:pc-b['entry']+len(raw)]==raw, 'Exact lifter input bytes')
                for at,byte in enumerate(raw,pc-b['entry']):
                    need(at not in assigned,'No overlapping code placement'); assigned[at]=byte
                owners[pc].append(symbol)
                (previous if revision=='lifts-r4' else new).add(pc)
                if revision=='lifts-r5': bytes_new.update(range(pc,pc+len(raw)))
            need(len(assigned)==b['physical_bytes'] and len(source)==b['source_span_bytes'], 'Whole physical and padded span counts')
            padding=[i for i in range(len(source)) if i not in assigned]
            need(all(source[i]==0xcc for i in padding),'Every unassigned source byte is explicit INT3 padding')
            if revision=='lifts-r5':
                need(set(r['pc'] for r in rows)<=reached, 'New compilation contains only reached rows')
                need(all(r['pc'] not in reached for r in b['omitted_unreached_rows']), 'Declared omitted rows are genuinely unreached')
                baseline=pin(folder/(symbol+'-baseline.ll')).read_text()
                transformed,records=control.repair(baseline,dict(entry=b['entry'],instructions=rows))
                transformed,counts=helper.strict_fp(transformed)
                transformed=transformed.replace('mw34_onexit_game_fsqrt_raw80','mw34_hypot_fsqrt_raw80')
                need(transformed==pin(folder/(symbol+'-guest.ll')).read_text() and counts==b['strict_FP']
                     and records==b['CW_transfers'], 'Whole exact reversible control and strict-FP transformation')
                repaired.extend(dict(symbol=symbol,**record) for record in records)
                padding_rows.append(dict(symbol=symbol,padding_bytes=len(padding),omitted_rows=len(b['omitted_unreached_rows'])))
            host=pin(folder/(symbol+'-host.ll'),b['host_sha256']).read_text(); body_name='mw34_hypot_'+symbol+'_body'
            need(host.count('define ptr @'+body_name+'(')==1 and 'target triple = "x86_64-pc-windows-msvc"' in host, 'One actual AMD64 host IR body')
            for level,q in b['objects'].items():
                obj=pin(q['path'],q['sha256']); symbols,sections=C.parse(obj.read_bytes())
                raw,relocs=C.function(symbols,sections,body_name)
                need(raw and all(0<=r['offset']<len(raw) for r in relocs),'Nonempty whole actual AMD64 function and bounded relocations')
                matching=[c for c in report['commands'] if Path(c['argv'][0]).name.lower()=='clang.exe'
                          and str(obj) in c['argv'] and '-'+level in c['argv']]
                need(len(matching)==1 and matching[0]['exit_code']==0
                     and '--target=x86_64-pc-windows-msvc' in matching[0]['argv']
                     and str(folder/(symbol+'-host.ll')) in matching[0]['argv'], 'Actual compiler command consumes the exact host IR')
                object_rows.append(dict(symbol=symbol,level=level,object_path=str(obj),object_sha256=q['sha256'],
                    function_bytes=len(raw),function_sha256=hashlib.sha256(raw).hexdigest(),
                    relocations=[dict(offset=r['offset'],type=r['type'],symbol=r['symbol']['name']) for r in relocs]))
            bodies[symbol]=b
    need(len(new)==135 and len(bytes_new)==316 and reached<=set(owners) and len(reached&previous)==304, 'Exact additional and inherited reached coverage')
    need([(r['physical_PC'],r['instruction']) for r in repaired]==[(0x7802d2ee,'wait'),(0x7802c2a5,'fldcw')], 'Only two new control instruction seams')
    joins=read(area/'reached-domain-r1/source-PC-joins.json'); expected=[]
    for o in observations:
        counted=collections.Counter()
        for row in o['instructions']:
            pc=row['PC']; need(row['BEFORE_CPU'][9]==pc and row['AFTER_CPU'][9]==row['next_PC'],'Actual observed instruction boundaries')
            counted[pc]+=1
            expected.append(dict(sequence=o['sequence'],index=row['index'],PC=pc,source_bytes=physical_source[pc][1],native_body_candidates=owners[pc]))
        need(dict(counted)=={int(k):v for k,v in o['actual_reached_PC_counts'].items()}, 'Complete genuine per-case reached occurrence inventory')
    need(joins==expected and len(joins)==6042,'Every compiled coverage join is exact actual trace PC/physical byte identity')
    inventory=read(area/'reached-domain-r1/literal-bodies.json'); need(set(inventory)==set(bodies),'Complete literal dispatch body inventory')
    header=pin(area/'reached-domain-r1/literal_dispatch.hpp').read_text()
    actual=[(int(a,16),s,f=='true') for a,s,f in re.findall(r'\{(0x[0-9a-f]+), &(mw34_hypot_f_[0-9a-f]+_body), (true|false)\}',header)]
    need(actual==[(b['entry'],'mw34_hypot_'+s+'_body',b['machine_fragment']) for s,b in bodies.items()], 'Exact 21-entry prepared dispatch, including four true machine fragments')
    pin(__file__);pin(sys.executable)
    out.mkdir()
    for filename,value in [('COFF-observations.json',object_rows),('control-seams.json',repaired),('padding-observations.json',padding_rows)]:
        p=out/filename;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
    result=dict(passed=True,lifts_sha256=digests['lifts-r5'],domain_sha256=digests['reached-domain-r1'],
        original_trace_sha256=sha(trace_path),independent_trace_sha256=sha(independent_path),
        counts=dict(genuine_cases=6,actual_instruction_joins=6042,unique_reached_PCs=439,inherited_reached_PCs=304,
                    additional_reached_PCs=135,additional_physical_bytes=316,literal_bodies=21,actual_COFF_functions=42,
                    new_reversible_control_seams=2,compiled_unreached_existing_PCs=len(previous-reached)),
        source_after_seed=False,numerical_expected_seed=False,archive_reader_opened=False,native_linked=False,
        native_executed=False,initializer_credit=0,hardware_control_instruction_equivalence=False,
        scope='Independent exact physical source, whole instruction-local IR transformation, actual two-level COFF membership and '
              'genuine observed PC coverage review only. New bodies contain reached rows and exact CC padding. The inherited corpus '
              'also contains unobserved decoded rows, so this receipt does not prove cold-path refusal or a final Runtime PC guard. '
              'No linked execution, independent numerical prediction, helper equivalence or initializer acceptance is claimed.',files=PINS)
    p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),counts=result['counts'],files=len(PINS))))

if __name__=='__main__': main(sys.argv[1])
