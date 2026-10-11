"""Independent bounded physical joins and observer scope of the genuine trace."""
from pathlib import Path
import collections, hashlib, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS, ARCHIVES={},{}
VSHA='be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f'
def need(x,s):
    if not x: raise ValueError(s)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture archive opened');v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical pin');PINS[str(p)]=v;return p
def load(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def u(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def cpu(c,pc=None):
    v=[u(c,i)[0]for i in(176,172,168,164,196,180,160,156,192,184)];v[8]&=~0x10100
    if pc is not None:v[9]=pc
    return v
def main(name):
    out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Additive output')
    vd=R/'reports/m4-hypot-original/trace-validation-r2';v=load(vd/'report.json',VSHA)
    need(v['passed']and v['reader_closed']and not v['canonical_debugger_FIP_FDP_claimed']and not v['debugger_metadata_replaced'],'Authentic current bounded observation scope')
    need(v['debugger_write_sections']=='CONTROL only'and v['TF_RF_projection_mask']==0x10100,'Exact declared debugger projection')
    for field in('source_after_seed','numerical_model_used','native_executed','source_native_equivalence'):need(v[field]is False,'No invented downstream credit '+field)
    for p,h in v['files'].items():
        if Path(p).suffix.lower()in('.mwb','.zip'):ARCHIVES[p]=h
        else:pin(p,h)
    pre=load(R/'reports/m4-tree-review/hypot-trace-prelaunch-r8/report.json','88ecbc021715bbf926b454eb962742c5f52a3b6db047c41b85899cdd8935e4a7')
    need(pre['passed'],'Independent current compiled tracer prelaunch')
    e=load(v['execution_path'],v['execution_sha256']);b=load(e['build_path'],e['build_sha256']);pdir=Path(b['preparation']);p=load(pdir/'report.json',b['preparation_sha256'])
    need(e['passed']and b['passed']and b['preparation_sha256']=='94a53e0fffb364f0265e86d54c43e215b3f454aa24e97b5da21573e091bc6b86','Actual admitted corrected writer lineage')
    points=load(pdir/'trace-instruction-contracts.json')['instructions'];point={x['pc']:x for x in points};need(len(points)==len(point)==3538,'Authentic immutable complete descriptor domain')
    traces=load(vd/'actual-source-traces.json');accesses=load(vd/'actual-source-accesses.json');need(len(traces)==6 and len(accesses)==3696,'Exact current bounded exported observations')
    indexed={(x['sequence'],x['instruction_index'],x['operand_index']):x for x in accesses};need(len(indexed)==len(accesses),'No duplicate operand identity')
    normal_path=R/'reports/m4-hypot-original/prefix-validation-r2/report.json'
    normal=load(normal_path,v['normal_canonical_ENV_gate_sha256']);normal_rows=load(normal_path.parent/'actual-hypot-endpoints.json')
    need(normal['passed']and normal['reader_closed']and normal['counts']['actual_final_canonical_FIP_FDP_overwrite_relations']==6,'Separate actual untraced canonical ENV proof')
    counts=collections.Counter();all_PCs=set();api_sides=[]
    for seq,row in enumerate(traces):
        need(row['sequence']==seq and row['event_count']==1007 and row['API_count']==2 and not row['unobserved_external_instruction_intervals'],'Actual complete finite source path')
        raw_events=pin(vd/f'raw-observations/case-{seq}-events.bin').read_bytes()
        raw_apis=pin(vd/f'raw-observations/case-{seq}-APIs.bin').read_bytes()
        record=pin(vd/f'raw-observations/case-{seq}-record.bin').read_bytes()
        need(len(raw_events)==1007*1840 and len(raw_apis)==2*9800 and len(record)==356992,'Whole actual immutable trace/API/root extents')
        need(record[36:76]==struct.pack('<10I',*row['own_BEFORE_CPU'])and record[76:116]==struct.pack('<10I',*row['own_AFTER_CPU']),'Actual root CPU fields at fixed ABI offsets')
        for field,a,z in(('own_BEFORE_FX512_hex',116,628),('own_AFTER_FX512_hex',628,1140),('own_BEFORE_ENV28_hex',2164,2192),('own_AFTER_ENV28_hex',2192,2220)):
            need(record[a:z].hex()==row[field],'Whole actual root hardware endpoint '+field)
        need(record[1140:1652]==record[1652:2164]and record[2220:2248]==record[2248:2276],'Actual outside host FX512/ENV28 restoration in these finite original cases')
        need(record[2204:2218]==bytes(14),'Raw debugger final metadata remains zero, never replaced')
        need(bytes.fromhex(normal_rows[seq]['AFTER_ENV28_hex'])[12:26]!=bytes(14),'Separately preserved normal canonical metadata differs from raw debugger result')
        for index,q in enumerate(row['instructions']):
            raw=raw_events[index*1840:(index+1)*1840];h=u(raw,0,8);desc=point[q['PC']]
            need(h[:4]==(index,q['PC'],q['next_PC'],q['PC']+1)and h[4]==desc['opcode']and h[5]==q['cell_count']==len(desc['cells']),'Every actual complete source/control descriptor header')
            before,after=raw[32:748],raw[748:1464];bc=cpu(before,q['PC']);ac=cpu(after)
            need(bc==q['BEFORE_CPU']and ac==q['AFTER_CPU']and u(before,184)[0]==q['PC']+1,'Both complete stopped CONTEXT sides and explicit breakpoint PC projection')
            need(u(before,192)[0]==q['source_flags_before_raw']and u(after,192)[0]==q['source_flags_after_raw'],'Full raw EFlags retained before declared TF/RF projection')
            need(u(raw,1832,2)==tuple(q['FS_heads']),'Actual per-instruction FS head endpoints')
            if index:
                prev=row['instructions'][index-1];need(prev['next_PC']==q['PC']and prev['AFTER_CPU'][:9]==bc[:9],'Actual zero-gap carried source GPR/architectural flags')
            for n,d in enumerate(desc['cells']):
                raw_cell=raw[1464+n*60:1524+n*60];obs=indexed[seq,index,n]
                address=(d['displacement']+sum(bc[k]*c for k,c in enumerate(d['coefficients']))+(row['TEB']if d['segment']else 0))&0xffffffff
                need(u(raw_cell,0,7)==(address,d['width'],d['read'],d['write'],d['segment'],1,1),'Entire actual operand geometry/status')
                need(obs['PC']==q['PC']and obs['address']==address and obs['width']==d['width']and obs['read']==d['read']and obs['write']==d['write']and obs['segment']==d['segment'],'Every bound exact source operand identity')
                need(raw_cell[28:28+d['width']].hex()==obs['before_hex']and raw_cell[44:44+d['width']].hex()==obs['after_hex'],'Whole observed operand byte values, without expected numeric seed')
                if not d['write']:need(obs['before_hex']==obs['after_hex'],'Actual read-only operand unchanged during its instruction')
                counts['operands']+=1;counts['reads']+=bool(d['read']);counts['writes']+=bool(d['write'])
            counts['instructions']+=1;counts['CONTEXT_sides']+=2;all_PCs.add(q['PC'])
        for i,a in enumerate(row['APIs']):
            raw=raw_apis[i*9800:(i+1)*9800];h=u(raw,0,12);entry,after=raw[48:764],raw[764:1480]
            need(a['import_name']=='_hypot'and a['target']==0x7802a122 and a['owning_IAT']==0x5bb5b0 and a['source_PC']in(0x4b58b8,0x4b58e3),'Exact actual genuine named call identity')
            need(h[:4]==(i,a['source_PC'],a['target'],a['return_PC'])and h[5:8]==(4,1,a['thread']),'Entire actual cdecl API metadata')
            need(entry.hex()==a['ENTRY_CONTEXT716_hex']and after.hex()==a['AFTER_CONTEXT716_hex'],'Both whole raw API CONTEXT716 observations')
            for field,start,end in(('entry_frame64_hex',1480,1544),('returned_frame64_hex',1544,1608),('entry_whole_stack_hex',1608,5704),('returned_whole_stack_hex',5704,9800)):
                need(raw[start:end].hex()==a[field],'Whole observed genuine API stack/frame '+field)
            ec,ac=cpu(entry),cpu(after);need(ec==a['ENTRY_CPU']and ac==a['AFTER_CPU']and ac[4]==ec[4]+4,'Actual cdecl saved return/ESP+4')
            need(raw[1480:1484]==struct.pack('<I',a['return_PC'])and raw[1484:1500].hex()==a['actual_F64_arguments_hex'],'Exact actual source caller arguments and saved return')
            need(after[236:246].hex()==a['actual_return_raw80_hex']==normal_rows[seq]['calls'][2*i+1]['actual_return_raw80_hex'],'Trace/untraced raw80 observation comparison only')
            counts['cdecl_intervals']+=1;counts['API_CONTEXT_sides']+=2
        counts['phases']+=1;counts['raw_debugger_ENVs']+=1
    need(dict(counts)==dict(operands=3696,reads=1938,writes=1758,instructions=6042,CONTEXT_sides=12084,cdecl_intervals=12,API_CONTEXT_sides=24,phases=6,raw_debugger_ENVs=6),'Complete measured current extent')
    validator=pin(R/'tools/m4-hypot-original/validate_trace_v2.py').read_text()
    need('canonical_debugger_FIP_FDP_claimed=False' in validator and 'debugger_metadata_replaced=False' in validator and 'normal_numerical_results_are_observation_comparison_only=True' in validator,'Executed validator preserves exact metadata/numerical scope')
    need("capture.close();capture.entries.clear();capture.bundles.clear();capture=None" in validator,'All actual archive aliases explicitly closed by producer')
    pin(__file__);pin(sys.executable)
    out.mkdir();target=out/'report.json';target.write_text(json.dumps(dict(passed=True,validation_sha256=VSHA,execution_sha256=v['execution_sha256'],
        prelaunch_sha256='88ecbc021715bbf926b454eb962742c5f52a3b6db047c41b85899cdd8935e4a7',counts=dict(counts),unique_actual_source_PCs=len(all_PCs),
        canonical_debugger_FIP_FDP_claimed=False,debugger_metadata_replaced=False,normal_canonical_gate_sha256=v['normal_canonical_ENV_gate_sha256'],
        numerical_prediction_credit=0,native_credit=0,initializer_credit=0,archive_reader_opened=False,
        scope='Independent exact physical joins of retained complete raw instruction/API/context/operand/root observations and fixed ABI, not a literal math predictor. '
              'Actual debugger latent ENV metadata remains zero and carries no canonical equivalence claim. The separately authenticated untraced canonical ENV gate is retained. '
              'Raw80 and F32 trace/normal relationships compare two observations; they seed no native/source output. Full native/source/provider equivalence and arbitrary caller domains remain separate.',
        files=PINS,retained_archive_declarations_not_rehashed=ARCHIVES),indent=2)+'\n')
    print(json.dumps(dict(passed=True,path=str(target),sha256=sha(target),files=len(PINS),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
