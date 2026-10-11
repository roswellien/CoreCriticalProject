from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
rec="1f0629822493a4edbd82b25273943e8828e79576a223e63c8a669a309972e46b"
s=(ROOT/'tools/m4-fs-source/lift.py').read_text().replace('reports/m4-fs-source','reports/m4-container-source').replace('recovery-r3','recovery-r2').replace('17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b',rec).replace('root_count=6','root_count=7')
out=ROOT/'tools/m4-container-source/lift.py';assert not out.exists();compile(s,str(out),'exec');out.write_text(s)
