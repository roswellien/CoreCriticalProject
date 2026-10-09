"""Bounded floating-point planning/profile admission; no guest execution."""
import hashlib
import json
from pathlib import Path

DATA=Path(__file__).with_name('profiles.json')
DATA_SHA='d6488bfec316d20949a89bb7ed87350fc182a76d2a76b4ac9737134ddcfe5fb8'
LIVE={'state-push':'db29c3','state-pop':'db3ac3','state-exchange':'d9c9c3','state-free':'ddc1c3'}


class PolicyError(ValueError):pass


def require(ok,reason):
    if not ok:raise PolicyError(reason)


def profiles():
    raw=DATA.read_bytes();require(hashlib.sha256(raw).hexdigest()==DATA_SHA,'profile_domain_identity_changed')
    return json.loads(raw)


def classify64(bits):
    require(type(bits) is int and 0<=bits<2**64,'unsupported_operand_encoding')
    exp=(bits>>52)&0x7ff;frac=bits&((1<<52)-1)
    if exp==0:return 'subnormal' if frac else 'zero'
    if exp!=0x7ff:return 'normal'
    if not frac:return 'infinity'
    return 'QNaN' if frac&(1<<51) else 'SNaN'


def admit(profile,cw,operands,fixture_hex,*,guest_clear=False,guest_trap_delivery=False,
          exceptional_exit=False,entry_status=0,entry_stack_empty=True,other_instructions=()):
    require(guest_clear is False,'unsupported_guest_exception_clearing')
    require(guest_trap_delivery is False,'unsupported_guest_unmasked_trap_delivery')
    require(exceptional_exit is False,'unsupported_guest_exceptional_exit_policy')
    require(other_instructions==(),'unsupported_instruction_family_or_sequence')
    data=profiles();require(type(cw) is int and cw in data['control_words'],'unmasked_or_unsupported_control_word')
    require(type(fixture_hex) is str,'unsupported_instruction_sequence')
    if profile in LIVE:
        require(fixture_hex.lower()==LIVE[profile],'unsupported_instruction_sequence')
        raise PolicyError('pending_live_state_final_acceptance')
    if profile in ('control-store','control-load-store'):
        expected='d939c3' if profile=='control-store' else 'd929d93ac3'
        require(fixture_hex.lower()==expected,'unsupported_instruction_sequence')
        require(entry_status==0 and entry_stack_empty is True,'unsupported_nonclean_control_entry')
        require(type(operands) in (list,tuple) and len(operands)==1 and type(operands[0]) is int and
                operands[0] in data['control_words'],'unsupported_loaded_control_word')
        return {'profile_admitted':True,'general_execution_allowed':False,'status_policy':'control_CW_only',
                'entry_CW':cw,'loaded_CW':operands[0]}
    require(profile in data['profiles'],'unsupported_instruction_profile')
    p=data['profiles'][profile]
    require(type(fixture_hex) is str and fixture_hex.lower()==p['fixture_hex'],'unsupported_instruction_sequence')
    require(entry_status==0 and entry_stack_empty is True,'unsupported_nonclean_or_nonempty_entry')
    require(type(operands) in (list,tuple) and len(operands)==2,'unsupported_operand_encoding')
    kinds=[classify64(x) for x in operands]
    if profile=='fistp32':
        require(kinds[0] not in ('infinity','QNaN','SNaN'),'excluded_nonfinite_conversion')
        require(kinds[0]!='subnormal','excluded_subnormal_conversion')
    if profile in ('mul-special','div-special'):
        require(sum(k in ('QNaN','SNaN') for k in kinds)<2,'excluded_two_NaN_selection')
    require(list(operands) in p['vectors'],'excluded_unlisted_exact_vector_or_payload')
    return {'profile_admitted':True,'general_execution_allowed':False,'status_mask':p['exit_status_mask'],
            'input_domain':'exact_listed_vectors_only','live_state_final_acceptance':'pending'}
