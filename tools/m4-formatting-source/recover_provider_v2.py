"""Physical formatter trace descriptors; no execution or initializer credit.

The inherited linear ledger is a locator. Each selected row is authenticated
against the staged PE. Focused decoding starts at two true branch/function
boundaries that the old linear ledger crossed from padding or table data.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, subprocess, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
REC = R/'reports/m4-formatting-frontier/recovery-r1'
REC_SHA = '8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15'
HELPERS = (0x7801041a, 0x7801044f, 0x78010480, 0x780104b8)

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def need(value, reason):
    if not value: raise ValueError(reason)

def main(name):
    out=R/'reports/m4-formatting-source'/name
    need(re.fullmatch('provider-recovery-r[1-9][0-9]*', name) and not out.exists(), 'Fresh additive provider descriptors')
    out.mkdir(parents=True); files={}; commands=[]
    def pin(p, expected=None):
        p=Path(p).resolve(); need(p.suffix.lower()!='.mwb', 'No capture reader')
        digest=sha(p); need(expected is None or digest==expected, 'Physical identity '+str(p))
        need(str(p) not in files or files[str(p)]==digest, 'Stable source input')
        files[str(p)]=digest; return p
    def load(p, tag):
        spec=importlib.util.spec_from_file_location(tag, pin(p)); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
    def read(p, expected=None): return json.loads(pin(p, expected).read_bytes())
    def emit(name, obj):
        p=out/name; p.write_text(json.dumps(obj, indent=2)+'\n'); pin(p); return p
    A=load(R/'tools/m4-service-initializers/recover.py', 'format_source_PE')
    D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py', 'format_source_contracts')
    receipt=read(REC/'report.json', REC_SHA); need(receipt['passed'], 'Frozen physical formatting frontier')
    crt=A.Module(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', A.IDENTITIES['local/mw3-staged/Shared_DLLs/MSVCRT.DLL']))
    lookup=pin(R/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.linear-lookup.txt')
    def parse(text):
        rows={}
        for line in text.splitlines():
            match=A.ROW.match(line)
            if not match: continue
            pc=int(match[1],16); code=bytes.fromhex(match[2]); asm=re.sub(r'\s+', ' ', match[3].strip()); op,_,args=asm.partition(' ')
            need(pc not in rows, 'Unique focused decode boundary')
            rows[pc]=dict(pc=pc,size=len(code),bytes=code.hex(),mnemonic=op,operands=args)
        return rows
    crt.rows.update(parse(lookup.read_text()))
    decoder=pin(A.DECODER, A.IDENTITIES[str(A.DECODER.relative_to(R)).replace('\\','/')])
    # Old linear decode starts FDD5's padding and 10419's table tail; these
    # exact source branch/function entries must be independently decoded.
    for label, start, end in (('dispatch-six',0x7800fdd6,0x7800fe25), ('put-character',0x7801041a,0x7801044f)):
        argv=[str(decoder),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(crt.path)]
        cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000)
        need(cp.returncode==0, 'Focused source decode '+label)
        for suffix,data in (('.stdout',cp.stdout),('.stderr',cp.stderr)):
            p=out/(label+suffix);p.write_bytes(data);pin(p)
        rows=parse(cp.stdout.decode());need(start in rows and b''.join(bytes.fromhex(rows[pc]['bytes']) for pc in sorted(rows))==crt.image.read(crt.image.rva_range(start-crt.base,end-start)[0],end-start), 'Complete exact focused extent '+label)
        crt.rows.update(rows);commands.append(dict(argv=argv,exit_code=cp.returncode))
    old=read(REC/'output-frontier-graphs.json'); entries=tuple(int(k) for k in old)
    graphs={entry:A.walk(crt,entry) for entry in (*entries,*HELPERS)}
    rows={row['pc']:row for graph in graphs.values() for row in graph['instructions']}
    for graph in read(REC/'provider-entry-graphs.json').values():
        for row in graph['instructions']: rows[row['pc']]=row
    contracts=[]
    for pc,row in sorted(rows.items()):
        raw=bytes.fromhex(row['bytes']); need(crt.image.read(crt.image.rva_range(pc-crt.base,len(raw))[0],len(raw))==raw, 'Exact physical provider row '+hex(pc))
        op=row['mnemonic'];args=row['operands'].split(' <')[0];repeat=None
        if op in ('rep','repe','repz','repne','repnz'): repeat=op;op,args=args.split(None,1)
        normal=dict(pc=pc,width=row['size'],bytes_hex=row['bytes'],mnemonic=op,operands=args)
        if repeat:normal['repeat']=repeat
        contract=D.instruction_contract(normal)
        if op=='scasb':
            # SCASB only reads ES:EDI. The inherited generic operand annotator
            # cannot represent this implicit REP stream or retained AL.
            contract['explicit_memory_reads']=[];contract['explicit_memory_writes']=[]
            contract['implicit_memory']=[dict(kind='string-read',bits=8,address='ESBASE+EDI',operation='AL minus byte; six arithmetic flags',direction='actual DF',repeat=repeat,count='ECX decremented per compared byte',termination='ECX=0 or ZF=1 for REPNE')]
            contract['flags']='six arithmetic comparison flags per actual compared byte; no comparison when ECX=0'
        if op in ('std','cld'):contract['flags']='DF='+('1' if op=='std' else '0')+'; all other flags retained'
        contracts.append(contract)
    dependencies=[]
    for entry, graph in graphs.items():
        for call in graph['direct_calls']:
            dependencies.append(dict(entry=entry,**call,descriptor_present=call['target'] in rows,normal_reached_observed=False))
    tables=[]
    for address,size,role in ((0x780103fa,32,'eight-way control table'),(0x7802e2d0,128,'ASCII class nibble table'),(0x7802e2f0,128,'state transition nibble table')):
        raw=crt.image.read(crt.image.rva_range(address-crt.base,size)[0],size)
        tables.append(dict(address=address,bytes=size,bytes_hex=raw.hex(),role=role,loaded_BEFORE_required=True))
    target=emit('instruction-contracts.json',dict(schema='mw34-formatting-provider-trace-descriptors-v1',instructions=contracts,entry_graphs=list(graphs),implicit_string_contracts=[c for c in contracts if c['mnemonic']=='scasb'],normal_reached_observed=False,source_post_state_seed=False))
    emit('provider-graphs.json',graphs);emit('direct-dependencies.json',dependencies);emit('tables.json',tables)
    emit('helper-contracts.json',dict(vararg_DWORD=dict(entry=0x780104b8,argument='pointer to source varargs cursor',effect='cursor+=4; return DWORD at cursor-4',ret_cleanup=0),write_string=dict(entry=0x78010480,args=['source bytes','signed count','source FILE32','source count pointer'],nested_character_CALL=0x780104a0),write_character=dict(entry=0x7801041a,args=['source signed character','source FILE32','source count pointer'],source_count_dec_PC=0x78010420,source_byte_write_PC=0x7801042a,source_pointer_inc_PC=0x7801042c,count_inc_PC=0x7801044b,cold_flush_CALL=0x78010442),normal_domain='Exact default narrow %s%s only after actual trace and source branch derivation',observed=False))
    pin(__file__);pin(sys.executable);pin(R/'tools/analysis/pe.py');pin(R/'tools/m4-pipeline/manifests.py');pin(R/'tools/m4-pipeline/paths.py')
    report=dict(passed=True,scope='Physical provider trace descriptors and narrow helper graphs, static only',instructions=str(target),instructions_sha256=sha(target),instruction_count=len(contracts),source_bytes=sum(c['width'] for c in contracts),helper_entries=list(HELPERS),helper_local_decode_closed={str(e):graphs[e]['local_decode_closed'] for e in HELPERS},recovered_dispatch_six=graphs[0x7800fdd6]['instruction_count'],commands=commands,files=files,generic_formatter_closed=False,normal_source_executed=False,native_executed=False,initializer_credit=0,capture_reader_opened=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),instructions=len(contracts),helper_rows={hex(e):graphs[e]['instruction_count'] for e in HELPERS})))

if __name__=='__main__':main(sys.argv[1])
