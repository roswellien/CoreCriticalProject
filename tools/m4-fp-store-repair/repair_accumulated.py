"""Preserve prior DE at both exact FMUL and FSTP overwrites."""
from pathlib import Path
import json
import subprocess
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from repair import sha,require
def main():
    source,output,report=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    require(not output.exists() and not report.exists(),'Fresh accumulated-status candidate required')
    first=output.with_suffix('.c1.ll');first_report=report.with_suffix('.c1.json')
    command=[sys.executable,str(Path(__file__).with_name('repair.py')),str(source),str(first),str(first_report)]
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    require(result.returncode==0,'Exact first C1 candidate generation failed')
    text=first.read_text()
    for value,pointer,label in ((96,98,'mul'),(159,160,'store')):
        old=f'  store i8 %{value}, ptr %{pointer}, align 1\n'
        require(text.count(old)==1 and f'  %{pointer} = getelementptr inbounds nuw i8, ptr %state, i32 2753\n'+old in text,'Exact reviewed DE overwrite required: '+label)
        new=(f'  %m4_prior_de_{label} = load i8, ptr %{pointer}, align 1\n'
             f'  %m4_sticky_de_{label} = or i8 %{value}, %m4_prior_de_{label}\n'
             f'  store i8 %m4_sticky_de_{label}, ptr %{pointer}, align 1\n')
        text=text.replace(old,new)
    output.write_text(text)
    report.write_text(json.dumps({'candidate_only':True,'original_host_sha':sha(source),'prior_C1_host_sha':sha(first),
        'repaired_host_sha':sha(output),'repair_source_sha':sha(__file__),
        'first_command':command,'first_exit_code':result.returncode,'numeric_changes':0,
        'changed_semantics':['Actual hardware C1 capture after FSTP','OR prior DE at FMUL and FSTP, preserving earlier FLD exceptions'],
        'sticky_replacements':2},indent=2)+'\n')
    print(json.dumps({'candidate':str(output),'numeric_changes':0,'sticky_DE_replacements':2}))
if __name__=='__main__':main()
