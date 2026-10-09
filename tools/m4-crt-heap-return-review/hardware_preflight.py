"""Early read-only hardware refusal check; grants no archive or complete-proof credit."""
import hashlib,importlib.util,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
p=ROOT/'tools/m4-review-bundles/transport.py'
if sha_file(p)!='0feb19971049f6547dc40cdad1f338142d48de4bc8de4f675f2d71b2bc3f619f':raise ValueError('Unchanged strict rich hardware transport')
spec=importlib.util.spec_from_file_location('unchanged_hardware_preflight',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
validator,_=module.load_validator();count=0
source=Path(sys.argv[1]).absolute()
for level in ('O0','O2'):
    tree=source/('actual-'+level)
    names=[f'case-{number}/{actor}-host-{side}.bin' for number in range(1,123) for actor in ('writer','entry') for side in ('before','after')]+[f'direct-query-failure-{diagnostic}/query-host-{side}.bin' for diagnostic in (1,2) for side in ('before','after')]
    expected={}
    for name in names:
        data=(tree/name).read_bytes();expected[name]={'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    reader=module.LogicalReader(expected,flat=tree)
    for number in range(1,123):
        for actor in ('writer','entry'):
            validator(reader.path(f'case-{number}/{actor}-host-before.bin'),reader.path(f'case-{number}/{actor}-host-after.bin'),number);count+=1
    for diagnostic in (1,2):
        validator(reader.path(f'direct-query-failure-{diagnostic}/query-host-before.bin'),reader.path(f'direct-query-failure-{diagnostic}/query-host-after.bin'),122+diagnostic);count+=1
print('Strict raw hardware preflight pairs passed: '+str(count)+'; archive closure and complete proof remain pending.')
