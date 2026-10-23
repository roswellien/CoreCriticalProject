"""ROOT-only supplement sourcev4/projector to frozen cold constructor closure."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.pyc')and p.name!='transport.json';v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 oldpath=pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r3/report.json');old=json.loads(oldpath.read_bytes());assert old['prepared_only']and old['imports_executed']is False and old['ordinary_export_reader_opened']is False
 required=pin(old['required_ordinary_files'],old['required_ordinary_files_sha256']);mapping=json.loads(required.read_bytes())
 for p,h in mapping.items():pin(p,h)
 preppath=pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r4/report.json');prep=json.loads(preppath.read_bytes());assert prep['prepared_only']and prep['physical_native_ENV_projector_bound']and prep['full_computed_State_required']and prep['raw_FNStENV_from_API_FX_inferred']is False
 for p,h in prep['files'].items():pin(p,h)
 contract=pin(preppath.parent/'projector-contract.json');d=json.loads(contract.read_bytes());assert d['source_State_bytes']==3504 and d['source_x87_offset']==2768 and d['source_sw_offset']==2736 and d['hardware_ENV_equality_from_FX_claim']is False
 for p,h in d['files'].items():pin(p,h)
 config=pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r1/configuration.json','a5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0');source=pin(R/'tools/m4-startup141-paired/constructor_native36_source141_v4.py');pin(__file__)
 q=out/'required-ordinary-files.json';q.write_text(json.dumps(files,indent=2)+'\n')
 recipe='UNEXECUTED main/source/admission. ROOT independently inspect every parent inverse and Stateprojector physicalheader/layout lineage, fresh rehash required-ordinary-files.json before sourcev4 import. ROOTscope native141_constructor36_own_source, configurationSHAa5c92bfb81bcc981d1fe8adf532d4c6876f1a5eb9b28091f70e81f6f7aac37e0. CLI Python -B '+str(source)+' ADMISSION SHA '+str(config)+' CONFIG_SHA FRESH_NAME. Two native O0/O2 ordinary index/payloads only; oldoriginal138 excluded. No fullverifier/nativeworker. Entire ownBefore-to-literal CPUStateFX/Env/pages/backings and fullgame/borrowed source operands exact. State-defined ENV28 metadata separate from zeroedFX6..23. SourceAPI_FX conservation corroborates but cannot imply hardwareENV equality. Previous nonphase ownercarry remains explicitlypending; no count/fullpair/wholeoriginalState credit.\n'
 (out/'ROOT-recipe.txt').write_text(recipe);r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,initializer_credit=0,source_main=str(source),configuration_sha256=sha(config),required_ordinary_files=str(q),required_ordinary_files_sha256=sha(q),source_main_execution_admitted=False,previous_checkpoint_nonphase_owner_carry_proven=False,files={str(oldpath):sha(oldpath),str(required):sha(required),str(preppath):sha(preppath),str(contract):sha(contract),str(config):sha(config),str(source):sha(source),str(q):sha(q),str(out/'ROOT-recipe.txt'):sha(out/'ROOT-recipe.txt'),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r),ordinary_files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
