from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'run_v2.py').read_text()
for a,b in [('preflight-r2/report.json','preflight-r4/report.json'),('28eccfbe8c54368921529ff021471db841726c18caa9392debc6e215beb8c43f','e43541fe81c0c19f3a407b3e6569fef7e3c85033001fe69a6480243ce3471721'),('original130-prelaunch-r6','original130-prelaunch-r7'),('d05f854b2c5ef2aa26410ff36592f67f4e93dcf12b4f869aa01e8ad243d43a3e','bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127')]:
 assert a in s;s=s.replace(a,b)
(p/'run_v3.py').write_text(s)
