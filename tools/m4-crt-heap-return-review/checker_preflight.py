"""Read one already published optimization archive union before final two-level sealing."""
import importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import unique_object
from stages import verify_stage
from bundle_union import BundleUnion
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
spec=importlib.util.spec_from_file_location('current_return_checker_preflight',HERE/'check.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
out=Path(sys.argv[1]).absolute();level=sys.argv[2];mapping=read(out/(level+'-partition-map.json'));records=mapping['files']
info={'logical_files':mapping['logical_files'],'bundles':[]}
for part in mapping['parts']:
    number=part['part'];stage=out/('pack-'+level+'-'+str(number));verify_stage(stage,sha_file(stage/'stage.json'));row=read(stage/'stage.json')
    if row['passed'] is not True:raise ValueError('Only completed immutable strict archives')
    bundle=out/(level+'-part-'+str(number)+'.mwb');inventory=out/(level+'-part-'+str(number)+'-inventory.json')
    info['bundles'].append({'part':number,'bundle':str(bundle),'bundle_sha256':sha_file(bundle),'inventory_path':str(inventory),'inventory_sha256':sha_file(inventory),'logical_files':part['logical_files']})
with BundleUnion(info,records) as reader:
    result=module.semantic_inventory(reader,{k:{'size_bytes':v['bytes'],'sha256':v['sha256']} for k,v in records.items()})
print(json.dumps({'passed':True,'level':level,'semantic_result':result,'full_two_level_proof_credit':False,'native_executed':False}))
