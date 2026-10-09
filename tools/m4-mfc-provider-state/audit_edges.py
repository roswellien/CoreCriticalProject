"""Independent narrow inventory edge/import/owner association audit."""
import copy
import importlib.util
import json
import ntpath
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('owned_mfc_recovery',Path(__file__).with_name('recover.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def edges(doc,pe):
    imports={pe.image_base+s['iat_rva']:dict(library=lib['library'],**s)
             for lib in pe.imports() for s in lib['symbols']}
    entries={b['graph']['entry_va'] for b in doc['bodies'] if b['image']=='mfc42_staged'}
    answer=[]
    for body in doc['bodies']:
        if body['image']!='mfc42_staged':continue
        for row in body['graph']['calls']+body['graph']['exits']:
            if 'target_va' not in row and row['kind']!='unresolved indirect branch':continue
            operand=row['operands'];match=M.re.fullmatch(r'dword ptr \[0x([0-9a-f]+)\]',operand)
            slot=int(match[1],16) if match else None;dest=row.get('target_va')
            item=dict(owner=body['graph']['entry_va'],pc=row['pc'],operands=operand,
                      kind='CALL' if 'target_va' in row else 'tail branch',target_va=dest,
                      disposition='selected helper local CFG only' if dest in entries else
                                  'direct helper missing dependency closure' if dest is not None else
                                  'exact IAT import service still required' if slot in imports else
                                  'unresolved indirect receiver/function pointer')
            if slot in imports:item.update(iat_va=slot,raw_iat_word=struct.unpack('<I',M.raw(pe,slot,4))[0],import_identity=imports[slot])
            answer.append(item)
    return answer


def validate(doc,pe):
    exact=edges(doc,pe)
    M.need(doc['source_edges']==exact,'Every source edge/owner/PC/target/rawIAT/import identity')
    M.need(doc['unclosed_source_targets']==sorted({e['target_va'] for e in exact if e['disposition']=='direct helper missing dependency closure'}),
           'Exact remaining helper frontier')
    facts={f['id']:f for f in doc['source_facts']}
    expected={
        'thread_access':dict(manager_global=0x5f4cb000,manager_TLS_index_offset=0,TLS_object_bound_offset=8,TLS_array_pointer_offset=12,
                             factory_call_pc=0x5f401067,factory_argument_offset=12),
        'module_access':dict(thread_factory=0x5f4053fe,thread_key_holder=0x5f4cb03c,current_module_pointer_offset=4,
                             fallback_factory=0x5f40b293,fallback_holder=0x5f4cb040),
        'factories':dict(allocation_sizes=[0x118,0x1090,0x84],constructors=[0x5f40544f,0x5f40b2df,0x5f405665]),
        'shared_lazy_access':dict(lock_index=16,normal_ret_bytes=4),
        'app_receiver_publication':dict(receiver_va=0x608c88,module_state_offset=4,receiver_saved_module_offset=0x1c,
                                        thread_factory=0x5f405631,per_module_thread_key_offset=0x108c),
        'application_callback_gate':dict(module_accessor=0x5f401083,application_slot_offset=4)}
    for fact,fields in expected.items():
        for key,value in fields.items():M.need(facts[fact][key]==value,'Literal operand/receiver owner '+fact+'/'+key)
    # These are preparation dependency gates, not a claim that all source calls form a DAG.
    M.need(doc['gate_order']==['provider-selection','guest-SEH','platform-resources','thread-slots','module-factories',
                              'module-context','app-object-lifetime','application-native-callback'],'Narrow preparation gate order')
    M.need(all(g['native_credit'] is False and g['implemented'] is False for g in doc['gates']),'No implementation/native gate credit')
    M.need(all(g['initialized_runtime_value'] is None and M.raw(pe,g['va'],4).hex()==g['raw_file_bytes'] and
               struct.unpack('<I',M.raw(pe,g['va'],4))[0]==g['raw_file_DWORD'] for g in doc['raw_provider_globals']),
           'Original global raw identity without initialized-value claim')


def main():
    out=ROOT/'reports/m4-mfc-provider-state/edge-audit-r1'
    M.need(not out.exists(),'Fresh owned report required')
    base=ROOT/'reports/m4-mfc-provider-state/recovery-r1'
    doc=json.loads((base/'inventory.json').read_text());receipt=json.loads((base/'report.json').read_text())
    pins=json.loads((base/'pins.json').read_text())['files']
    M.need(receipt['passed'] and M.digest((base/'inventory.json').read_bytes())==receipt['inventory_sha256'] and
           M.digest((base/'pins.json').read_bytes())==receipt['pins_sha256'],'Exact original source recovery receipt')
    pe=M.PEImage(Path(doc['images']['mfc42_staged']['path']).read_bytes())
    validate(doc,pe)
    probes=[('edge-owner',lambda d:d['source_edges'][0].__setitem__('owner',0)),
            ('edge-call-target',lambda d:d['source_edges'][0].__setitem__('target_va',0)),
            ('raw-import-word',lambda d:next(e for e in d['source_edges'] if 'raw_iat_word' in e).__setitem__('raw_iat_word',0)),
            ('module-factory',lambda d:d['source_facts'][1].__setitem__('fallback_factory',0)),
            ('initialized-global',lambda d:d['raw_provider_globals'][0].__setitem__('initialized_runtime_value',0)),
            ('missing-helper',lambda d:d['unclosed_source_targets'].pop())]
    denials=[]
    for name,mutate in probes:
        changed=copy.deepcopy(doc);mutate(changed)
        try:validate(changed,pe)
        except ValueError:denials.append(name)
        else:raise ValueError('Same edge validator admitted '+name)
    bindings={}
    for info in pins:
        key=ntpath.normcase(ntpath.normpath(str(Path(info['path']).absolute())))
        M.need(key not in bindings or info['sha256']==bindings[key]['sha256'],'No source path conflict')
        bindings[key]=info
    for path in [base/'report.json',base/'pins.json',Path(__file__).absolute(),ROOT/'reports/m4-mfc-provider-state/check-r1/report.json']:
        data=path.read_bytes();key=ntpath.normcase(ntpath.normpath(str(path.absolute())))
        info=dict(path=str(path.absolute()),size_bytes=len(data),sha256=M.digest(data))
        M.need(key not in bindings or info['sha256']==bindings[key]['sha256'],'No association conflict')
        bindings[key]=info
    for info in bindings.values():
        data=Path(info['path']).read_bytes()
        M.need(len(data)==info['size_bytes'] and M.digest(data)==info['sha256'],'Final physical source identity')
    out.mkdir(parents=True)
    (out/'pins.json').write_text(json.dumps(dict(schema_version=1,files=sorted(bindings.values(),key=lambda i:i['path'].lower())),indent=2)+'\n')
    report=dict(passed=True,scope='Read-only exact source edge/import/owner/global inventory audit; no code execution',
                recovery_report_sha256=M.digest((base/'report.json').read_bytes()),source_edges=len(doc['source_edges']),
                unclosed_direct_targets=len(doc['unclosed_source_targets']),gate_count=len(doc['gates']),
                shared_validator_denials=denials,pins_sha256=M.digest((out/'pins.json').read_bytes()),
                unique_physical_bindings=len(bindings),native_execution_credit=False,source_implementation_credit=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=report,report_sha256=M.digest((out/'report.json').read_bytes()))))


if __name__=='__main__':main()
