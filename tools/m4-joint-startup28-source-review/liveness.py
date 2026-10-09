"""Bounded suffix source liveness; no whole program register policy inference."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup28-source-review'/name;assert not out.exists();out.mkdir(parents=True)
 pp=ROOT/'reports/m4-joint-startup28-original/preparation-r3/report.json';gp=ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json';graphs=json.loads(gp.read_bytes());order=json.loads(pp.read_bytes())['order'];assert order[14]['entry']==0x482cf0
 rows=[]
 for item in order[15:]:
  g=graphs[str(item['entry'])];assert g['local_decode_closed']
  reached=g['instructions'];raw='\n'.join(i['operands']for i in reached)
  assert not re.search(r'\b(?:ecx|edx|cx|dx|cl|ch|dl|dh|xmm\d+|ymm\d+|zmm\d+)\b',raw)
  assert all(i['mnemonic']not in('adc','sbb','lahf','sahf','pushf','pushfd','popf','popfd','fldenv','fstenv','fnstenv','frstor','fxrstor','fxsave','fnsave')and not i['mnemonic'].startswith(('cmov','set'))and (not i['mnemonic'].startswith('j')or i['mnemonic']=='jmp')for i in reached)
  rows.append(dict(entry=item['entry'],table_slot=item['slot'],instruction_count=len(reached),graph_instruction_sha256=g['instruction_bytes_sha256'],ECX_EDX_or_SIMD_source_references=0,CPU_arithmetic_flags_consumers=0))
 first=graphs[str(0x4adb50)]['instructions'];assert first[1]['mnemonic']=='fld'and first[1]['pc']==0x4adb60
 report=dict(passed=True,scope='Only selected13roots afterSPI in original table order, within admitted closedinstructiongraphs; no latergame/runtime/global liveness claim',suffix=rows,fields='Actualx86 ECX/EDX/CPUflags remainexactcarried observations; native representatives separatelyexactcarried. No followingselectedroot consumesECX/EDX/SIMD or oldCPUflags',legacy_metadata='NextsourceFLD482? actual4ADB60 overwrites IP/DP/FOP before reachednumericaloperations; no suffixFLDENV/FXRSTOR/sourceENVreads; actualfullAPIENVretained',first_metadata_replacement_PC=0x4adb60,first_arithmetic_flag_replacement_PC=0x4b5b30,numeric_service_leaf='Existing accepted provider780C10F0 leafFLD[78115004],RET hasnoCPUvolatileinputreads',whole_program=False,original_or_native_executed=False,files={str(p.resolve()):sha(p)for p in(pp,gp,Path(__file__),Path(sys.executable))})
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
