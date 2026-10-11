"""Pure complete constructor evaluator and finite cross-branch role relations.

Callers admit only complete own source BEFORE and actual API inputs. The result
contains every source operand/frame/owner byte and root endpoint; captured
endpoints are equality targets checked by compare_source.py, never inputs here.
"""
from pathlib import Path
import copy, hashlib, importlib.util, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('constructor_complete_source_machine',R/'tools/m4-constructor-native/game_model.py')
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)

def derive(domain,preparation):
    M.I.need(set(('root','BEFORE_State_hex','BEFORE_CPU_hex','BEFORE_FX_hex','BEFORE_memory','owners','APIs'))<=set(domain),'Complete explicit constructor source inputs')
    root=domain['root'];M.I.need(root in M.ROOTS,'One of three physically prepared constructor roots')
    state=bytes.fromhex(domain['BEFORE_State_hex']);cpu=bytes.fromhex(domain['BEFORE_CPU_hex']);fx=bytes.fromhex(domain['BEFORE_FX_hex'])
    M.I.need((len(state),len(cpu),len(fx))==(3504,40,512),'Whole source BEFORE machine lengths')
    memory={int(a):bytes.fromhex(b) for a,b in domain['BEFORE_memory'].items()}
    program,callbacks=M.source_program(preparation)
    imports={(v['PC'],v['address']):dict(raw=v['raw'],target=v['target']) for v in domain.get('imports',[])}
    m=M.Machine(state,fx,cpu,memory,program=program,callbacks=callbacks,owner_roles=domain['owners'],source_imports=imports)
    frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little')
    M.I.need(m.cursor==root and frame==0x20001800 and tuple(m.projected_cpu())==struct.unpack('<10I',cpu),'Actual committed source root entry CPU/stack frame')
    m.call_stack.append((root,frame,ret,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0))
    # Do not project a scheduler token or reseed any source memory here.
    m.begin_constructor(root); response=M.ActualAPIs(domain['APIs']);m.run(lambda x:x.cursor==ret,api=response);response.complete();m.end_constructor()
    M.I.need(m.reg('esp')==frame+4 and not m.call_stack and m.fp_depth==0,'Whole normal literal root/FS/provider return')
    d=m.result()
    owners=[]
    for owner in m.constructor_owners:
        v=copy.deepcopy(owner)
        if v.get('live',True):
            raw=m.bytes(v['guest'],v['extent']);v['source_final_hex']=raw.hex()
            initial=bytes.fromhex(v['initial_hex']);M.I.need(raw[v['requested']:]==initial[v['requested']:],'Whole actual source extent unused tails conserved')
        owners.append(v)
    d.update(root=root,source_computed_CPU=tuple(m.projected_cpu()),source_computed_State_hex=bytes(m.state).hex(),source_computed_FX_hex=m.fx.hex(),source_computed_memory={str(a):bytes(b).hex() for a,b in m.memory.items()},source_complete_owners=owners,actual_API_occurrences=response.index,source_AFTER_seed=False,per_phase_reseed=False,capacity_inferred_from_rounded_extent=False,original_HardwareHeapSize_substituted_into_native=False)
    return d

def role_relations(original,native):
    """Typed pointer equality by source role; all scalar/tail bytes stay exact.

    Does not run either model and cannot convert an observation into a source
    derivation. Inputs must be the separately sealed complete derivation rows.
    Capacity is explicitly branch-owned: no equality/inference for native
    physical HeapSize unless its own actual _msize/HeapSize seam measured it.
    """
    I=M.I;I.need(original['root']==native['root'],'Same physical constructor root')
    oo=original['source_complete_owners'];nn=native['source_complete_owners']
    def key(o):return (o['role'],o['publication_site'],o['site_occurrence'])
    om={key(o):o for o in oo};nm={key(o):o for o in nn}
    I.need(len(om)==len(oo) and len(nm)==len(nn) and set(om)==set(nm),'Complete current source role/occurrence owner inventories')
    pointer_map={om[k]['guest']:nm[k]['guest'] for k in om}; rows=[]
    for k in sorted(om):
        a,b=om[k],nm[k];I.need(a['requested']==b['requested'] and a['extent']==b['extent'],'Physical source requested/rounded HeapAlloc extent')
        ar=bytes.fromhex(a['source_final_hex']);br=bytes.fromhex(b['source_final_hex'])
        I.need(len(ar)==a['extent'] and len(br)==b['extent'],'Whole own final allocation extent')
        fields=a['pointer_fields'];I.need(fields==b['pointer_fields'] and len(set(fields))==len(fields),'Exact source-owned pointer field schema')
        normalized=bytearray(ar)
        for off in fields:
            I.need(off%4==0 and off+4<=a['requested'],'Whole source-used aligned pointer cell')
            value=struct.unpack_from('<I',ar,off)[0]
            if value in pointer_map:struct.pack_into('<I',normalized,off,pointer_map[value])
            else:I.need(value==struct.unpack_from('<I',br,off)[0],'Whole carried literal non-owner pointer/scalar stays exact; opaque residue is never rewritten')
        # Requested bytes are all source-driven. Native/original unused tails
        # may start differently; both models separately proved exact carry.
        I.need(bytes(normalized[:a['requested']])==br[:b['requested']],'Every source-used byte after typed role-only pointer relation')
        rows.append(dict(role=list(k),original_guest=a['guest'],native_guest=b['guest'],requested=a['requested'],actual_source_extent=a['extent'],pointer_fields=fields,original_measured_HeapSize=a.get('measured_capacity'),native_actual_measured_capacity=b.get('measured_capacity',0),native_capacity_inferred=False,original_complete_hex=ar.hex(),native_complete_hex=br.hex(),unused_branch_tails_separately_source_conserved=True))
    return rows
