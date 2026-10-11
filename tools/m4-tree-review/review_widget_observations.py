"""Independent bounded actual GDI/raw source observation review."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,struct,sys,traceback
R=Path(__file__).resolve().parents[2];PINS={};COUNTS=Counter()
VH='2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c'
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.iso'),'No archive reader');a=sha(p);need(h is None or h==a,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable input');PINS[str(p)]=a;return p
def load(p,h=None):return json.loads(pin(p,h).read_bytes())
def words(b,at=0,n=10):return struct.unpack_from('<'+'I'*n,b,at)
def main(name):
    out=R/'reports/m4-tree-review'/name;need(re.fullmatch('widget-observations-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned output');out.mkdir();passed=False;observations=[]
    try:
        area=R/'reports/m4-widget-original/validation-r1';v=load(area/'report.json',VH)
        need(v['passed']and v['reader_closed']and v['initializer_credit']==0,'Bounded authentic observations only')
        for p,h in v['files'].items():
            if Path(p).suffix.lower()not in('.mwb','.zip'):pin(p,h)
        preflight=load(R/'reports/m4-tree-review/widget-prelaunch-r9/report.json','59bdcd9b3e5bc5260aa71dca6bfcffe110c18b2f79c84cc108c916e3c6b3ede5')
        need(preflight['passed'],'Independent actual current compiled source/observer binding')
        for p,h in preflight['files'].items():pin(p,h)
        roots=load(area/'actual-root-endpoints.json');api=load(area/'actual-GDI-boundaries.json');lifetimes=load(area/'actual-owned-font-lifetimes.json');fs=load(area/'actual-source-FS-events.json');pages=load(area/'actual-whole-page-endpoints.json')
        prep=load(R/'reports/m4-widget-original/preparation-r9/report.json',preflight['preparation_sha256']);contracts=load(Path(next(p for p in prep['files']if Path(p).name=='normal-contracts.json')))
        whole=contracts['whole_pages'];ordinary=prep['observed_pages'];need(len(whole)==64 and len(ordinary)==43,'Exact current source page domain')
        need(len(roots)==5 and len(api)==290 and len(lifetimes)==15 and len(fs)==570 and len(pages)==320,'Actual measured finite observation extent')
        source_returns=[0x5a0142,0x5a0645,0x5a0751];argc=[1,1,14];stock={};owned={};created=[]
        for root in roots:
            raw=pin(root['raw_record'],root['raw_record_sha256']).read_bytes();need(len(raw)==356992,'Fixed exact raw root ABI')
            need(words(raw,36)==tuple(root['CPU_before'])and words(raw,76)==tuple(root['CPU_after']),'Whole raw root CPU joins')
            need(raw[116:628].hex()==root['FX_before_hex']and raw[628:1140].hex()==root['FX_after_hex']and raw[2164:2192].hex()==root['ENV_before_hex']and raw[2192:2220].hex()==root['ENV_after_hex'],'Complete actual root FX/ENV joins')
            need(raw[1140:1652]==raw[1652:2164]and raw[2220:2248]==raw[2248:2276],'Whole outside-caller raw FX512/ENV28 restored')
            need(root['CPU_before'][4]==0x20001800 and root['CPU_before'][9]==root['root']and root['CPU_after'][4]==0x20001804 and root['CPU_after'][9]==0x410a80,'Actual current caller entry/return geometry')
            COUNTS['whole_actual_root_CPU_FX_ENV_relations']+=1
            phase_rows=[x for x in api if x['phase']==root['phase']];need(len(phase_rows)==root['GDI_boundaries'],'Actual source phase boundary count')
            for i,row in enumerate(phase_rows):
                b=pin(row['raw_snapshot'],row['raw_snapshot_sha256']).read_bytes();need(len(b)==266964,'Whole current raw boundary snapshot')
                h=words(b,0,16);cpu=words(b,64);kind=h[3]//2;returned=h[3]%2
                need(list(h)==row['header']and list(cpu)==row['CPU']and h[:3]==(1,i,root['root'])and h[4]==cpu[9]and h[8]==cpu[4]and h[11]==cpu[6]and h[12]==argc[kind],'All actual raw source/API header and CPU values')
                need(b[104:616].hex()==row['FX512_hex']and b[616:644].hex()==row['ENV28_hex']and b[644:708].hex()==row['frame64_hex']and b[708:724].hex()==row['FS_view16_hex'],'Whole raw hardware/live-frame/FS fields')
                def memory(address,n):
                    page=address&~4095;need(page in whole and(address&4095)+n<=4096,'Actual full current source backing');at=4820+whole.index(page)*4096+(address&4095);return b[at:at+n]
                need(memory(cpu[4],64)==b[644:708],'Complete live actual guest stdcall frame')
                if h[14]:need(memory(h[5],16)==b[708:724],'Entire actual current source FS16 frame')
                need([hashlib.sha256(b[4820+j*4096:4820+(j+1)*4096]).hexdigest()for j in range(64)]==row['page_sha256'],'Every whole source page bound to raw snapshot')
                if not returned:
                    need(cpu[9]==h[7]and words(b,644,1)[0]==source_returns[kind],'Actual API target and literal source saved return')
                    args=words(b,648,argc[kind]);need(list(args)==row['arguments'],'Complete source argument vector')
                    if kind==0:need(args==(10,),'Actual stock font identifier')
                    if kind==1:
                        need(memory(cpu[6]+0x258,4)==struct.pack('<I',args[0]),'Actual DeleteObject uses same source object handle field')
                        origin='owned-created'if(cpu[6],args[0])in owned else'borrowed-stock'if stock.get(cpu[6])==args[0]else'unknown'
                        need(origin!='unknown'and row['resource_origin']==origin,'Actual measured same-instance source handle provenance')
                    if kind==2:need(args==(0xfffffff6,6,0,0,500,0,0,0,0,4,0,1,2,0x5e15dc)and memory(0x5e15dc,6)==b'Arial\0','Exact whole current source CreateFontA parameters')
                else:
                    entry=phase_rows[i-1];need(i>0 and entry['side']=='entry'and entry['API']==row['API'],'Actual same API entry/first-source-return pair')
                    need(cpu[9]==source_returns[kind]and cpu[4]==entry['CPU'][4]+4*(argc[kind]+1),'Actual stdcall cleanup and first true source continuation before replay')
                    need(all(cpu[j]==entry['CPU'][j]for j in(3,5,6,7))and h[5]==entry['header'][5],'Actual callee-saved registers and source FS head conserved')
                    if kind==0:stock[cpu[6]]=cpu[0]
                    if kind==1:
                        need(row['BOOL_result']==cpu[0]and row['resource_origin']==entry['resource_origin'],'Actual result remains measured, not inferred deletion')
                        if cpu[0]and entry['resource_origin']=='owned-created':owned.pop((cpu[6],entry['arguments'][0]))
                    if kind==2:
                        need(cpu[0]!=0 and all(handle!=cpu[0]for _,handle in owned),'Observed successful CreateFontA and no unexpired owned alias')
                        record=dict(phase=row['phase'],root=row['root'],instance=cpu[6],handle=cpu[0],created_event=i);created.append(record);owned[cpu[6],cpu[0]]=record
                    COUNTS['actual_'+row['API']+'_pairs']+=1;COUNTS['complete_true_stdcall_RET_pairs']+=1
                COUNTS['whole_actual_GDI_raw_boundaries']+=1;COUNTS['whole_actual_GDI_source_page_endpoints']+=64
            for page in ordinary:
                index=ordinary.index(page);before=raw[2276+index*4096:2276+(index+1)*4096];after=raw[178404+index*4096:178404+(index+1)*4096]
                relation=next(x for x in pages if x['phase']==root['phase']and x['page']==page)
                need(hashlib.sha256(before).hexdigest()==relation['before_sha256']and hashlib.sha256(after).hexdigest()==relation['after_sha256'],'Whole raw ordinary endpoint bytes bound to output relation')
                delta=[dict(offset=i,before=x,after=y)for i,(x,y)in enumerate(zip(before,after))if x!=y]
                need(delta==relation['differences'],'Entire ordinary page difference domain, no mask')
                COUNTS['whole_raw_ordinary_page_endpoint_pairs']+=1
        need(len(created)==15 and len(owned)==15,'Actual fifteen still-live source-owned font occurrences')
        for recorded,resource in zip(created,lifetimes):
            need(all(resource[k]==v for k,v in recorded.items())and resource['live']and resource['deleted_event']is None and resource['manual_cleanup_BOOL']!=0,'Actual creation then separately labeled successful research cleanup')
            need((resource['instance'],resource['handle'])in owned,'Borrowed stock never enters owned research cleanup')
            need(len(bytes.fromhex(resource['manual_cleanup_FX_before_hex']))==len(bytes.fromhex(resource['manual_cleanup_FX_after_hex']))==512 and len(bytes.fromhex(resource['manual_cleanup_ENV_before_hex']))==28,'Whole cleanup raw hardware observations retained')
            # Record equalities only; this is the raw cleanup-call seam rather
            # than a claim about source shutdown callbacks or all host locals.
            observations.append(dict(**recorded,raw_FX512_equal=resource['manual_cleanup_FX_before_hex']==resource['manual_cleanup_FX_after_hex'],raw_ENV28_equal=resource['manual_cleanup_ENV_before_hex']==resource['manual_cleanup_ENV_after_hex']))
            COUNTS['separate_manual_owned_font_lifetimes']+=1
        bindings=load(R/'reports/m4-widget-original/preparation-r9/fs-hook-bindings.json');by_pc={x['PC']:x for x in bindings}
        for row in fs:
            w=row['words'];a=row['CPU_before'];b=row['CPU_after'];need(w[2]in by_pc and row['source_raw']==by_pc[w[2]]['raw_bytes']and a[9]==b[9]==w[2]and w[3]==by_pc[w[2]]['kind'],'Exact physically reviewed source FS instruction')
            need(all(a[i]==b[i]for i in(1,2,3,4,5,6,7,8))and(b[0]==w[4]if w[3]==0 else b[0]==a[0]),'Literal observed FS operation CPU effect')
            need(row['record_before_hex']==row['record_after_hex']and row['FX_before_hex']==row['FX_after_hex']and row['ENV_before_hex']==row['ENV_after_hex'],'Whole current source FS frame/hardware unchanged')
            COUNTS['complete_observed_source_FS_instruction_rows']+=1
        validator=pin(R/'tools/m4-widget-original/validate_v2.py').read_text()
        need('limit==0xffffffff'in validator and'descriptor[5]&128'in validator and'descriptor[6]&64'in validator,'Effective segment limits were explicitly checked by actual executed validator')
        need(v['counts']['actual_flat_DS_ES_SS_descriptor_relations']==870,'Actual declared descriptor count bound; raw descriptor independent recapture remains distinct')
        for key in('source_after_seed','provider_preinvoked','predicted_counts_used','source_model_equivalence','full_reached_source_instruction_trace','source_shutdown_callbacks_executed','source_failure_unwind_admitted','manual_cleanup_is_source_callback','borrowed_stock_deleted_as_owned'):
            need(v[key]is False,'Explicit original observer evidence scope '+key)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        pin(__file__);pin(sys.executable);q=out/'independent-owned-font-observations.json';q.write_text(json.dumps(observations,indent=2)+'\n');pin(q)
        report=dict(passed=passed,validation_sha256=VH,counts=dict(COUNTS),files=PINS,archive_reader_opened=False,worker_launched=False,all_bounded_readers_closed=True,
            actual_selector_descriptor_checker_reviewed=True,raw_selector_descriptor_records_independently_read=False,initializer_credit=0,source_model_equivalence=False,
            scope='Independent raw physical source/GDI/stdcall/handle/FS/root observation review only. Fifteen actual CreateFont objects are distinguished from borrowed stock and manually released outside source shutdown callbacks. Whole source model, repeated virtual/array instruction provenance, loaded API physical export proof, raw independent selector record recheck and connected native acceptance remain separate obligations.')
        q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),files=len(PINS),counts=dict(COUNTS))))
if __name__=='__main__':main(sys.argv[1])
