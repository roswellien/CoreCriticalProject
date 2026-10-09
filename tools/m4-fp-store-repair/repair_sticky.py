"""Preserve accumulated DE in the same exact static FSTP candidate."""
from pathlib import Path
import json
import subprocess
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from repair import sha,require
def main():
    source,output,report=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    require(not output.exists() and not report.exists(),'Fresh sticky candidate required')
    first=output.with_suffix('.c1.ll');first_report=report.with_suffix('.c1.json')
    command=[sys.executable,str(Path(__file__).with_name('repair.py')),str(source),str(first),str(first_report)]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    require(result.returncode==0,'Exact first C1 candidate generation failed')
    text=first.read_text();old='  store i8 %159, ptr %160, align 1\n'
    require(text.count(old)==1 and '  %160 = getelementptr inbounds nuw i8, ptr %state, i32 2753\n'+old in text,'Exact unconditional FSTP DE overwrite required')
    new=('  %m4_prior_de = load i8, ptr %160, align 1\n'
         '  %m4_sticky_de = or i8 %159, %m4_prior_de\n'
         '  store i8 %m4_sticky_de, ptr %160, align 1\n')
    output.write_text(text.replace(old,new))
    report.write_text(json.dumps({'candidate_only':True,'original_host_sha':sha(source),'prior_C1_host_sha':sha(first),
        'repaired_host_sha':sha(output),'repair_source_sha':sha(__file__),
        'first_command':command,'first_exit_code':result.returncode,'numeric_changes':0,
        'changed_semantics':['Actual hardware C1 capture after FSTP','OR existing DE with store operand DE, preserving accumulated exception status'],
        'sticky_replacements':1},indent=2)+'\n')
    print(json.dumps({'candidate':str(output),'numeric_changes':0,'sticky_DE_replacements':1}))
if __name__=='__main__':main()
