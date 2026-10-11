"""Bounded PE32 physical attribution of actual x86 named API observations."""
from pathlib import Path
import struct
def identities(named,mode_directory,PE,raw,pin,need,eq):
    result=[];kernel=Path('C:/Windows/SysWOW64/kernel32.dll');k=PE.PEImage(pin(kernel).read_bytes());exports={n:e for e in k.exports()for n in e['names']}
    for index,row in enumerate(named):
        reported=Path(row['module_path']);need(reported.parent.name.lower()=='system32'and reported.name.lower()in('kernel32.dll','ntdll.dll'),'Exact x86 WOW64 system-module path domain')
        physical=Path('C:/Windows/SysWOW64')/reported.name;image=PE.PEImage(pin(physical,row['module_sha256']).read_bytes());meta=struct.unpack('<8I',raw(mode_directory/f'named-API/{index}-owner-metadata.bin'));owner,target,base,size,state,protect,kind,allocation=meta
        need(owner==allocation and target==row['target']and base<=target<base+size and state==0x1000 and kind==0x1000000 and protect&0xf0 and not protect&0x101,'Actual committed executable owner image target')
        requested=row['API'];e=exports[requested];forward=e.get('forwarder','');alias=requested
        if forward:
            alias={'EnterCriticalSection':'RtlEnterCriticalSection','LeaveCriticalSection':'RtlLeaveCriticalSection'}[requested];eq(forward,'NTDLL.'+alias,'Exact kernel32 physical forwarding text');eq(physical.name.lower(),'ntdll.dll','Actual physical forwarded owner')
        else:eq(physical.name.lower(),'kernel32.dll','Actual direct named owner')
        owners=[v for v in image.exports()if alias in v['names']];need(len(owners)==1 and 'forwarder'not in owners[0],'Exact named physical owning export');rva=owners[0]['rva'];eq(owner+rva,target,'Actual image base plus exact physical export RVA')
        expected=bytearray(image.read(image.rva_range(rva,64)[0],64));relocations=[];directory,length=image.directory(5);cursor=0
        while cursor<length:
            offset=image.rva_range(directory+cursor,8)[0];page,extent=image.unpack('<II',offset);need(extent>=8 and extent%2==0 and extent<=length-cursor,'Bounded physical relocation block')
            offset=image.rva_range(directory+cursor+8,extent-8)[0]
            for slot in range((extent-8)//2):
                word=image.u16(offset+2*slot);type_,at=word>>12,page+(word&4095)
                if type_ and at<rva+64 and at+4>rva:
                    need(type_==3 and rva<=at and at+4<=rva+64,'Only complete exact HIGHLOW relocation in observed provider span');i=at-rva;value=struct.unpack_from('<I',expected,i)[0];struct.pack_into('<I',expected,i,(value+owner-image.image_base)&0xffffffff);relocations.append(at)
            cursor+=extent
        eq(expected.hex(),row['entry64_hex'],'Entire actual API entry64 is physical export plus exact source relocations')
        row.update(physical_module_path=str(physical.resolve()),owner_metadata=list(meta),owning_alias=alias,physical_forwarder=forward,physical_export_rva=rva,entry_HIGHLOW_RVAs=relocations)
        result.append(dict(API=requested,reported_module_path=str(reported),physical_module_path=str(physical.resolve()),module_sha256=row['module_sha256'],owner_metadata=list(meta),owning_alias=alias,forwarder=forward,export_rva=rva,entry64_hex=row['entry64_hex'],HIGHLOW_RVAs=relocations))
    return result
