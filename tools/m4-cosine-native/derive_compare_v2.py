"""Keep native host restoration within the existing architectural contract."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
source = (Path(__file__).parent / 'compare.py').read_text()
before = "                assert n[8188:8700] == n[8700:9212] and n[9212:9240] == n[9240:9268]\n                counts['complete_actual_host_FP_ENV_pairs'] += 1"
after = """                host0, host1 = n[8188:8700], n[8700:9212]
                eq(host0[:5], host1[:5], 'actual restored host CW/SW/tag')
                eq(host0[24:32], host1[24:32], 'actual restored host MXCSR and mask')
                eq(host0[160:416], host1[160:416], 'actual restored host sixteen XMM registers')
                for register in range(8):
                    begin = 32 + register * 16
                    eq(host0[begin:begin + 10], host1[begin:begin + 10], 'actual restored host raw80 ' + str(register))
                eq(n[9212:9240], n[9240:9268], 'actual restored whole host ENV28')
                observations[-1]['host_FX_raw_differences'] = [dict(offset=i, before=a, after=b)
                    for i, (a, b) in enumerate(zip(host0, host1)) if a != b]
                observations[-1]['whole_host_FX512_equality_claimed'] = False
                counts['actual_architectural_host_FX_and_whole_ENV_pairs'] += 1"""
assert source.count(before) == 1
source = source.replace(before, after)
target = Path(__file__).parent / 'compare_v2.py'
assert not target.exists()
target.write_text(source)
