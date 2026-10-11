from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'run.py').read_text()
a="b=json.loads(pin(build,digest).read_text(encoding='utf-8-sig'));assert b['passed']"
b=a+"""
  preflight=json.loads(pin(BASE/'preflight-r2/report.json','28eccfbe8c54368921529ff021471db841726c18caa9392debc6e215beb8c43f').read_text());assert preflight['passed']and preflight['build_sha256']==digest
  review=json.loads(pin(ROOT/'reports/m4-tree-review/original130-prelaunch-r6/report.json','d05f854b2c5ef2aa26410ff36592f67f4e93dcf12b4f869aa01e8ad243d43a3e').read_text());assert review['passed']
  space=json.loads(pin(BASE/'space-preflight-r1/report.json','6d0373a0f48b854c898d3b7caf7eb788394f766e7fdb2868a5ff8ec291b2dd4b').read_text());assert space['passed'];import shutil;assert shutil.disk_usage(BASE).free>space['conservative_required_free_bytes']"""
assert a in s;s=s.replace(a,b)
(p/'run_v2.py').write_text(s)
