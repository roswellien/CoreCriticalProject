"""Bounded physical/compiled review of the genuine finite FCOS probe.

Observed FP results remain observations. This tool neither predicts cosine nor
grants native credit; it reviews compact full machine endpoints and executable
capture functions without reopening any capture archive.
"""
import collections
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,C.pin(path))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def capture_bytes(kind):
    code=bytearray();relocations=[]
    def emit(raw):code.extend(bytes.fromhex(raw))
    def address(symbol,addend=0):
        relocations.append((len(code),'_'+symbol,6));code.extend(struct.pack('<I',addend))
    def ins(op,symbol,addend=0):emit(op);address(symbol,addend)
    stores=('a3','890d','8915','891d','8925','892d','8935','893d')
    if kind=='mixed_enter':
        emit('9c60');ins('8925','mixed_host_esp');ins('0fae05','mixed_host_fx');ins('d935','mixed_host_env')
        ins('0fae0d','mixed_guest_fx');ins('833d','mixed_env_ready');emit('007406');ins('d925','mixed_guest_env')
        ins('0fae05','mixed_fx_before');ins('d935','mixed_env_before');ins('ff35','mixed_input',32);emit('9d')
        for offset,op in ((0,'a1'),(4,'8b0d'),(8,'8b15'),(12,'8b1d'),(20,'8b2d'),(24,'8b35'),(28,'8b3d'),(16,'8b25')):
            ins(op,'mixed_input',offset)
        for i,op in enumerate(stores):ins(op,'mixed_before',4*i)
        ins('8b25','mixed_host_esp');emit('9c');ins('8f05','mixed_before',32)
        ins('8b25','mixed_input',36);ins('8925','mixed_before',36);ins('8b25','mixed_input',16);ins('ff25','mixed_input',36)
    elif kind=='mixed_capture':
        for i,op in enumerate(stores):ins(op,'mixed_after',4*i)
        ins('8b25','mixed_host_esp');emit('9c');ins('8f05','mixed_after',32)
        ins('c705','mixed_after',36);emit('800a4100')
        ins('0fae05','mixed_fx_after');ins('d935','mixed_env_after');ins('0fae0d','mixed_host_fx');ins('d925','mixed_host_env')
        ins('0fae05','mixed_host_after');ins('d935','mixed_host_env_after');ins('d925','mixed_host_env');emit('619dc3')
    else:
        C.need(kind=='mixed_restore','Only exact capture/broker functions')
        ins('0fae0d','mixed_host_fx');ins('d925','mixed_host_env');ins('0fae05','mixed_host_after')
        ins('d935','mixed_host_env_after');ins('d925','mixed_host_env');emit('c3')
    return bytes(code),relocations


def matching_linked_function(image,expected,relocations):
    ignored={i for offset,_,_ in relocations for i in range(offset,offset+4)}
    prefix=expected[:relocations[0][0]]
    candidates=[]
    for section in image.sections:
        if not section['executable']:continue
        raw=image.data[section['raw_offset']:section['raw_offset']+section['raw_size']]
        start=0
        while True:
            start=raw.find(prefix,start)
            if start<0:break
            actual=raw[start:start+len(expected)]
            if len(actual)==len(expected)and all(a==b for i,(a,b)in enumerate(zip(actual,expected))if i not in ignored):
                candidates.append((image.image_base+section['virtual_address']+start,actual))
            start+=1
    C.need(len(candidates)==1,'One unique complete final-linked capture byte pattern')
    return candidates[0]


def main(name):
    out=ROOT/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh additive cosine review');out.mkdir(parents=True)
    passed=False;counts=collections.Counter();observations=[];linked=[]
    try:
        C.pin(__file__);C.pin(C.__file__)
        path=ROOT/'reports/m4-cosine-original/prefix-validation-r2/report.json'
        report=C.read(path,'cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e')
        C.need(report['passed']and report['reader_closed']and report['source_after_seed']is False and
               report['host_cos_expected_output_used']is False and report['predicted_FP_outputs_used_as_expected']is False and
               report['source_native_equivalence']is False and report['initializer_credit']is False,
               'Only measured original finite hardware credit; no predicted/native FP proof')
        execution=C.read(report['execution_path'],report['execution_sha256'])
        build=C.read(execution['build_path'],execution['build_sha256'])
        prep_path=Path(build['preparation']);prep=C.read(prep_path/'report.json',build['preparation_sha256'])
        C.need(execution['passed']and build['passed']and prep['passed']and build['sequences']==build['phases']==6 and
               build['roots']==1 and build['record_bytes']==356992 and prep['source_instruction_rows']==19 and
               prep['source_instruction_bytes']==110,'Actual selected one-root six-case worker and immutable ABI')
        for filename in ('reference.cpp','reference_x86.asm','protocol.hpp','spec.hpp','instruction-contracts.json'):
            C.pin(prep_path/filename,prep['files'][str(prep_path/filename)])
        C.pin(ROOT/'tools/m4-cosine-original/prepare_v3.py',prep['files'][str(ROOT/'tools/m4-cosine-original/prepare_v3.py')])
        C.pin(ROOT/'tools/m4-cosine-original/validate_v2.py',report['files'][str(ROOT/'tools/m4-cosine-original/validate_v2.py')])
        contract=C.read(prep_path/'instruction-contracts.json',prep['files'][str(prep_path/'instruction-contracts.json')])
        PE=module(ROOT/'tools/analysis/pe.py','cosine_independent_PE')
        game_path=ROOT/'MW3/Mech3.exe';C.pin(game_path,prep['files'][str(game_path)])
        game=PE.PEImage(game_path.read_bytes())
        pack=C.pin(prep_path/'pages.bin',prep['pack_sha256']).read_bytes()
        C.need(pack[:8]==b'MW4J124P','Physical exact page pack magic')
        records={}
        for i in range(struct.unpack_from('<I',pack,8)[0]):
            offset=12+i*4104;page,permission=struct.unpack_from('<II',pack,offset)
            C.need(page not in records,'No duplicate finite page source input')
            records[page]=(permission,pack[offset+8:offset+4104])
        data_section=next(section for section in game.sections if
                          game.image_base+section['virtual_address']<=0x5e8000<game.image_base+section['virtual_address']+max(section['raw_size'],section['virtual_size']))
        C.need(data_section['writable']and records[0x5e8000][0]==2 and records[0x5c9000][0]==0 and
               prep['source_permission_update']['page']==0x5e8000 and prep['source_permission_update']['from']==0 and
               prep['source_permission_update']['to']==2,'Physical PE writable data justifies exact single output-page RW promotion')
        opcounts=collections.Counter()
        for row in contract['instructions']:
            offset,end=game.rva_range(row['pc']-game.image_base,row['width'])
            raw=game.data[offset:offset+row['width']]
            C.need(raw.hex()==row['bytes_hex']and records[row['pc']&~4095][1][row['pc']&4095:(row['pc']&4095)+row['width']]==raw,
                   'Every actual physical source instruction and unchanged mapped code span')
            opcounts[row['mnemonic']]+=1;counts['physical_reachable_instruction_rows']+=1;counts['physical_reachable_instruction_bytes']+=row['width']
        C.need(opcounts=={'jmp':1,'fld':3,'fcos':3,'mov':7,'fstp':3,'xor':1,'ret':1}and
               contract['source_imports']==contract['normal_FS_sites']==[]and contract['callbacks_registered']==0,
               'Complete reachable source has only three compound x87 operations, seven scalars, XOR and RET')
        C.need([r['pc']for r in contract['instructions']if r['mnemonic']=='fcos']==[0x4b6506,0x4b6552,0x4b6560],
               'Exactly three genuine compound FCOS source sites')
        for item in prep['source_default_inputs']:
            address=item['address'];offset,end=game.rva_range(address-game.image_base,8);raw=game.data[offset:offset+8]
            C.need(raw.hex()==item['bytes_hex']and records[address&~4095][1][address&4095:(address&4095)+8]==raw,
                   'Complete immutable physical default double input bytes')
            counts['physical_immutable_double_inputs']+=1
        worker_path=C.pin(build['worker'],build['worker_sha256']);worker=PE.PEImage(worker_path.read_bytes())
        COFF=module(ROOT/'tools/m4-fs-source/observer_attribution.py','cosine_independent_COFF')
        release=worker_path.parent/'build-x86/mw34_joint_startup124_original.dir/Release'
        symbols,sections=COFF.parse_coff(C.pin(release/'reference_x86.obj').read_bytes())
        defs={row['name']:row for row in symbols.values()if row['section']>0 and row['storage']==2}
        commands=list(release.rglob('link.command.1.tlog'));C.need(len(commands)==1,'One actual completed link command')
        command=C.pin(commands[0]).read_text(encoding='utf-16');C.need('REFERENCE_X86.OBJ'in command.upper(),'Actual capture COFF linked into current worker')
        addresses={}
        for name in ('mixed_enter','mixed_capture','mixed_restore'):
            expected,relocations=capture_bytes(name);definition=defs['_'+name];section=sections[definition['section']]
            actual=section['bytes'][definition['value']:definition['value']+len(expected)]
            C.need(actual==expected,'Every compiled capture/save/restore byte independently reconstructed')
            C.need([(offset-definition['value'],symbol,type_)for offset,symbol,type_ in section['relocations']
                    if definition['value']<=offset<definition['value']+len(expected)]==relocations,
                   'Every compiled capture relocation/addend exact')
            target,actual=matching_linked_function(worker,expected,relocations)
            for offset,symbol,type_ in relocations:
                C.need(type_==6,'Only exact direct capture storage relocations')
                address=(struct.unpack_from('<I',actual,offset)[0]-struct.unpack_from('<I',expected,offset)[0])&0xffffffff
                C.need(symbol not in addresses or addresses[symbol]==address,'All final shared capture storage identities coherent')
                addresses[symbol]=address
            linked.append(dict(name=name,address=target,bytes=len(expected),relocations=len(relocations)))
            counts['compiled_final_capture_functions']+=1;counts['compiled_final_capture_bytes']+=len(expected);counts['compiled_final_capture_relocations']+=len(relocations)
        ends=C.read(report['observations'],report['observations_sha256'])
        C.need(len(ends)==6 and prep['source_CW_TOP_cases']==[[0,127,0],[0,895,7],[0,3967,0],[1,1151,7],[1,2687,0],[1,3711,7]],
               'All measured actual six finite CW/TOP cases')
        for sequence,(actual,case)in enumerate(zip(ends,prep['source_CW_TOP_cases'])):
            C.need(actual['sequence']==sequence and [actual['repeat'],actual['CW'],actual['TOP']]==case and
                   actual['host_restored']is True and actual['XOR_AF_architecturally_undefined']is True,
                   'Exact complete independent endpoint case and architectural flag scope')
            before=actual['BEFORE_CPU'];after=actual['AFTER_CPU'];C.need(len(before)==len(after)==10,'Whole actualCPU40 retained')
            C.need(before[9]==0x4b64f0 and after[9]==0x410a80 and after[0]==0 and after[4]==before[4]+4 and
                   all(before[j]==after[j]for j in (1,2,3,5,6,7))and
                   (after[8]&~0x8d5)==(before[8]&~0x8d5)and(after[8]&0x8c5)==0x44,
                   'Literal XOR/RET and every unchanged whole GPR/defined flag')
            fx0=bytes.fromhex(actual['BEFORE_FX512_hex']);fx1=bytes.fromhex(actual['AFTER_FX512_hex'])
            env0=bytes.fromhex(actual['BEFORE_ENV28_hex']);env1=bytes.fromhex(actual['AFTER_ENV28_hex'])
            C.need(len(fx0)==len(fx1)==512 and len(env0)==len(env1)==28,'Complete original hardware FX512/ENV28 bytes')
            word=lambda b,offset:struct.unpack_from('<H',b,offset)[0]
            C.need(word(fx0,0)==word(fx1,0)==word(env0,0)==word(env1,0)==case[1]and
                   ((word(fx0,2)>>11)&7)==((word(fx1,2)>>11)&7)==case[2]and
                   fx0[4]==fx1[4]==0 and word(env0,8)==word(env1,8)==0xffff and not(word(fx1,2)&0x400),
                   'Actual empty x87 stack, carried sourceCW/TOP and cleared range flag')
            C.need(fx0[24:32]==fx1[24:32]and fx0[160:]==fx1[160:]and
                   struct.unpack_from('<I',env1,12)[0]==0x4b6562 and struct.unpack_from('<I',env1,20)[0]==0x5e8888,
                   'Architectural untouched SSE/control bytes and exact final source x87 instruction/data metadata')
            C.need([item['bytes_hex']for item in actual['inputs']]==[item['bytes_hex']for item in prep['source_default_inputs']]and
                   [item['address']for item in actual['outputs']]==[0x5e8880,0x5e8884,0x5e8888]and
                   all(item['observed_only']is True and len(bytes.fromhex(item['bytes_hex']))==4 for item in actual['outputs']),
                   'All physical input bytes and actual unpredicted FSTP slots retained separately')
            observations.append(dict(sequence=sequence,latent_ST_byte_differences=[i for i in range(32,160)if fx0[i]!=fx1[i]],
                                     status_before=word(fx0,2),status_after=word(fx1,2),
                                     actual_outputs=actual['outputs'],x87_latent_register_conservation_claimed=False))
            counts['complete_actual_CPU_FX_ENV_endpoint_cases']+=1;counts['observed_only_FCOS_results']+=3
        C.need(report['counts']['whole_page_endpoint_relations']==516 and report['counts']['literal_scalar_stores']==42 and
               report['counts']['full_host_restoration_relations']==6,'Producing original observer supplies all43 pages/host restoration; no independent archive reread claimed')
        passed=True
    finally:
        artifact=out/'physical-and-endpoint-review.json';artifact.write_text(json.dumps(dict(linked=linked,endpoints=observations),indent=2)+'\n');C.pin(artifact)
        target=out/'report.json';target.write_text(json.dumps(dict(passed=passed,counts=dict(counts),files=C.PINS,
                    scope='Independent physical default source/pack/writable-data permission, full compiled/final-linked capture functions and compact complete genuine machine endpoint review',
                    capture_archives_opened=0,host_cos_expected_output_used=False,source_AFTER_seed=False,native_equivalence=False,
                    x87_latent_register_conservation_claimed=False,whole_architectural_x87_endpoint_retained=True,initializer_credit=False),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))


if __name__=='__main__':main(sys.argv[1])
