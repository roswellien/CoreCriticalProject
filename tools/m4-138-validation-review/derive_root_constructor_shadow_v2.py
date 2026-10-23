"""Keep capture identities as retained metadata; hash ordinary review inputs."""
from pathlib import Path
def main():
 p=Path(__file__).with_name('root_review_constructor_shadow_v1.py');t=p.read_text();old="  for q,v in g['files'].items():pin(q,v)";new="  for q,v in g['files'].items():\n   if Path(q).suffix.lower()in('.mwb','.mwi','.zip')or Path(q).name=='transport.json':continue\n   pin(q,v)";assert t.count(old)==1
 n=t.replace(old,new).replace('constructor-shadow-root-review-r1','constructor-shadow-root-review-r2');assert n.replace(new,old).replace('constructor-shadow-root-review-r2','constructor-shadow-root-review-r1')==t
 q=p.with_name('root_review_constructor_shadow_v2.py');assert not q.exists();q.write_text(n)
if __name__=='__main__':main()
