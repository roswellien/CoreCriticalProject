"""Finite widget pair joins. Values without source provenance stay unresolved.

This never authorizes endpoint masks or consumes candidate AFTER as input.
Own branch source gates must be independently admitted before use by pairing.
"""
from collections import Counter
WIDGETS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
CALLBACKS=(0x40e420,0x40ef90,0x40f030,0x4795d0,0x5a3c60,0x5a4020,0x5a6720)
# Entire seven callback table must agree with the frozen physical widget literals.
def need(v,m):
 if not v:raise ValueError(m)
def compare_root(original,native):
 root=original['root'];need(root==native['root']and root in WIDGETS,'Exact same literal widget root')
 need(original['registration_callback']==dict(zip(WIDGETS,CALLBACKS))[root],'Exact frozen literal widget callback')
 need(not original['source_callback_execution']and native['whole_State_source_derived']and not native['AFTER_machine_or_page_seed'],'Own complete source gate semantics')
 need(original['source_PCs']==native['source_PCs'],'Every ordered literal source PC matches')
 oa=original['source_accesses'];na=native['source_accesses'];need(len(oa)==len(na),'All ordered source operands retained')
 registry_stores=[]
 for i,(a,b)in enumerate(zip(oa,na)):
  need((a[0],a[3],a[4])==(b[0],b[3],b[4]),'Every ordered source operand PC/width/direction')
  if a[1]!=b[1]:
   need(a[0]==0x78004a67 and a[3:]==[4,1]and a[2]==b[2]==original['registration_callback'],'Only literal registry callback backing store address may be an alias')
   own=[]
   for source,row in((oa,a),(na,b)):
    before=source[:i];nexts=[v for v in before if v[1]==0x78037888 and v[3]==4];begins=[v for v in before if v[1]==0x7803788c and v[3]==4]
    need(not nexts or nexts[-1][4]==0 or nexts[-1][0]==0x7801e2b5,'Only literal growth end publication may supply source next')
    need(not begins or begins[-1][4]==0 or begins[-1][0]==0x7801e2aa,'Only literal growth begin publication may supply source begin')
    need(nexts and begins and nexts[-1][2]==row[1]and row[1]>=begins[-1][2]and (row[1]-begins[-1][2])%4==0,'Own literal last registry next/begin reads derive callback write address')
    own.append(dict(begin=begins[-1][2],next=nexts[-1][2],callback_index=(row[1]-begins[-1][2])//4))
   need(own[0]['callback_index']==own[1]['callback_index'],'Same chronological callback registry offset')
   registry_stores.append(dict(PC=a[0],callback=a[2],original=own[0],native=own[1],source_access_index=i))
  else:need(a[1]==b[1],'Every other source operand address exact')
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
 handle_stores=[];store_cursor=-1
 for relation in api:
  if relation['service']not in('GetStockObject','CreateFontA'):continue
  pc=0x5a0142 if relation['service']=='GetStockObject'else 0x5a0753
  address=relation['instance']+0x258;matches=[i for i,(a,b)in enumerate(zip(oa,na))if i>store_cursor and a[0]==b[0]==pc and a[1]==b[1]==address and a[3:]==b[3:]==[4,1]and a[2]==relation['original_result']and b[2]==relation['native_guest_result']]
  need(matches,'Exact source ESI+258 GDI result storing MOV in both own branches');index=matches[0];store_cursor=index
  handle_stores.append(dict(source_access_index=index,PC=pc,address=address,width=4,service=relation['service'],instance=relation['instance'],original=relation['original_result'],native=relation['native_guest_result'],native_generation=relation['native_generation'],API_ordinal=relation['ordinal'],activation_root=root))
 need(len(handle_stores)==sum(v['service']in('GetStockObject','CreateFontA')for v in api),'All typed stock/font result stores matched')
 counts['literal_GDI_ESI258_lastwriter_activations']=len(handle_stores)
 borrowed=native['borrowed_provider'];need(borrowed['returned']and borrowed['callback']==original['registration_callback'],'Exact callback argument and accepted own provider return')
 expected=[9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,borrowed['source_CALL_frame'],0x5ac124];need(borrowed['borrowed_projection']==expected,'Entire eight DWORD source projection')
 shared=[[0x5ac11e,0x5bb52c,0x1decb0,4,0],[0x5ac11e,borrowed['source_CALL_frame'],0x5ac124,4,1]];need(borrowed['shared_source_rows']==shared,'Exact shared source IAT/CALL operands')
 need(shared[0]in na and [0x5ac11e,0x5bb52c,0x78004a36,4,0]in oa,'Exact original loaded/native raw onexit IAT and source CALL PC')
 need(shared[1]in oa and shared[1]in na,'Both independent branches execute same literal source CALL return word/frame')
 need(any(r[1]==borrowed['source_CALL_frame']+4 and r[2]==borrowed['callback']and r[3:]==[4,1]for r in oa),'Original own literal callback push')
 realloc=[]
 for row in original['source_registry_reallocation_inputs']:
  need(row['source_CALL_pc']==0x78011c27 and row['source_return_word']==0x78011c2d and row['requested']>=144 and row['complete_old_prefix_source_derived']and not row['AFTER_endpoint_seed'],'Literal onexit growth full APIinitial source facts')
  realloc.append(row)
 counts.update(ordered_source_PC_relations=len(original['source_PCs']),ordered_source_operand_identity_relations=len(oa),actual_original_FS_source_joins=len(fs),exact_registrar_shared_operands=2,source_original_realloc_births=len(realloc))
 # Deliberately not a declaration set. Source-dependent scalar operand differences
 # require literal transfer/last-writer proof before whole-page pair acceptance.
 unresolved=[dict(index=i,PC=a[0],address=a[1],width=a[3],writing=bool(a[4]),original=a[2],native=b[2])for i,(a,b)in enumerate(zip(oa,na))if a[2]!=b[2]]
 return dict(root=root,sequence=original['sequence'],level=native['level'],counts=dict(counts),GDI_relations=api,FS_relations=fs,typed_handle_source_stores=handle_stores,registry_source_stores=registry_stores,registration=dict(callback=borrowed['callback'],projection=expected,shared_source_operands=shared),original_realloc_source_births=realloc,unresolved_value_relations=unresolved,whole_endpoint_difference_authorization=False,source_after_input_seed=False)


class HandleFieldPolicy:
 """Only literal source GDI storing MOV activates exact own-valued four-byte fields."""
 def __init__(self):self.fields={};self.activations=[]
 def activate(self,root_relation,phase):
  for store in root_relation['typed_handle_source_stores']:
   need(store['PC']in(0x5a0142,0x5a0753)and store['address']==store['instance']+0x258 and store['width']==4,'Finite exact literal handle field activation')
   row=dict(store,phase=phase);self.fields[row['address']]=row;self.activations.append(row)
 def page(self,phase,side,page,original,native):
  declared=set()
  for address,row in self.fields.items():
   if address&~4095!=page or phase<row['phase']or(phase==row['phase']and side=='before'):continue
   offset=address&4095;need(original[offset:offset+4]==row['original'].to_bytes(4,'little')and native[offset:offset+4]==row['native'].to_bytes(4,'little'),'Each whole paired endpoint retains exact latest own source handle value')
   declared.update(range(offset,offset+4))
  return declared


def compare_font_cleanup(original_generations,root_relations,native_cleanup):
 need(len(root_relations)==7 and len({r['root']for r in root_relations})==7,'Whole seven widget source result scope')
 sequence=root_relations[0]['sequence'];level=root_relations[0]['level'];need(all(r['sequence']==sequence and r['level']==level for r in root_relations),'One carried same original/native sequence')
 originals=[r for r in original_generations if r['sequence']==sequence];stores=[v for r in root_relations for v in r['typed_handle_source_stores']if v['service']=='CreateFontA'];need(len(originals)==len(stores)==15,'All fifteen actual original/native source owned fonts')
 need(native_cleanup['level']==level and native_cleanup['sequence']==sequence and native_cleanup['actual_owned_font_frees']==15 and not native_cleanup['source_callbacks_executed']and not native_cleanup['manual_cleanup_source_body_modeled']and not native_cleanup['AFTER_State_or_memory_seed'],'Same strictly manual native fifteen-font cleanup; no source callback execution claim')
 need(native_cleanup['physical_GDI']['passed']and native_cleanup['whole_caller_FX512_ENV28_restore'],'Whole independently physical API and own caller cleanup hardware proof')
 manual=[r for r in native_cleanup['physical_GDI']['calls']if r['call_words'][2]==1];need(len(manual)==15,'All actual current physical native manual API calls')
 joined=[]
 for original in originals:
  matching=[r for r in stores if r['instance']==original['instance']and r['activation_root']==original['root']];need(len(matching)==1,'Same instance unique literal font birth/store')
  store=matching[0];ow=original['source_owning_store'];need(ow['PC']==store['PC']==0x5a0753 and ow['address']==store['address']==original['instance']+0x258 and ow['value']==store['original']==original['handle'],'Exact original source owning store joins independent native store by literal instance/field')
  actual=[r for r in manual if r['call_words'][4]==original['root']and r['call_words'][7]==original['instance']];need(len(actual)==1 and actual[0]['requested']=='DeleteObject'and actual[0]['call_words'][10]==original['manual_cleanup_BOOL']==1,'Same-instance own-generation actual original/native cleanup BOOL1')
  need(original['live']and original['deleted_event']is None and len(bytes.fromhex(original['FX_BEFORE_hex']))==len(bytes.fromhex(original['FX_AFTER_hex']))==512 and len(bytes.fromhex(original['ENV_BEFORE_hex']))==len(bytes.fromhex(original['ENV_AFTER_hex']))==28,'Own original complete measured lifetime/FX/ENV facts')
  joined.append(dict(instance=original['instance'],root=original['root'],field=store['address'],store_PC=store['PC'],original_handle=original['handle'],native_guest_handle=store['native'],native_generation=store['native_generation'],source_store_index_original=ow['source_access_index'],source_store_index_native=store['source_access_index'],manual_API_row_sha256=actual[0]['manual_row_sha256'],BOOL=1,source_callback_executed=False))
 need({r['native_generation']for r in joined}==set(native_cleanup['font_generations'])and len(native_cleanup['font_generations'])==15,'All and only actual fifteen owned native generations freed; stock generation excluded')
 return joined
