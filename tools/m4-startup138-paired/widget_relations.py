"""Finite widget pair joins. Values without source provenance stay unresolved.

This never authorizes endpoint masks or consumes candidate AFTER as input.
Own branch source gates must be independently admitted before use by pairing.
"""
from collections import Counter
WIDGETS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
CALLBACKS=(0x40e420,0x40ef90,None,0x4795d0,0x5a3c60,0x5a4020,0x5a6720)
# 40F000 is a registrar; exact callback is derived by the independently frozen literal table.
def need(v,m):
 if not v:raise ValueError(m)
def compare_root(original,native):
 root=original['root'];need(root==native['root']and root in WIDGETS,'Exact same literal widget root')
 need(not original['source_callback_execution']and native['whole_State_source_derived']and not native['AFTER_machine_or_page_seed'],'Own complete source gate semantics')
 need(original['source_PCs']==native['source_PCs'],'Every ordered literal source PC matches')
 oa=original['source_accesses'];na=native['source_accesses'];need(len(oa)==len(na),'All ordered source operands retained')
 need([(r[0],r[1],r[3],r[4])for r in oa]==[(r[0],r[1],r[3],r[4])for r in na],'Every ordered source operand PC/address/width/direction')
 fs=[]
 for row in original['FS_joins']:
  i=row['source_access_index'];a=oa[i];b=na[i];need(a[0]==b[0]==row['PC']and a[4]==b[4]==int(row['writing']),'Exact actual source FS occurrence/index/direction')
  fs.append(dict(PC=row['PC'],source_access_index=i,writing=row['writing'],original_source_value=a[2],native_source_value=b[2],typed_own_FS_head_semantics=True,raw_values_equal=a[2]==b[2]))
 api=[];aliases={};counts=Counter();native_api=native['GDI_source']['API_response_derivations'];need(len(original['API_inputs'])==len(native_api),'Complete same GDI chronology')
 for ordinal,(a,b)in enumerate(zip(original['API_inputs'],native_api)):
  need(a['API']==b['service']and a['source_CALL_pc']==b['CALL_pc']and a['source_frame']==b['source_frame']and b['ordinal']==ordinal,'Exact source GDI API/CALL/frame/ordinal')
  service=a['API'];args=a['arguments'];nargs=b['source_arguments'];result=a['finite_volatile_EAX_ECX_EDX_EFLAGS'][0];guest=b['guest_result_derived'];key=(b['instance'],ordinal)
  if service=='DeleteObject':
   need(len(args)==len(nargs)==1 and (args[0],nargs[0])in aliases,'Same previously actual sourced GDI handle pair at DeleteObject')
   need(bool(result)==bool(guest),'Whole original/native DeleteObject BOOL success correspondence')
  else:
   need(args==nargs,'Every normal source GDI argument DWORD exact')
   need(service in('GetStockObject','CreateFontA'),'Finite three service inventory')
   need(result and guest,'Positive actual original/native GDI source handles')
   aliases[(result,guest)]=dict(service=service,instance=b['instance'],ordinal=ordinal,generation=b['generation'])
  need(a['object_or_stack_bytes_seeded']is False and b['full_guest_FX_unchanged'],'Own exact typed provider facts; no object/stack/FX response seed')
  api.append(dict(ordinal=ordinal,source_CALL_pc=a['source_CALL_pc'],source_frame=a['source_frame'],service=service,instance=b['instance'],original_arguments=args,native_arguments=nargs,original_result=result,native_guest_result=guest,native_actual_RAX=b['native_RAX'],native_generation=b['generation'],full_native_API_record_sha256=b['API_record_sha256'],volatile_and_FX_ENV_values_retained_own_branch=True))
  counts['typed_GDI_CALL_argument_result_relations']+=1
 borrowed=native['borrowed_provider'];need(borrowed['returned']and borrowed['callback']==original['registration_callback'],'Exact callback argument and accepted own provider return')
 expected=[9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,borrowed['source_CALL_frame'],0x5ac124];need(borrowed['borrowed_projection']==expected,'Entire eight DWORD source projection')
 shared=[[0x5ac11e,0x5bb52c,0x1decb0,4,0],[0x5ac11e,borrowed['source_CALL_frame'],0x5ac124,4,1]];need(borrowed['shared_source_rows']==shared,'Exact shared source IAT/CALL operands')
 for row in shared:need(row in oa and row in na,'Both independent branches execute exact shared IAT/CALL operand')
 need(any(r[1]==borrowed['source_CALL_frame']+4 and r[2]==borrowed['callback']and r[3:]==[4,1]for r in oa),'Original own literal callback push')
 realloc=[]
 for row in original['source_registry_reallocation_inputs']:
  need(row['source_CALL_pc']==0x78011c27 and row['source_return_word']==0x78011c2d and row['requested']>=144 and row['complete_old_prefix_source_derived']and not row['AFTER_endpoint_seed'],'Literal onexit growth full APIinitial source facts')
  realloc.append(row)
 counts.update(ordered_source_PC_relations=len(original['source_PCs']),ordered_source_operand_identity_relations=len(oa),actual_original_FS_source_joins=len(fs),exact_registrar_shared_operands=2,source_original_realloc_births=len(realloc))
 # Deliberately not a declaration set. Source-dependent scalar operand differences
 # require literal transfer/last-writer proof before whole-page pair acceptance.
 unresolved=[dict(index=i,PC=a[0],address=a[1],width=a[3],writing=bool(a[4]),original=a[2],native=b[2])for i,(a,b)in enumerate(zip(oa,na))if a[2]!=b[2]]
 return dict(root=root,sequence=original['sequence'],level=native['level'],counts=dict(counts),GDI_relations=api,FS_relations=fs,registration=dict(callback=borrowed['callback'],projection=expected,shared_source_operands=shared),original_realloc_source_births=realloc,unresolved_value_relations=unresolved,whole_endpoint_difference_authorization=False,source_after_input_seed=False)
