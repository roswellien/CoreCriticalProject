"""Import and physical dependency preflight; deliberately opens no captures."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];READS=set()
def audit(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
 if not reading or not p.is_relative_to(ROOT)or not p.is_file():return
 assert p.suffix.lower()not in('.mwb','.mwc')and p.name!='transport.json','Preflight must not open any capture'
 READS.add(str(p))
sys.addaudithook(audit)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 tool=ROOT/'tools/m4-formatting-source/compare_provider130_v4.py';C=load('combined130_static_preflight',tool)
 receipt=json.loads((ROOT/'reports/m4-formatting-source/persistent-family-model-r1/report.json').read_bytes());assert sha(receipt['model'])==receipt['model_sha256'];G=load('combined130_literal_preflight',Path(receipt['model']));program,callbacks=G.source_program()
 assert len(program)==4637 and len(callbacks)==195
 assert len(C.PAGES)==46 and len(C.LEGACY_PAGES)==43 and C.R.EXPECTED_LOCKIT_CALLS==36
 assert C.F.Observer.__name__=='Observer'and C.F.FORMAT_ROOTS==(0x4df610,0x4e0710,0x4e0810,0x4e1ca0)
 assert C.FD.verify_mixed.__module__=='formatting_derivations_v3'
 native=ROOT/'reports/m4-formatting-native/preparation-r19/report.json';assert sha(native)=='1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'
 joint=ROOT/'reports/m4-joint-startup130/preparation-r2/report.json';assert sha(joint)=='060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c'
 n=json.loads(native.read_bytes());j=json.loads(joint.read_bytes());assert len(j['selected_order'])==130 and set(C.F.FORMAT_ROOTS)|{0x4b64f0}<=set(j['selected_order'])
 for p in(ROOT/'tools/m4-formatting-source').glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 paths=set(READS)|{str(Path(__file__).resolve()),str(tool.resolve()),str(native.resolve()),str(joint.resolve())};files={p:sha(p)for p in sorted(paths)}
 report=dict(passed=True,scope='Bounded code/import/physical-input preflight for complete130 combined source/provider reader',selected_roots=130,physical_source_rows=len(program),source_callback_PC_count=len(callbacks),ordinary_pages=46,Lockit_calls_per_sequence=36,source_observer='final_observer130_v2.Observer',private_mixed_equality='whole32Q frames plus whole16Q raw metadata/owned/publications and whole16Q Lockit+8Q imports',current_native_preparation=str(native),current_joint_preparation=str(joint),capture_reader_opened=False,canonical_payload_bytes_read=0,executed_initializer_credit=0,actual_inputs_bound_by_run_receipt_later=True,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),files=len(files),rows=len(program))))
if __name__=='__main__':main(sys.argv[1])
