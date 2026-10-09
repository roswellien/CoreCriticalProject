"""Require the exact private image, then recover static complete-function evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));from admission import IMAGE_SHA, reviewed_evidence, validate_evidence
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
RANGES={
    'selected':(0x558290,43,'fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa'),
    'timer_wrapper':(0x5996d0,52,'c9a83047c5d0758f496132c425fa619e569800f2e5aeb64e584f6f54033dc1a9'),
    'timer_callee':(0x5995b0,98,'923f7a471c6ad95f20a1b39762cc505a6da78b1d94765647f95e2d991abc5522'),
    'comparison_wrapper':(0x599710,52,'6aa073967d4d0edaaf2e362cbfabb38ac5ed993e1bddf8f71330def3a47adbf3'),
    'comparison_callee':(0x599620,176,'3e9002acd60a97201301750dc3bdba288a59f7067577509586c14e59d03fa0f0')}


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(image_path,output):
    # No missing-input pass, alternate executable, or game execution fallback.
    raw=image_path.read_bytes();require(hashlib.sha256(raw).hexdigest()==IMAGE_SHA,'wrong_image_identity')
    image=PEImage(raw);require(image.image_base==0x400000 and image.size_of_image==0x5f5000,'wrong_PE_mapping')
    objdump=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    child=subprocess.run([str(objdump),'-d','--x86-asm-syntax=intel',str(image_path)],capture_output=True,text=True,check=True)
    instructions={}
    for line in child.stdout.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(\S+)(?:\s+(.*))?$',line)
        if match:
            pc=int(match[1],16);data=bytes.fromhex(match[2]);mnemonic=match[3];operands=match[4] or ''
            instructions[pc]={'pc':pc,'size':len(data),'mnemonic':mnemonic,'operands':operands,'instruction_sha256':hashlib.sha256(data).hexdigest()}
    functions={}
    for label,(entry,size,digest) in RANGES.items():
        off,_=image.rva_range(entry-image.image_base,size);body=raw[off:off+size]
        require(hashlib.sha256(body).hexdigest()==digest,'wrong_complete_function_identity:'+label)
        decoded=[];pc=entry
        while pc<entry+size:
            require(pc in instructions,'missing_instruction_boundary:'+hex(pc));inst=instructions[pc];decoded.append(inst);pc+=inst['size']
        require(pc==entry+size and decoded[-1]['mnemonic']=='ret','incomplete_function_extent:'+label)
        branches=[];calls=[];returns=[]
        for inst in decoded:
            mnemonic=inst['mnemonic'];operands=inst['operands'];pc=inst['pc']
            if mnemonic=='call':
                target=re.match(r'0x([0-9a-f]+)',operands)
                calls.append({'pc':pc,'return_pc':pc+inst['size'],'kind':'direct' if target else 'indirect',
                              'target':int(target[1],16) if target else None,'operand':operands})
            elif mnemonic.startswith('j'):
                target=re.match(r'0x([0-9a-f]+)',operands);require(target,'unresolved_direct_CFG')
                target=int(target[1],16);require(target in {i['pc'] for i in decoded},'branch_outside_reviewed_function')
                branches.append({'pc':pc,'target':target,'fallthrough':pc+inst['size'],'condition':mnemonic})
            elif mnemonic=='ret':returns.append({'pc':pc,'callee_argument_cleanup':int(operands,0) if operands else 0})
        functions[label]={'entry_va':entry,'end_va':entry+size,'size_bytes':size,'file_offset':off,'sha256':digest,
                          'instruction_count':len(decoded),'instructions':decoded,'calls':calls,'branches':branches,'returns':returns}
    require(functions['selected']['instruction_count']==11 and not functions['selected']['calls'] and not functions['selected']['branches'], 'selected_dependency_closure_changed')
    require(functions['selected']['returns']==[{'pc':0x5582b8,'callee_argument_cleanup':8}],'selected_return_changed')
    direct={c['target'] for c in functions['timer_callee']['calls'] if c['kind']=='direct'}
    require(direct=={0x576db0,0x576da0,0x576d90,0x576d80,0x558290,0x56f520,0x51a300},'callee_dependency_inventory_changed')
    edge=next(c for c in functions['timer_callee']['calls'] if c['target']==0x558290)
    require((edge['pc'],edge['return_pc'])==(0x5995dd,0x5995e2),'selected_incoming_edge_changed')
    constant_off,_=image.rva_range(0x5cf838-image.image_base,4);constant=raw[constant_off:constant_off+4]
    require(int.from_bytes(constant,'little')==0x3a83126f,'wrong_timer_scale_global')
    constant_section=next(s for s in image.sections if s['virtual_address']<=0x5cf838-image.image_base<s['virtual_address']+s['virtual_size'])
    require(constant_section['name']=='.rdata' and not constant_section['writable'],'timer_scale_permissions_changed')
    globals_section=next(s for s in image.sections if s['virtual_address']<=0x72c000-image.image_base<s['virtual_address']+s['virtual_size'])
    require(globals_section['name']=='.data' and globals_section['writable'] and
            0x72c000-image.image_base>=globals_section['virtual_address']+globals_section['raw_size'] and
            0x72d000-image.image_base<=globals_section['virtual_address']+globals_section['virtual_size'],'wrong_selected_global_zero_fill')
    imports=image.imports();selected=[]
    for library in imports:
        for symbol in library['symbols']:
            if symbol.get('name')=='timeGetTime':selected.append({'library':library['library'],**symbol})
    require(len(selected)==1 and selected[0]['library'].lower()=='winmm.dll' and selected[0]['iat_rva']==0x1bb75c,'wrong_timer_import_binding')
    global_refs={}
    for address in (0x5cf838,0x72c1e4,0x72c1e8,0x72c1ec,0x72c1f0,0x72c1f4):
        refs=[i for i in instructions.values() if re.search(r'\b0x'+format(address,'x')+r'\b',i['operands'])]
        global_refs[hex(address)]=refs
    evidence=reviewed_evidence();validate_evidence(evidence)
    output.mkdir(parents=True,exist_ok=True)
    # Proprietary disassembly stays in ignored local reports; public tests contain none.
    disassembly=output/'private-disassembly.txt';disassembly.write_text(child.stdout)
    record={'schema_version':1,'status':'actual_image_static_admission_checked_execution_blocked','image_path':str(image_path.resolve()),
            'image_sha256':IMAGE_SHA,'image_bytes':len(raw),'image_base':image.image_base,'image_size':image.size_of_image,
            'functions':functions,'selected_evidence':evidence,'selected_global_initial':'20 zero-filled bytes; complete containing page zero-filled',
            'timer_scale':{'va':0x5cf838,'size':4,'file_offset':constant_off,'bits32':hex(int.from_bytes(constant,'little')),
                           'binary32_value':struct.unpack('<f',constant)[0],'sha256':hashlib.sha256(constant).hexdigest(),
                           'section':constant_section['name'],'permissions':'r'},
            'timer_import':selected[0],'global_direct_operand_references':global_refs,
            'global_reference_limit':'Whole-image linear decoding exposes direct operands; it does not prove absence of indirect aliases or runtime writes.',
            'candidate_rejection':['FILD_m64int/FMUL_m32real/FSTP_m64real exact translations unvalidated',
                                   'callee virtual target at object->vtable+8 unresolved',
                                   '0x56f520/0x51a300 and global object0x5f4650 closure unreviewed'],
            'evidence_tools':{str(objdump):sha(objdump),str(ROOT/'tools/analysis/pe.py'):sha(ROOT/'tools/analysis/pe.py'),
                              str(HERE/'admission.py'):sha(HERE/'admission.py'),str(Path(__file__)):sha(Path(__file__)),
                              str(disassembly):sha(disassembly)},
            'scope':'Static complete-function/context admission for M2-11 only. No translated game execution, process startup or gameplay claim.'}
    path=output/'actual-image.json';path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'record_sha256':sha(path),'selected_function_sha256':evidence['code_sha256'],
                      'selected_instruction_count':11,'closed_selected_calls':0,'image_sha256':IMAGE_SHA,'execution_allowed':False},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--image',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'reports/m2-slice-admission')
    args=parser.parse_args();inspect(args.image,args.output)
