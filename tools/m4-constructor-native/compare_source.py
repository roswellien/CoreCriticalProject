"""Strict loose-input constructor source comparison, intentionally unexecuted.

The endpoint manifest has separate input and equality-target objects. Source
derivation receives only inputs. All equality targets are read afterwards.
Capture/facade admission and physical lineage must be sealed by its exporter.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('constructor_pure_complete_derivation',R/'tools/m4-constructor-native/derive_source.py')
D=importlib.util.module_from_spec(sp);sp.loader.exec_module(D)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def main(manifest,digest,preparation,prep_digest,name):
    out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh source comparer output');out.mkdir(parents=True);files={};passed=False;results=[]
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader in loose source comparer');v=sha(p);need(h is None or h==v,'Exact loose source gate input');files[str(p)]=v;return p
    try:
        receipt=json.loads(pin(manifest,digest).read_bytes());prep=json.loads(pin(preparation,prep_digest).read_bytes());need(receipt['passed'] and receipt['original_or_native_input_export_only'] and not receipt['source_AFTER_seed'],'Pure measured input exporter receipt')
        for path,identity in receipt['files'].items():pin(path,identity)
        for path,identity in prep['files'].items():pin(path,identity)
        cases=receipt['cases'];need(len(cases)in(18,36),'Six actual original and/or two-level constructor root cases')
        for c in cases:
            inp=json.loads(pin(c['input_path'],c['input_sha256']).read_bytes())
            need(not any(k.startswith('AFTER') or k=='expected' for k in inp),'No equality target reachable from source input object')
            deriv=D.derive(inp,preparation)
            # Open candidate/original AFTER only after literal execution ended.
            expected=json.loads(pin(c['endpoint_path'],c['endpoint_sha256']).read_bytes())
            need(deriv['source_computed_State_hex']==expected['State_hex'],'Whole independently source-derived State3504 endpoint')
            need(list(deriv['source_computed_CPU'])==expected['CPU'],'Whole independently source-derived CPU40 endpoint')
            need(deriv['source_computed_FX_hex']==expected['FX_hex'],'Whole independently carried guest FX512 endpoint')
            memory=deriv['source_computed_memory'];need(set(memory)==set(expected['memory']),'Every complete admitted source region present at endpoint')
            for address,raw in memory.items():need(raw==expected['memory'][address],'Every complete source region endpoint '+address)
            if 'accesses' in expected:need([list(v)for v in deriv['accesses']]==expected['accesses'],'Every source operand ordered PC/address/width/value relation')
            results.append(dict(branch=c['branch'],sequence=c['sequence'],root=inp['root'],source_PCs=deriv['PCs'],source_accesses=deriv['accesses'],source_FS=deriv['constructor_FS'],source_getters=deriv['constructor_getters'],source_owned_writes=deriv['constructor_owned_writes'],source_flag_consumers=deriv['constructor_flag_consumers'],source_complete_owners=deriv['source_complete_owners'],source_computed_CPU=list(deriv['source_computed_CPU']),source_computed_State_sha256=hashlib.sha256(bytes.fromhex(deriv['source_computed_State_hex'])).hexdigest(),source_computed_FX_sha256=hashlib.sha256(bytes.fromhex(deriv['source_computed_FX_hex'])).hexdigest(),whole_source_regions=len(memory),AFTER_machine_seed=False))
        q=out/'source-derivations.json';q.write_text(json.dumps(results,indent=2)+'\n');pin(q);passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        for p,h in files.items():need(sha(p)==h,'All current source inputs/targets conserved')
        for p in(__file__,R/'tools/m4-constructor-native/derive_source.py',R/'tools/m4-constructor-native/game_model.py'):pin(p)
        d=dict(passed=passed,scope='Complete own-BEFORE constructor literal source gate; raw opaque original API stack spill differences require a separately physically justified liveness policy, never an unconditional mask',input_manifest_sha256=digest,preparation_sha256=prep_digest,cases=len(results),source_AFTER_seed=False,initializer_credit=0,reader_closed=True,files=files)
        p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),cases=len(results))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
