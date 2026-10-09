"""Check rejected guest IR, static helper bodies and exact insertion ordering."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import adapt_state as a
import semantic_lowerings as s


def check(kind, guest, host):
    source, printed = guest.read_text(), host.read_text()
    s.descriptor(kind,printed)
    lowered = s.lower(a.constrain(source,kind),kind)
    s.descriptor(kind,lowered)
    rows = []
    def reject(name, action):
        try: action()
        except ValueError as error: rows.append({'name':name,'outcome':'rejected_before_compilation','diagnostic':str(error)})
        else: raise ValueError('Unsafe stack adapter mutation accepted:'+name)
    site = s.SITES[kind][0]
    reject('wrong_profile',lambda:s.lower(source,'unknown'))
    reject('missing_insertion_site',lambda:s.lower(source.replace(site,''),'push' if kind=='push' else kind))
    reject('duplicate_insertion_site',lambda:s.lower(source.replace(site,site+site),kind))
    reject('already_lowered_input',lambda:s.lower(lowered,kind))
    call = '  call void @'+s.NAMES[kind]+'(ptr %state'+(', ptr %1' if kind=='push' else '')+')\n'
    reject('removed_helper_call',lambda:s.descriptor(kind,printed.replace(call,'')))
    reject('duplicate_helper_call',lambda:s.descriptor(kind,printed.replace(call,call+call)))
    reject('wrong_helper_state_pointer',lambda:s.descriptor(kind,printed.replace(call,call.replace('%state','%memory'))))
    reject('helper_after_observed_operand',lambda:s.descriptor(kind,printed.replace(call+site,site+call)))
    reject('wrong_physical_tag_offset',lambda:s.descriptor(kind,printed.replace('i32 2772','i32 2773')))
    extra = s.helpers(kind)[s.NAMES[kind]].replace(s.NAMES[kind],'mw34_x87_unreviewed_prepare')
    reject('unreviewed_helper_body',lambda:s.descriptor(kind,printed+'\n'+extra+'\n'))
    if kind == 'pop':
        reject('lost_sticky_DE',lambda:s.descriptor(kind,printed.replace(s.DE_REPAIR,s.DE_SITE)))
    root = Path(__file__).resolve().parents[2]
    s.require(host.parent.resolve().is_relative_to(root), 'Adapter control workspace must stay in project')
    with tempfile.TemporaryDirectory(dir=host.parent.resolve()) as temporary:
        s.require(Path(temporary).resolve().is_relative_to(root), 'Temporary control path escaped project')
        folder = Path(temporary); altered=folder/'altered.ll';altered.write_text(source+'\n; changed identity\n')
        reject('changed_exact_guest_IR',lambda:a.adapt(Path('unloaded.dll'),altered,folder/'host.ll',folder/'layout.json',kind))
        other = 'free' if kind != 'free' else 'push'
        reject('cross_profile_IR',lambda:a.adapt(Path('unloaded.dll'),guest,folder/'host.ll',folder/'layout.json',other))
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind',choices=s.NAMES,required=True)
    for field in ('guest','host','record'):parser.add_argument('--'+field,type=Path,required=True)
    args=parser.parse_args();rows=check(args.kind,args.guest,args.host)
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    record={'schema_version':1,'status':'passed','kind':args.kind,'negative_controls':len(rows),
            'positive_controls':2,'controls':rows,'guest_ir_sha256':sha(args.guest),'host_ir_sha256':sha(args.host),
            'source_sha256':{str(p.resolve()):sha(p) for p in (Path(__file__),Path(a.__file__),Path(s.__file__),s.HELPERS_PATH)}}
    args.record.write_text(json.dumps(record,indent=2)+'\n')
    print(f'State adapter {args.kind}: {len(rows)} rejected mutations, two positive checks')


if __name__=='__main__':main()
