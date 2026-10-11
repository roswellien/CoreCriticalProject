"""Independent exact-PC audit of every prepared constructor source IR store."""
from pathlib import Path
from collections import Counter,deque
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
GPR={'eax':2216,'ebx':2232,'ecx':2248,'edx':2264,'esi':2280,'edi':2296,'esp':2312,'ebp':2328,'pc':2472}
SEG={'ss':2120,'es':2136,'gs':2152,'fs':2168,'ds':2184,'cs':2200}
FIELDS={v:'gpr:'+k for k,v in GPR.items()}|{v:'seg:'+k for k,v in SEG.items()}

def need(v,m):
    if not v:raise ValueError(m)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def e(c=0,terms=None,bits=32):return {'c':c&((1<<bits)-1),'terms':{k:v&((1<<bits)-1)for k,v in sorted((terms or {}).items())if v&((1<<bits)-1)},'bits':bits}
def atom(name,bits=32):return e(terms={name:1},bits=bits)
def plus(a,b,sign=1):
    if a is None or b is None:return None
    need(a['bits']==b['bits']==32,'Only exact DWORD affine arithmetic needed for current stores')
    terms=dict(a['terms'])
    for k,v in b['terms'].items():terms[k]=terms.get(k,0)+v*sign
    return e(a['c']+b['c']*sign,terms)
def narrow(a,bits):
    if a is None:return None
    if a['bits']==bits:return a
    if not a['terms']:return e(a['c'],bits=bits)
    if len(a['terms'])==1 and a['c']==0 and next(iter(a['terms'].values()))==1:
        name=next(iter(a['terms']));name=re.sub(r':bits\d+$',f':bits{bits}',name)
        return atom(name,bits)
    return None
def widen(a,bits):
    if a is None:return None
    if a['bits']==bits:return a
    return e(a['c'],a['terms'],bits)
def field_atom(offset,bits):
    if offset in FIELDS:return atom(FIELDS[offset]+f':bits{bits}',bits)
    if offset-1 in FIELDS and bits==8:return atom(FIELDS[offset-1]+':shift8:bits8',8)
    return atom('state-offset:'+str(offset)+f':bits{bits}',bits)
def expected_ea(d):
    a=d['address'];terms={'seg:'+a['segment']+':bits32':1}
    if a['base']:terms['gpr:'+a['base']+':bits32']=terms.get('gpr:'+a['base']+':bits32',0)+1
    if a['index']:terms['gpr:'+a['index']+':bits32']=terms.get('gpr:'+a['index']+':bits32',0)+a['scale']
    return e(a['displacement'],terms)
def expected_value(d,last_read):
    v=d['value'];bits=d['width']*8
    if v['kind']=='immediate':return e(v['immediate'],bits=bits)
    if v['kind']=='register':return atom('gpr:'+v['register']+(f":shift{v['shift']}"if v['shift']else'')+f':bits{bits}',bits)
    need(last_read is not None,'Literal same-block RMW prior read required')
    return plus(last_read['value'],e(v['immediate']))
def function_blocks(text):
    at=text.index('define ptr @');body=text[at:];body=body[:body.index('\n}\n')]
    split=re.split(r'(?m)^([A-Za-z0-9_$.-]+):[^\n]*\n',body)
    return split[0],{split[i]:split[i+1]for i in range(1,len(split),2)}
def constant_pointer_offsets(text):
    pointers={}
    for line in text.splitlines():
        match=re.fullmatch(r'  (%\w+) = getelementptr inbounds(?: nuw)? i8, ptr %state, i32 (\d+)',line)
        if match:pointers[match[1]]=int(match[2]);continue
        match=re.fullmatch(r'  (%\w+) = getelementptr inbounds %struct.State, ptr %state, i32 0, i32 0, i32 (5|6), i32 (\d+), i32 0, i32 0',line)
        if match:pointers[match[1]]=(2112 if match[2]=='5'else 2208)+int(match[3])*8
    return pointers
def pc_blocks(entry,blocks,rows):
    queue=deque([(next(iter(blocks)),entry)]);mapped={}
    while queue:
        label,pc=queue.popleft()
        if label in mapped:need(mapped[label]==pc,'Unique exact current physical PC for shared IR block '+label);continue
        need(label in blocks and pc in rows,'Whole compiled source IR block has exact frozen physical instruction '+hex(pc))
        block=blocks[label];row=rows[pc]
        header=re.match(r'  (%\d+) = load i32, ptr %NEXT_PC, align 4\n  store i32 \1, ptr %PC, align 4\n  (%\d+) = add i32 \1, (\d+)\n',block)
        need(header is None or int(header[3])==row['size'],'Exact physicalPC/whole source size block header '+hex(pc)+'/'+label)
        mapped[label]=pc
        edges=re.findall(r'^  br (.+)$',block,re.M)
        need(len(edges)<=1,'One source instruction branch in IR block '+hex(pc))
        if not edges:continue
        branch=edges[0];conditional=re.fullmatch(r'i1 %\d+, label %([A-Za-z0-9_$.-]+), label %([A-Za-z0-9_$.-]+)',branch)
        if conditional:
            architectural=bool(re.search(r'= load i8, ptr %BRANCH_TAKEN, align 1\n  %\d+ = icmp eq i8 %\d+, 1\n  br i1',block))
            if architectural:
                need(row['mnemonic'].startswith('j')and row['mnemonic']!='jmp','Physical conditional branch attribution')
                target=int(row['operands'].split()[0],0);queue.extend([(conditional[1],target),(conditional[2],pc+row['size'])])
            else:
                for destination in conditional.groups():
                    begins_instruction=blocks[destination].startswith('  %')and bool(re.match(r'  %\d+ = load i32, ptr %NEXT_PC, align 4\n  store i32 %\d+, ptr %PC, align 4\n',blocks[destination]))
                    queue.append((destination,pc+row['size']if begins_instruction else pc))
        else:
            edge=re.fullmatch(r'label %([A-Za-z0-9_$.-]+)',branch);need(edge is not None,'Exact source unconditional IR edge '+hex(pc)+'/'+label+' '+branch)
            begins_instruction=bool(re.match(r'  %\d+ = load i32, ptr %NEXT_PC, align 4\n  store i32 %\d+, ptr %PC, align 4\n',blocks[edge[1]]))
            target=(int(row['operands'].split()[0],0)if row['mnemonic']=='jmp'else pc+row['size'])if begins_instruction else pc
            queue.append((edge[1],target))
    need(len(mapped)==len(blocks),'Every prepared body IR block has a physical-PC attribution '+hex(entry)+' '+str((len(mapped),len(blocks))))
    return mapped

def audit_block(body,label,pc,block,row,store,pointers):
    values={};local_memory={'%NEXT_PC':e(pc)};state_writes=[];read_callbacks=[];writes=[];lines=block.splitlines()
    def value(token,bits=32):
        if token.startswith('%'):return values.get(token)
        try:return e(int(token),bits=bits)
        except ValueError:return None
    for line_index,line in enumerate(lines):
        match=re.fullmatch(r'  (%\d+) = load i(8|16|32), ptr (%\w+), align \d+',line)
        if match:
            name,bits,pointer=match[1],int(match[2]),match[3]
            values[name]=local_memory.get(pointer)if pointer in local_memory else field_atom(pointers[pointer],bits)if pointer in pointers else None
            continue
        match=re.fullmatch(r'  (%\d+) = (add|sub) i32 ([^,]+), (\S+)',line)
        if match:values[match[1]]=plus(value(match[3]),value(match[4]),1 if match[2]=='add'else-1);continue
        match=re.fullmatch(r'  (%\d+) = (trunc|zext) i(8|16|32) (\S+) to i(8|16|32)',line)
        if match:values[match[1]]=(narrow if match[2]=='trunc'else widen)(value(match[4],int(match[3])),int(match[5]));continue
        match=re.fullmatch(r'  store i(8|16|32) ([^,]+), ptr (%\w+), align \d+',line)
        if match:
            bits=int(match[1]);v=value(match[2],bits);pointer=match[3]
            if pointer in ('%NEXT_PC','%RETURN_PC'):local_memory[pointer]=v
            if pointer in pointers:state_writes.append(dict(line=line_index,offset=pointers[pointer],width=bits//8,value=v,text=line))
            continue
        match=re.fullmatch(r'  (%\d+) = call (?:noundef )?(?:zeroext )?i(8|16|32) @mw34_(?:constructor|onexit)_game_read(8|16|32)\(ptr noundef %\w+, i32 noundef (\S+)\) #\d+',line)
        if match:
            bits=int(match[2]);need(bits==int(match[3]),'Exact source read callback scalar width')
            v=atom('read:'+body+':'+label+':'+match[1]+f':bits{bits}',bits)
            item=dict(line=line_index,result=match[1],address=value(match[4]),width=bits//8,value=v,text=line)
            values[match[1]]=v;read_callbacks.append(item);continue
        match=re.fullmatch(r'  (%\d+) = call (?:noundef )?ptr @mw34_(?:constructor|onexit)_game_write(8|16|32)\(ptr noundef %\w+, i32 noundef (\S+), i(8|16|32) noundef (?:zeroext )?(\S+)\) #\d+',line)
        if match:
            bits=int(match[2]);need(bits==int(match[4]),'Exact source write callback scalar width')
            writes.append(dict(line=line_index,width=bits//8,address=value(match[3]),value=value(match[5],bits),text=line))
    if store is None:need(not writes,'No mirror callback at non-writing physical source instruction '+hex(pc));return None
    need(len(writes)==1,'One actual callback for every prepared physical store '+hex(pc)+'/'+label+' count'+str(len(writes)))
    write=writes[0];need(write['width']==store['width']and write['address']==expected_ea(store),'Actual source IR effective address equals independent physical affine store descriptor '+hex(pc)+' '+str(write['address']))
    prior=[r for r in read_callbacks if r['line']<write['line']];last_read=prior[-1]if prior else None
    need(write['value']==expected_value(store,last_read),'Actual source IR value equals physical incoming State/immediate/prior-read store descriptor '+hex(pc)+' '+str(write['value']))
    dependencies={SEG[store['address']['segment']]}
    for key in ('base','index'):
        if store['address'][key]:dependencies.add(GPR[store['address'][key]])
    if store['value']['kind']=='register':dependencies.add(GPR[store['value']['register']])
    before=[v for v in state_writes if v['line']<write['line']]
    need(all(not any(v['offset']<offset+4 and offset<v['offset']+v['width']for offset in dependencies)for v in before),'No source State address/value register/segment mutation before callback '+hex(pc))
    pcs=[v for v in before if v['offset']==GPR['pc']]
    need(pcs and pcs[-1]['value']==e(pc),'Actual State PC remains exact physical store PC at callback '+hex(pc))
    if store['kind']in('PUSH','CALL'):
        esp=[v for v in state_writes if v['offset']==GPR['esp']]
        need(len(esp)==1 and esp[0]['line']>write['line']and esp[0]['value']==plus(atom('gpr:esp:bits32'),e(-4)),'Source ESP decrement publication follows actual PUSH/CALL callback '+hex(pc))
    if store['kind']=='ADD':
        need(last_read and last_read['width']==4 and last_read['address']==write['address']and len(prior)==1,'Genuine single same-PC/source-EA DWORD prior read supplies RMW '+hex(pc))
        flags=[v for v in state_writes if 2064<=v['offset']<2080]
        need(flags and all(v['line']>write['line']for v in flags),'RMW read/write before architectural arithmetic flags publication '+hex(pc))
    return dict(body=body,label=label,pc=pc,source_instruction=row,kind=store['kind'],width=store['width'],write_callback=write,prior_reads=prior,State_dependencies=sorted(dependencies),State_writes=state_writes,address_expression_matches=True,value_expression_matches=True,relevant_State_unchanged_before_callback=True,whole_block_text=block)

def main(name):
    pins={};counts=Counter();source_findings=[]
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip')and p.name not in('payload.bin','index.json','transport.json'),'No archive or raw capture reader')
        actual=sha(p);need(h is None or actual==h,'Exact frozen source '+str(p));pins[str(p)]=actual;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    prep_path=ROOT/'reports/m4-constructor-native/preparation-r4/report.json';prep=read(prep_path,'66aac363ce562a8960e92faf7731111172bb2ea48ee31f04eb99d9de82baf969')
    operands_path=ROOT/'reports/m4-constructor-native/store-operands-r1/report.json';operands=read(operands_path,'56acaf9dffcf68355d6a68bcd28ef841e084208e9f10724a8a14d3d06ed63d33')
    contracts=read(operands['contracts_path'],operands['contracts_sha256']);pin(operands['guard_path'],operands['guard_sha256']);stores={r['pc']:r for r in contracts['stores']}
    source=read(ROOT/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf')
    rows_path=ROOT/'reports/m4-constructor-source/preparation-r1/source-instructions.json';rows=read(rows_path,source['files'][str(rows_path.resolve())]);by_pc={r['pc']:r for r in rows}
    graphs_path=ROOT/'reports/m4-remaining-service-source/preparation-r2/all-seven-graphs.json';graphs=read(graphs_path,source['files'][str(graphs_path.resolve())])
    entries=read(ROOT/'reports/m4-constructor-native/entry-preparation-r1/report.json','4d19363697529ff122d2ccd0127ec532a313d6e13da3b1eee902905604fd299c')
    entry_lifts=read(ROOT/'reports/m4-constructor-native/entry-lifts-r1/report.json','e6082e83ba2c48342ca13c26e79e2b63a6533726d222e64b96cb17cece5e7103')
    bodies=[]
    for row in prep['namespace_relations']:
        original=pin(row['original_IR'],row['original_sha256']);path=pin(row['component_IR'],row['component_sha256']);need(path.read_text()==original.read_text().replace('mw34_onexit_game_','mw34_constructor_game_'),'Exact namespace-only current source body');bodies.append((row['entry'],path))
    for entry in (0x4c0310,0x4c0570):
        path=ROOT/f'reports/m4-constructor-native/entry-lifts-r1/f_{entry:x}-host.ll';pin(path,entry_lifts['source_bodies'][f'f_{entry:x}']['host_sha256']);bodies.append((entry,path))
    need(len(bodies)==len({r[0]for r in bodies})==33,'All exact current prepared31 bodies plus2 fresh missing tail bodies')
    callbacks=[];attributions=[];compiled_PC=set()
    for entry,path in bodies:
        text=path.read_text();prefix,blocks=function_blocks(text);mapping=pc_blocks(entry,blocks,by_pc);pointers=constant_pointer_offsets(text)
        for label,pc in mapping.items():
            instruction_start=bool(re.match(r'  %\d+ = load i32, ptr %NEXT_PC, align 4\n  store i32 %\d+, ptr %PC, align 4\n',blocks[label]))
            compiled_PC.add(pc);proof=audit_block(path.stem,label,pc,blocks[label],by_pc[pc],stores.get(pc)if instruction_start else None,pointers)
            attributions.append(dict(body=entry,IR=str(path.resolve()),label=label,pc=pc,source_store=pc in stores,instruction_start=instruction_start))
            if proof:callbacks.append(proof);counts[proof['kind']+'_callbacks']+=1
        counts['compiled_IR_bodies']+=1;counts['compiled_instruction_blocks']+=len(mapping)
    unique_store={r['pc']for r in callbacks};cold_PC={r['pc']for r in graphs[str(0x56fea0)]['instructions']};cold_stores={pc for pc in stores if pc in cold_PC}
    missing=set(stores)-unique_store
    need(missing==cold_stores and len(cold_stores)==8,'All actual compiled store PCs covered; only explicit cold recursive8 descriptors remain uncompiled '+str([hex(v)for v in sorted(missing)]))
    need(compiled_PC==set(by_pc)-cold_PC and len(compiled_PC)==1287,'Every physically frozen source instruction outside uncompiled recursive body has exact compiled IR block attribution')
    counts['unique_compiled_store_PCs']=len(unique_store);counts['cold_descriptor_only_store_PCs']=len(cold_stores);counts['store_callback_occurrences_checked']=len(callbacks)
    service_path=pin(ROOT/'tools/m4-constructor-native/borrowed_constructor_v2.inc');service=service_path.read_text();component_path=pin(ROOT/'tools/m4-constructor-native/component_v2.cpp');component=component_path.read_text()
    need(service.index('constructor_prior_read_={pc,address,bytes,value,constructor_access_epoch_,false}')<service.index('if(!a)return'),'All owned and nonowned literal prior reads retained before allocation early return')
    need(service.index('m4_constructor_store_source::guard(')<service.index('r.memory().write({address}'),'Independent current-State store guard precedes mirror memory commit')
    need('constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;'in service,'Successful source store clears prior and advances epoch')
    need('constructor_active_root_=entering?root:0;constructor_prior_read_={};constructor_prior_root_=0;++constructor_access_epoch_;'in service and 'whole source State/FX unchanged'in service,'Private scope clearing with entire source State/FX conservation')
    need('session.constructor_scope(s,root,true);active=true;'in component and 'session.constructor_scope(s,root,false);r.cpu()=cpu(s);'in component,'Actual positive root entry/return scope is balanced')
    if 'catch(...){t.owner->failed=true;t.exception=std::current_exception();}'in component:source_findings.append(dict(kind='Failure-scope cleanup residual',scope='Current Component catch marks failure but does not clear private Session constructor scope/prior; existing borrowed MFC poison route requires private clearing as well',source_path=str(component_path.resolve()),normal_positive_scope_balanced=True))
    if name=='dry':print(json.dumps(dict(counts=dict(counts),unique_compiled_PCs=len(compiled_PC),missing=[hex(v)for v in sorted(missing)],findings=source_findings)));return
    out=ROOT/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh complete compiled IR timing receipt');out.mkdir(parents=True)
    def write(filename,data):
        p=out/filename;p.write_text(json.dumps(data,indent=2)+'\n');pin(p);return p
    callback_path=write('store-callback-contracts.json',callbacks);attribution_path=write('physical-PC-blocks.json',attributions)
    scope_path=write('scope-contracts.json',dict(all_prepared_store_callback_forms_checked=True,actual_normal_reachability_claim=False,compiled_store_PC_count=len(unique_store),compiled_source_descriptor_count=418-len(cold_stores),cold_uncompiled_entry=0x56fea0,cold_descriptor_only_PCs=sorted(cold_stores),source_optimized_machine_order_claim=False,source_adapter_positive_scope_and_prior_invalidation=True,failure_scope_findings=source_findings,unsupported_compiled_store_forms=0))
    pin(__file__)
    for p,h in list(pins.items()):pin(p,h)
    report=dict(passed=True,scope='Independent exact physicalPC/IR CFG attribution, every prepared store callback address/value algebra and relevant State timing across33 literal bodies. Cold recursive stores remain descriptor-only; optimized linked artifact timing and actual normal path execution are separate.',complete_compiled_store_IR_timing_claim=True,compiled_body_count=33,store_callback_occurrences_checked=len(callbacks),unique_compiled_store_PC_count=len(unique_store),cold_uncompiled_entry=0x56fea0,cold_uncompiled_store_count=len(cold_stores),counts=dict(counts),current_preparation_sha256=sha(prep_path),entry_lifts_sha256='e6082e83ba2c48342ca13c26e79e2b63a6533726d222e64b96cb17cece5e7103',operand_receipt_sha256=sha(operands_path),callback_contracts=str(callback_path.resolve()),callback_contracts_sha256=sha(callback_path),physical_PC_attribution=str(attribution_path.resolve()),physical_PC_attribution_sha256=sha(attribution_path),scope_contracts=str(scope_path.resolve()),scope_contracts_sha256=sha(scope_path),failure_scope_findings=source_findings,source_State_observer_mutation=False,machine_code_order_reviewed=False,optimized_machine_order_claim=False,native_executed=False,compiler_executed=False,capture_reader_opened=False,payload_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,files=pins)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(p),callback_contracts_sha256=sha(callback_path),counts=dict(counts),findings=source_findings)))

if __name__=='__main__':main(sys.argv[1])
