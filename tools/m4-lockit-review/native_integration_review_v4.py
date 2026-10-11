"""Independent exact owner/publication array attribution for current preparation5."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
p=HERE/'native_integration_review_v3.py';s=p.read_text(encoding='utf-8')
needle="exec(compile(s,str(p),'exec'),globals())"
assert s.count(needle)==1
s=s.replace(needle,"compiled_source=s")
context={"__file__":__file__,"__name__":"review_deriver"};exec(compile(s,str(p),'exec'),context);source=context['compiled_source']
source=source.replace("reports/m4-lockit-native/preparation-r4","reports/m4-lockit-native/preparation-r5").replace("reports/m4-joint-startup124/preparation-r4","reports/m4-joint-startup124/preparation-r5")
anchor="    counts['physical_early_FS_variant_contracts']=2"
extra='''    owned_receipt=read(ROOT/'reports/m4-lockit-source/owned-interface-r1/report.json');need(owned_receipt['passed'],'Source-owned interface derivation')
    owned=read(ROOT/'reports/m4-lockit-source/owned-interface-r1/contracts.json');new_contract=text(np/'fs_contract.inc');old_contract=text(ROOT/'reports/m4-lockit-native/preparation-r4/fs_contract.inc')
    def parse_named_array(body,kind,name):
        block=re.search('constexpr '+kind+' '+name+r'\\[\\]\\{(.*?)\\};',body,re.S)[1]
        return [tuple(map(int,re.findall(r'\\d+',r))) for r in re.findall(r'\\{([^{}]+)\\}',block)]
    additions={}
    for kind,name in (('FsOwnedAccess','fs_owned_accesses'),('FsInput','fs_inputs')):
        before=parse_named_array(old_contract,kind,name);after=parse_named_array(new_contract,kind,name);expected=[tuple(x) for x in owned[name]]
        need(after==before+expected,'Only exact additive source-derived owner/publication arrays '+name);additions[name]=expected
    need(len(additions['fs_owned_accesses'])==32 and len(additions['fs_inputs'])==8,'Exact32 new owner stores/eight publications')
    normal_graphs=read(ROOT/'reports/m4-lockit-frontier/recovery-r1/game-normal-graphs.json');literal_rows={row['pc']:row for graph in normal_graphs.values() for row in graph['instructions']}
    for root,pc,writing,width,owner_root,owner_call,offset in additions['fs_owned_accesses']:
        shape=next(x for x in physical if x['root']==root);allocation=next(x for x in shape['allocations'] if x['CALL_pc']==owner_call);r=literal_rows[pc]
        need(owner_root==root and width==4 and writing==1 and 0<=offset<=allocation['requested_size']-4,'Exact requested-bound owner context')
        left=r['operands'].split(',')[0];match=re.fullmatch(r'dword ptr \\[([a-z]+)(?: \\+ 0x([0-9a-f]+))?\\]',left)
        need(match and int(match[2] or '0',16)==offset and r['mnemonic']=='mov','Literal raw destination offset and DWORD store')
        prior=[a['CALL_pc'] for a in shape['allocations'] if a['CALL_pc']<pc];need(prior and max(prior)==owner_call,'Distinct straight-line current allocation CALL context')
        off,_=game.rva_range(pc-game.image_base,r['size']);need(game.read(off,r['size'])==bytes.fromhex(r['bytes']),'Physical source-owned store')
    for root,call,request,obj,publication,pc,parent_root,parent_call,offset in additions['fs_inputs']:
        row=literal_rows[pc];need(parent_root==parent_call==offset==0 and row['mnemonic']=='mov' and row['operands']==f'dword ptr [0x{publication:x}], eax','Exact literal static owner publication')
        need(any(x[:4]==(root,call,request,obj) and x[4]==0 for x in mfc),'Generic MFC publication disabled only for same exact new objects')
        off,_=game.rva_range(pc-game.image_base,row['size']);need(game.read(off,row['size'])==bytes.fromhex(row['bytes']),'Physical source-owned publication')
    for name in ('fs_operations.inc','mfc_operations.inc','lockit_operations.inc','locale_batch_operations.inc','locale_batch_binding.inc','session_impl.inc'):
        need(pin(np/name).read_bytes()==pin(ROOT/'reports/m4-lockit-native/preparation-r4'/name).read_bytes(),'Owner fix retains every runtime/source check '+name)
    counts['exact_physical_new_owner_stores']=32;counts['exact_physical_new_owner_publications']=8
    emit('owner-admission.json',{'contracts':additions,'whole_requested_bound_20_or_24':True,'actual32B_backing_pending_independent_capture':True,'cross_root_heap_access_added':False,'generic_MFC_publication_zero_only_new8':True})
'''
assert source.count(anchor)==1;source=source.replace(anchor,anchor+'\n'+extra)
exec(compile(source,str(HERE/'native_integration_review.py'),'exec'),globals())
