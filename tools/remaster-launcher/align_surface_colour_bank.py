"""Stage registered stock color/normal pairs in a separate 16-bit preview bank.

Only explicitly registered entries are copied from the pinned reference bank.
Unselected entry bytes and ordering are preserved. Existing banks are read-only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import struct

from normal_materials import pixel_hash
from prepare_surface_normals import bank_entries, pinned, sha


def align(source, expected_source, reference, expected_reference, materials, output):
    source,reference,output=Path(source),Path(reference),Path(output)
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('Choose a fresh aligned bank output')
    if sha(source)!=expected_source or sha(reference)!=expected_reference:
        raise ValueError('Color bank identity changed')
    table=bank_entries(source);reviewed=bank_entries(reference)
    if set(materials)-table.keys() or set(materials)-reviewed.keys():
        raise ValueError('Registered color entry is absent from a bank')
    table_bytes=24+len(table)*40
    with source.open('rb') as stream:header=bytearray(stream.read(table_bytes))
    output.parent.mkdir(parents=True,exist_ok=True);temporary=output.with_suffix(output.suffix+'.tmp')
    changed=[]
    try:
        with source.open('rb') as old,reference.open('rb') as approved,temporary.open('xb') as result:
            result.write(header)
            for i,(name,(offset,span)) in enumerate(table.items()):
                stream=old;position=offset;size=span
                if name in materials:stream=approved;position,size=reviewed[name]
                stream.seek(position);data=stream.read(size)
                if len(data)!=size:raise ValueError('Color entry changed during read')
                if name in materials:
                    flags,w,h,zero,palette,stretch=struct.unpack_from('<IHHIHH',data)
                    if flags not in (3,5,0x23,0x25) or zero or palette or stretch or len(data)!=16+w*h*2:
                        raise ValueError('Unsupported registered color entry')
                    if (w,h,1,pixel_hash(data[16:]))!=tuple(materials[name]):
                        raise ValueError('Reference pixels differ from normal registration: '+name)
                    changed.append(dict(material=name,reference_offset=position,
                                        entry_sha256=hashlib.sha256(data).hexdigest()))
                if result.tell()+len(data)>0xffffffff:raise ValueError('Color bank exceeds 32-bit offsets')
                struct.pack_into('<I',header,24+i*40+32,result.tell())
                result.write(data)
            result.seek(0);result.write(header)
        if sha(source)!=expected_source or sha(reference)!=expected_reference:
            raise ValueError('Pinned color bank changed during alignment')
        os.replace(temporary,output)
    except BaseException:
        # This is only the file created exclusively by this invocation.
        temporary.unlink(missing_ok=True)
        raise
    report=dict(source_sha256=expected_source,reference_sha256=expected_reference,
                output_sha256=sha(output),entries=len(table),changed_entries=changed,
                unchanged_entries=len(table)-len(changed))
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def redirect_bank_map(data, replacement):
    if data[:8]!=b'MWBANK1\0' or len(data)<12:raise ValueError('Invalid native bank map')
    count=struct.unpack_from('<I',data,8)[0]
    if not 0<count<=1024:raise ValueError('Invalid native bank count')
    at=12;out=bytearray(data[:12]);changed=0
    for _ in range(count):
        if at+8>len(data):raise ValueError('Truncated native bank map')
        a,b=struct.unpack_from('<II',data,at);at+=8
        if not 0<a<=4096 or not 0<b<=32768 or at+a+b>len(data):raise ValueError('Invalid bank path')
        key,path=data[at:at+a],data[at+a:at+a+b];at+=a+b
        if key==b'zbd/rmechtex16.zbd':path=str(Path(replacement).resolve()).encode();changed+=1
        out.extend(struct.pack('<II',len(key),len(path)));out.extend(key);out.extend(path)
    if at!=len(data) or changed!=1:raise ValueError('Expected exactly one 16-bit mech bank binding')
    return bytes(out)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['registration','receipt','source','output','bank_map','output_bank_map']:
        parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--allow-missing',nargs='*',default=[],help='Exact audited list of reference-only entries; no entries are added to the live bank')
    args=parser.parse_args();config=json.loads(args.registration.read_text());receipt=json.loads(args.receipt.read_text())
    if receipt['config_sha256']!=sha(args.registration):raise ValueError('Catalog receipt/registration mismatch')
    references={(r['bank']['path'],r['bank']['sha256']) for r in config['registrations']}
    if len(references)!=1:raise ValueError('Select a single reviewed reference bank')
    reference,reference_hash=next(iter(references));reference=pinned(dict(path=reference,sha256=reference_hash),args.registration.parent)
    materials={r['material']:r['key'] for r in receipt['registrations']}
    missing=set(materials)-bank_entries(args.source).keys()
    if missing!=set(args.allow_missing):raise ValueError('Reference-only entries differ from the explicit allow-missing list')
    materials={name:key for name,key in materials.items() if name not in missing}
    if not materials:raise ValueError('No aligned materials selected')
    if args.output_bank_map.exists():raise ValueError('Bank map output already exists')
    redirected=redirect_bank_map(args.bank_map.read_bytes(),args.output)
    report=align(args.source,args.source_sha256,reference,reference_hash,materials,args.output)
    args.output_bank_map.parent.mkdir(parents=True,exist_ok=True);args.output_bank_map.write_bytes(redirected)
    print('Aligned',len(report['changed_entries']),'registered entries;',report['unchanged_entries'],'entries preserved')
