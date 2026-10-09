"""Extract complete import-free real startup FP roots for hardware research.

No native equivalence or full-startup admission is granted by this probe.
Original executable bytes and full page fixtures stay in ignored reports.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/analysis'))
from pe import PEImage, read_binary

IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
ROOTS = (0x4133c0,0x4adb50,0x4b5af0,0x4b7020,0x4c78f0,
         0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600)
CODE_PAGES = (0x413000,0x4ad000,0x4b5000,0x4b7000,0x4c7000,0x4ce000)
DATA_PAGES = (0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e1000,0x5e8000,0x604000,0x60b000)
STACK_PAGE = 0x20001000

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def bind(path):
    path=Path(path).resolve()
    return {'path':str(path),'size_bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def page_bytes(image, address):
    # Exact file-backed bytes and actual PE zero fill; never invent constants.
    out=bytearray(4096)
    for offset in range(4096):
        va=address+offset
        section=next((s for s in image.sections if image.image_base+s['virtual_address'] <= va <
                      image.image_base+s['virtual_address']+max(s['virtual_size'],s['raw_size'])),None)
        require(section is not None, 'Page has unmapped byte')
        within=va-image.image_base-section['virtual_address']
        if within<section['raw_size']:
            out[offset]=image.data[section['raw_offset']+within]
    return bytes(out)

def main():
    output=Path(sys.argv[1]).resolve()
    require(output.is_relative_to(ROOT/'reports/m4-fp-startup'),'Private report path required')
    require(not output.exists(),'Fresh output required')
    image_path=ROOT/'MW3/Mech3.exe'
    data=read_binary(image_path)
    require(hashlib.sha256(data).hexdigest()==IMAGE_SHA,'Exact admitted image required')
    image=PEImage(data)
    inventory=ROOT/'reports/m4-initializer-inventory/r1'
    graphs=json.loads((inventory/'function-graphs.json').read_text())
    rows=json.loads((inventory/'instruction-lookup.json').read_text())
    pages={a:bytearray(b'\xcc'*4096) for a in CODE_PAGES}
    specs=[]
    for entry in ROOTS:
        graph=graphs[str(entry)]
        require(graph['static_local_branch_decode_closed'] and not graph['direct_calls'] and
                not graph['import_sites'] and not graph['FS_sites'] and len(graph['returns'])==1,
                'Probe requires complete reviewed import-free branch graph')
        selected=[rows[str(pc)] for pc in graph['instruction_pcs']]
        end=max(row['pc']+row['size'] for row in selected)
        require(entry&~4095 in pages and (end-1)&~4095 == entry&~4095,'Code page extent differs')
        for row in selected:
            actual=image.read(image.rva_range(row['pc']-image.image_base,row['size'])[0],row['size'])
            require(actual==bytes.fromhex(row['bytes']),'Instruction bytes no longer match exact image')
        code=image.read(image.rva_range(entry-image.image_base,end-entry)[0],end-entry)
        pages[entry&~4095][entry&4095:(entry&4095)+len(code)]=code
        reads=[]; writes=[]
        for row in selected:
            address=re.search(r'\[(0x[0-9a-f]+)\]',row['operands'])
            if address:
                va=int(address[1],16)
                size=8 if 'qword ptr' in row['operands'] else 4
                require((va&~4095) in DATA_PAGES and (va+size-1)&~4095 == va&~4095,
                        'Unmapped FP operand span')
                item={'pc':row['pc'],'address':va,'size':size,'mnemonic':row['mnemonic']}
                (writes if row['mnemonic'] in ('fstp','mov') else reads).append(item)
        specs.append({'entry':entry,'end':end,'code_sha256':hashlib.sha256(code).hexdigest(),
                      'instructions':selected,'read_spans':reads,'write_spans':writes})
    # A fixed pack is admitted by a generated exact SHA in the compiled worker.
    records=[(a,1,bytes(pages[a])) for a in CODE_PAGES]
    records += [(a,2 if a in (0x604000,0x60b000) else 0,page_bytes(image,a)) for a in DATA_PAGES]
    records.append((STACK_PAGE,2,b'\xa5'*4096))
    pack=b'MW4FPK01'+struct.pack('<I',len(records))+b''.join(struct.pack('<II',a,p)+b for a,p,b in records)
    output.mkdir(parents=True)
    (output/'pages.bin').write_bytes(pack)
    header=['#pragma once','#include <array>','#include <cstdint>',
            'namespace mw34::m4_fp {',
            'inline constexpr char pack_sha[]="'+hashlib.sha256(pack).hexdigest()+'";',
            'inline constexpr std::array<std::uint32_t,10> entries{'+','.join(hex(a) for a in ROOTS)+'};',
            'inline constexpr std::array<std::uint32_t,15> page_bases{'+','.join(hex(a) for a,p,b in records)+'};',
            'inline constexpr std::array<std::uint32_t,15> page_permissions{'+','.join(str(p) for a,p,b in records)+'};','}']
    (output/'probe_spec.hpp').write_text('\n'.join(header)+'\n',encoding='utf-8')
    report={'scope':'Actual original FP output/metadata research; no native equivalence, complete CRT or live menu execution',
            'image':bind(image_path),'roots':specs,'pack':bind(output/'pages.bin'),
            'pages':[{'address':a,'permission':p,'sha256':hashlib.sha256(b).hexdigest()} for a,p,b in records],
            'inputs':[bind(inventory/n) for n in ('function-graphs.json','instruction-lookup.json')],
            'source':bind(__file__),'pe_parser':bind(ROOT/'tools/analysis/pe.py')}
    (output/'extraction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'roots':len(specs),'pages':len(records),'pack_bytes':len(pack),'output':str(output)}))

if __name__=='__main__':
    main()
