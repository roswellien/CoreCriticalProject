"""Parse fresh review sources with Python and the actual bundled PowerShell parser."""
import ast,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes

def main(name):
    base=ROOT/'reports/m4-crt-heap-return-review';out=base/name
    if not name.startswith('syntax-') or out.parent!=base or out.exists():raise ValueError('Fresh syntax receipt')
    out.mkdir();files={};parsed=[]
    def pin(p):
        p=Path(p).absolute();files[normalized(str(p))]=sha_file(p)
    for p in sorted(HERE.glob('*.py')):ast.parse(p.read_text(encoding='utf-8'));pin(p);parsed.append(p.name)
    ps=HERE/'build_controls.ps1';pwsh=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
    command="$tokens=$null;$errors=$null;[System.Management.Automation.Language.Parser]::ParseFile('"+str(ps).replace("'","''")+"',[ref]$tokens,[ref]$errors)|Out-Null;if($errors.Count){$errors|ForEach-Object{$_.Message};exit 1};[pscustomobject]@{passed=$true;parser_assembly=[System.Management.Automation.Language.Parser].Assembly.Location;PowerShell_AST_files=1}|ConvertTo-Json -Compress"
    process=subprocess.run([str(pwsh),'-NoProfile','-Command',command],capture_output=True,check=False)
    publish_bytes(out/'stdout.bin',process.stdout);publish_bytes(out/'stderr.bin',process.stderr)
    if process.returncode:raise ValueError('Actual PowerShell parser refused new build source')
    row=json.loads(process.stdout.decode('utf-8-sig'))
    if row['passed'] is not True or row['PowerShell_AST_files']!=1:raise ValueError('Exact actual syntax parser outcome')
    for p in (ps,pwsh,Path(row['parser_assembly']),Path(sys.executable),out/'stdout.bin',out/'stderr.bin',ROOT/'tools/m4-pipeline/capture_bundle.py',ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
    closure=verify_manifest(files)
    report={'passed':True,'Python_AST_files':parsed,'PowerShell_AST_files':1,'PowerShell_parser_assembly':row['parser_assembly'],'native_executed':False,'original_executed':False,'files':files,'physical_closure':closure}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'Python_AST_files':len(parsed),'PowerShell_AST_files':1}))
if __name__=='__main__':main(*sys.argv[1:])
