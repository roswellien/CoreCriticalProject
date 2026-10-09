"""Asset-free admission contract; this module never executes guest code."""
from __future__ import annotations
import hashlib

IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
CODE_SHA = 'fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa'
ENTRY, SIZE, RETURN, STACK, GLOBAL = 0x558290, 43, 0x10000100, 0x20001000, 0x72c000
GLOBAL_START, GLOBAL_SIZE = 0x72c1e4, 20
STATE_BYTES, FLAGS = 3504, 0xcd5
CWS = tuple(0x7f | pc << 8 | rc << 10 for pc in (0,2,3) for rc in range(4))
DEPENDENCIES = ('mov32_reg_stack', 'mov32_global_reg', 'cdq32', 'sub32', 'sar32_1', 'ret32_8')
# No exact translated version of this real function has passed an original/native gate.
EXECUTION_BLOCKERS = ('missing_exact_translation_and_original_native_comparison',
                      'sar32_1_final_AF_undefined_policy_unvalidated')


class AdmissionError(ValueError):
    pass


def require(ok, code):
    if not ok: raise AdmissionError(code)


def u32(value):
    return type(value) is int and 0 <= value < 2**32


def blob(text, length, code):
    require(type(text) is str and len(text) == length*2, code)
    try: result=bytes.fromhex(text)
    except ValueError: raise AdmissionError(code) from None
    require(len(result)==length,code)
    return result


def full_tags(top, ftw, slots):
    result=0
    for i,value in enumerate(slots):
        p=(top+i)&7
        if not ftw&(1<<p): tag=3
        else:
            sig=int.from_bytes(value[:8],'little');exp=int.from_bytes(value[8:],'little')&0x7fff
            canonical=(sig==0 if exp==0 else bool(sig>>63) and
                       (exp!=0x7fff or sig==1<<63 or bool(sig&(1<<62))))
            require(canonical,'unsupported_occupied_raw80')
            tag=1 if exp==0 and sig==0 else 2 if exp==0x7fff else 0
        result|=tag<<(2*p)
    return result


def reviewed_evidence():
    """Expected metadata for asset-free controls; not evidence of a file check."""
    return {'image_sha256':IMAGE_SHA,'entry_va':ENTRY,'size_bytes':SIZE,'code_sha256':CODE_SHA,
            'global_va':GLOBAL_START,'global_size':GLOBAL_SIZE,
            'global_initial_sha256':hashlib.sha256(bytes(GLOBAL_SIZE)).hexdigest(),
            'global_section':'.data','global_zero_fill':True,'global_permissions':'rw',
            'direct_targets':[],'indirect_targets':[],'dependencies':list(DEPENDENCIES),
            'static_incoming_edge':{'caller_entry':0x5995b0,'call_pc':0x5995dd,'target':ENTRY,'return_pc':0x5995e2}}


def validate_evidence(evidence):
    want=reviewed_evidence()
    require(type(evidence) is dict and set(evidence)==set(want),'unknown_or_missing_dependency_metadata')
    require(evidence.get('image_sha256')==IMAGE_SHA,'wrong_image_identity')
    for field in ('entry_va','size_bytes','code_sha256'):
        require(evidence.get(field)==want[field],'wrong_complete_function_identity')
    for field in ('global_va','global_size','global_initial_sha256','global_section','global_zero_fill','global_permissions'):
        require(evidence.get(field)==want[field],'wrong_global_mapping_or_initial_value')
    require(evidence.get('direct_targets')==[] and evidence.get('indirect_targets')==[], 'unknown_callee_target')
    require(evidence.get('dependencies')==list(DEPENDENCIES),'unsupported_instruction_dependency')
    require(evidence.get('static_incoming_edge')==want['static_incoming_edge'],'wrong_observed_call_return_edge')
    return want


def fixture_context():
    """Authored metadata-only valid context for tests; no game bytes or execution."""
    stack=bytearray(4096);esp=STACK+256
    stack[256:268]=RETURN.to_bytes(4,'little')+(17).to_bytes(4,'little')+(0xfffffff9).to_bytes(4,'little')
    slots=[(0x8000000000000001+i).to_bytes(8,'little')+(0x3fff).to_bytes(2,'little') for i in range(8)]
    return {'image_sha256':IMAGE_SHA,'entry_va':ENTRY,'state_bytes':STATE_BYTES,'address_bits':32,
            'registers':[0x11111111,0x22222222,0x33333333,0x44444444,esp,0x66666666,0x77777777,0x88888888],
            'flags':0x202,'eip':ENTRY,'cw':0x37f,'sw':0,'top':0,'physical_ftw':3,
            'physical_full_tags':full_tags(0,3,slots),'logical_raw80':[s.hex() for s in slots],
            'vector_bytes':bytes(2048).hex(),'mmx_bytes':bytes(128).hex(),
            'stack_base':STACK,'stack_permissions':'rw','stack_bytes':stack.hex(),
            'global_base':GLOBAL,'global_permissions':'rw','global_bytes':bytes(4096).hex(),
            'object_mappings':[],'import_mappings':[],'direct_targets':[],'indirect_targets':[],
            'return_pc':RETURN,'return_route':'authored_return_capture','return_cleanup_bytes':12,
            'route_image_sha256':IMAGE_SHA,'route_entry_va':ENTRY,'route_code_sha256':CODE_SHA,
            'route_frozen':True,'route_selection':'generated','original_route_selection':'generated_original',
            'thread_id':1,'context_id':'isolated-authored-context-1','thread_policy':'single_owner_no_concurrency',
            'host_abi':'win64_state_guest32_memory','host_fp_policy':'save_restore_all_exits',
            'callbacks':False,'seh':False,'tls_fs':False,'reentrancy':False,'concurrency':False,
            'host_pointer_in_guest':False,'translation_evidence':None}


def admit_context(context, evidence, *, execute=False):
    """Validate a proposed isolated guest context. Execution is currently denied."""
    validate_evidence(evidence);q=context
    require(type(q) is dict and set(q)==CONTEXT_KEYS,'unknown_or_missing_context_field')
    require(q.get('image_sha256')==IMAGE_SHA,'wrong_image_identity')
    require(q.get('entry_va')==ENTRY and q.get('eip')==ENTRY,'wrong_entry_target')
    require(q.get('state_bytes')==STATE_BYTES and q.get('address_bits')==32,'wrong_guest_state_layout')
    regs=q.get('registers');require(type(regs) is list and len(regs)==8 and all(u32(r) for r in regs),'invalid_GPR_or_guest_pointer_width')
    flags=q.get('flags');require(u32(flags) and flags&0x202==0x202 and flags&~(0x202|FLAGS)==0,'invalid_entry_flags')
    require(q.get('cw') in CWS,'unsupported_or_unmasked_CW')
    sw,top,ftw=q.get('sw'),q.get('top'),q.get('physical_ftw')
    require(u32(sw) and sw&~0x7f7f==0 and sw&0x80==0 and type(top) is int and 0<=top<8 and top==(sw>>11&7)
            and type(ftw) is int and 0<=ftw<256,'invalid_SW_TOP_or_physical_FTW')
    raw_slots=q.get('logical_raw80');require(type(raw_slots) is list and len(raw_slots)==8,'invalid_raw80_slots')
    slots=[blob(x,10,'invalid_raw80_slots') for x in raw_slots]
    require(type(q.get('physical_full_tags')) is int and 0<=q['physical_full_tags']<=0xffff and
            q['physical_full_tags']==full_tags(top,ftw,slots),'inconsistent_physical_full_tags')
    blob(q.get('vector_bytes'),2048,'invalid_vector_state');blob(q.get('mmx_bytes'),128,'invalid_MMX_state')
    require(q.get('stack_base')==STACK and q.get('stack_permissions')=='rw','wrong_stack_mapping')
    stack=blob(q.get('stack_bytes'),4096,'invalid_stack_snapshot');esp=regs[4]
    require(STACK<=esp and esp+12<=STACK+4096,'return_argument_frame_out_of_bounds')
    require(q.get('return_pc')==RETURN and int.from_bytes(stack[esp-STACK:esp-STACK+4],'little')==RETURN
            and q.get('return_route')=='authored_return_capture' and q.get('return_cleanup_bytes')==12,'wrong_return_PC_or_cleanup')
    require(q.get('global_base')==GLOBAL and q.get('global_permissions')=='rw','wrong_global_mapping_or_permissions')
    global_bytes=blob(q.get('global_bytes'),4096,'invalid_global_snapshot')
    require(global_bytes==bytes(4096),'wrong_global_initial_value')
    require(q.get('object_mappings')==[] and q.get('import_mappings')==[],'unsupported_object_or_import_dependency')
    require(q.get('direct_targets')==[] and q.get('indirect_targets')==[],'unknown_callee_target')
    require(q.get('route_image_sha256')==IMAGE_SHA and q.get('route_entry_va')==ENTRY and q.get('route_code_sha256')==CODE_SHA,'wrong_route_identity')
    require(q.get('route_frozen') is True and q.get('route_selection')=='generated' and q.get('original_route_selection')=='generated_original','unfrozen_or_unreviewed_route_selection')
    require(u32(q.get('thread_id')) and type(q.get('context_id')) is str and len(q['context_id'])>0 and
            q.get('thread_policy')=='single_owner_no_concurrency','invalid_thread_context_owner')
    require(q.get('host_abi')=='win64_state_guest32_memory' and q.get('host_fp_policy')=='save_restore_all_exits','wrong_host_ABI_or_isolation')
    for policy in ('callbacks','seh','tls_fs','reentrancy','concurrency','host_pointer_in_guest'):
        require(q.get(policy) is False,'unsupported_'+policy)
    require(q.get('translation_evidence') is None,'unreviewed_translation_evidence')
    if execute: raise AdmissionError('execution_blocked:'+','.join(EXECUTION_BLOCKERS))
    return {'context_contract_admitted':True,'execution_allowed':False,'blockers':list(EXECUTION_BLOCKERS)}


CONTEXT_KEYS=frozenset(fixture_context())
