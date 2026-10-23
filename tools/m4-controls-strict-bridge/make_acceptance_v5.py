from pathlib import Path
R=Path(r'D:\Projects\MW34Recomp')
src=R/'tools/m4-controls-strict-bridge/acceptance138_v4.py';dst=R/'tools/m4-controls-strict-bridge/acceptance138_v5.py'
b=src.read_bytes()
EXP4='343a593a99dc771a134d6eab5918a20797891fcc2c1d69d7f8bfb3dbf0398782';POOL='4b3f3d465bfc909fbd6c4b4a7a08b26daa98bfbb50dbb2286df53c15a00616b0'
deltas=[
 (b'"""Current138 acceptance using retained131 criteria and full disk-backed union.',
  b'"""Current138 acceptance using retained131 criteria and full disk-backed union (v5: ordered-parallel whole-byte measurement; criteria/gates unchanged).'),
 (b'import acceptance138_storage_v2 as storage',b'import acceptance138_storage_v3 as storage'),
 (b"ROOT/'tools/m4-138-controls-review/full_raw_review_v2.py',ROOT/'tools/m4-138-controls-review/expand_proof_inventory.py']:",
  b"ROOT/'tools/m4-138-controls-review/full_raw_review_v2.py',ROOT/'tools/m4-138-controls-review/expand_proof_inventory_v2.py',ROOT/'tools/m4-parallel-measure/ordered_pool.py']:"),
 (b"expander_path=ROOT/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py'",
  b"expander_path=ROOT/'tools/m4-controls-terminal-composite/expand_composite_inventory_v4.py';pool_path=ROOT/'tools/m4-parallel-measure/ordered_pool.py'"),
 (b"(expander_path,'e73f992e185bd3f24a5a3d5fa1afb536f0250816e5a54130ca6e37bfc90de26a')):",
  b"(expander_path,'"+EXP4.encode()+b"'),(pool_path,'"+POOL.encode()+b"')):"),
 (b"  GRAPH=storage.load('accepted138_exact_controls_graph',graph_path)",
  b"  GRAPH=storage.load('accepted138_exact_controls_graph',graph_path);POOL=storage.load('accepted138_ordered_measure_pool',pool_path);PINS.mapper=POOL.ordered_map"),
 (b"storage.load('accepted138_full_controls_expansion',ROOT/'tools/m4-138-controls-review/expand_proof_inventory.py')",
  b"storage.load('accepted138_full_controls_expansion',ROOT/'tools/m4-138-controls-review/expand_proof_inventory_v2.py')"),
 (b"register,lambda n:print(json.dumps(dict(progress='expand_fullraw',rows=n)),flush=True))",
  b"register,lambda n:print(json.dumps(dict(progress='expand_fullraw',rows=n)),flush=True),mapper=POOL.ordered_map)"),
 (b"progress=lambda n:print(json.dumps(dict(progress='expand_distinct_controls_composite',rows=n)),flush=True))",
  b"progress=lambda n:print(json.dumps(dict(progress='expand_distinct_controls_composite',rows=n)),flush=True),mapper=POOL.ordered_map)"),
]
s=b
for a,c in deltas:assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,c)
inv=s
for a,c in reversed(deltas):assert inv.count(c)==1,c[:60];inv=inv.replace(c,a)
assert inv==b,'Exact inverse to acceptance138_v4'
assert not dst.exists();dst.write_bytes(s)
import ast;ast.parse(s.decode());print('wrote',dst)
