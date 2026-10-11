from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-startup130-original'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists();p=BASE/'preflight-r2/report.json';h=sha(p);assert h=='28eccfbe8c54368921529ff021471db841726c18caa9392debc6e215beb8c43f'and json.loads(p.read_text())['passed'];usage=shutil.disk_usage(BASE);need=3*1024**3;assert usage.free>need,'Original writer requires3GiB conservative available headroom'
 out.mkdir(parents=True);r=dict(passed=True,scope='Current destination disk headroom for original-only writer; native archive disk capacity remains separately admitted.',free_bytes=usage.free,conservative_required_free_bytes=need,preflight_sha256=h,files={str(p):h,str(Path(__file__).resolve()):sha(__file__)},writer_launched=False)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),free_bytes=usage.free)))
if __name__=='__main__':main(sys.argv[1])
