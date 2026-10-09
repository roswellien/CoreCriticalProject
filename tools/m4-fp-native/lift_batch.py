"""Produce exact static candidate IR for the required original-probed FP roots.

Unadapted Remill IR is recovery material, not native equivalence/admission.
No original game code is executed and no values are supplied by this tool.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(path):
    path=Path(path).resolve();return {'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha(path)}
def require(ok,why):
    if not ok:raise ValueError(why)
def main():
    out=Path(sys.argv[1]).resolve()
    require(out.is_relative_to(ROOT/'reports/m4-fp-native') and not out.exists(),'Fresh private native-FP output required')
    probe=ROOT/'reports/m4-fp-startup/research-r1'
    pins_path=ROOT/'reports/m4-fp-startup/run-r1/closure/pins.json'
    require(sha(pins_path)=='2e62afe363336541379664032cc6d09ae75382caf4337e63578a3a8dc3d2a3fd','Probe provenance map changed')
    pins=json.loads(pins_path.read_text())['files']
    for path in (probe/'pages.bin',probe/'extraction.json'):
        require(sha(path)==pins[str(path.resolve())],'Original probe fixture changed')
    record=json.loads((probe/'extraction.json').read_text())
    pack=(probe/'pages.bin').read_bytes()
    require(sha(record['image']['path'])==record['image']['sha256'],'Original image changed')
    repair_path=ROOT/'reports/x87-repair/toolchain/repair.json'
    repair=json.loads(repair_path.read_text())
    require(repair['remill_lifter_sha256']=='b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38' and
            repair['repaired_semantics_sha256']=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca',
            'Reviewed x87 repair identities differ')
    for path,expected in ((repair['remill_lifter_path'],repair['remill_lifter_sha256']),
                          (repair['repaired_semantics_path'],repair['repaired_semantics_sha256'])):
        require(sha(path)==expected,'Reviewed tool changed')
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    out.mkdir(parents=True)
    commands=[];roots=[]
    def run(name,args):
        p=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,timeout=45)
        (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
        commands.append({'name':name,'command':list(map(str,args)),'exit_code':p.returncode})
        require(p.returncode==0,'Candidate IR tool failed: '+name)
    pages={struct.unpack_from('<I',pack,12+i*4104)[0]:pack[12+i*4104+8:12+(i+1)*4104] for i in range(15)}
    for item in record['roots']:
        entry=item['entry'];end=item['end'];name=f'{entry:x}'
        code=pages[entry&~4095][entry&4095:(entry&4095)+end-entry]
        require(hashlib.sha256(code).hexdigest()==item['code_sha256'],'Exact slice bytes differ')
        (out/(name+'.bin')).write_bytes(code)
        run(name+'-lift',[repair['remill_lifter_path'],'--arch=x86','--os=windows',f'--address={entry}',
            '--bytes='+code.hex(),'--semantics_dir='+str(Path(repair['repaired_semantics_path']).parent),
            '--ir_out='+str(out/(name+'.ll'))])
        run(name+'-assemble',[llvm/'llvm-as.exe',out/(name+'.ll'),'-o',out/(name+'.bc')])
        run(name+'-verify',[llvm/'opt.exe','-passes=verify','-disable-output',out/(name+'.bc')])
        source=(out/(name+'.ll')).read_text()
        definitions=re.findall(r'^define .*?@([^ (]+)',source,re.M)
        declarations=re.findall(r'^declare [^@]+@([^ (]+)',source,re.M)
        require(definitions==['sub_'+name],'Complete lifted root identity differs')
        roots.append({'entry':entry,'code':bind(out/(name+'.bin')),'guest_IR':bind(out/(name+'.ll')),
            'definitions':definitions,'declarations':declarations,
            'contains_x86_fp80':'x86_fp80' in source,'ordinary_IR_verified':True,
            'translation_admitted':False})
    report={'passed':True,'scope':'Actual static guest IR candidate batch only; native execution/equivalence unproven',
            'roots':roots,'commands':commands,'sources':[bind(__file__)],
            'tools':[bind(repair['remill_lifter_path']),bind(repair['repaired_semantics_path']),bind(llvm/'llvm-as.exe'),bind(llvm/'opt.exe')],
            'original_probe':[bind(probe/'extraction.json'),bind(probe/'pages.bin'),bind(pins_path)],
            'full_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    files={str(path.resolve()):sha(path) for path in out.rglob('*') if path.is_file()}
    for group in ('sources','tools','original_probe'):
        for item in report[group]:files[item['path']]=item['sha256']
    files[str(repair_path)]=sha(repair_path)
    (out/'pins.json').write_text(json.dumps({'files':files},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'roots':len(roots),'IR_verified':True,'native_equivalence':False,'output':str(out)}))

if __name__=='__main__':main()
