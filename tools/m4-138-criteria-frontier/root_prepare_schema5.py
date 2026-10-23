"""Create exact ROOT admission derivative for current compiler tlog scope."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-criteria-frontier/root_admit_schema_v4.py';t=p.read_text()
for a,b in [('root-schema-admission-r4','root-schema-admission-r5'),('root-schema-admission-r3/report.json','root-schema-admission-r4/report.json'),('001dcf86a94e7e88994253c240716a6a8040704a4288c9fa2eece7e3f78e874c','da06bc10f7e576d95f6ab22a1b25d9999199b37ecb58f812f9094d1c1aa244d8'),('schema-checker-preparation-r6','schema-checker-preparation-r7'),('schema-checker-preparation-r4','schema-checker-preparation-r6'),('e337ba3bd78f717dd25dc7888bb164042f9c01526d9e82db331f34787eea0549','21204a6c0511100caae296f557710124de7f2d35d2223cf365d715ef54af4d11'),('check_schema138_v5.py','check_schema138_v6.py'),('06343be28bc404d11cbaf923a098c894f91435d56f55198a8297ec17914d26df','737749fb40562ed9ce89a3d1b9944e41eb936e158810101b097415cca6dbda09'),('check_schema138_v3.py','check_schema138_v5.py'),('517c18c1ff14151fabb98326ffed73f8da0acbac4b85fb50961c7dfdec4b05ef','06343be28bc404d11cbaf923a098c894f91435d56f55198a8297ec17914d26df'),('positive-files-preflight-r1','tlog-preflight-r1'),('327c493959262b9cd51175429cbfa82f2de48d1f66b3cc5f9ab9d2b3a485e7f6','c2240b835d00c51b07a546443c36bf7e13af56714614f1e942967e4b4ddb4734')]:
 assert a in t;t=t.replace(a,b)
a="delta=d['checker_source_delta'];anchor=delta['anchor'];addition=delta['addition']\n+ assert text.count(anchor+addition)==1 and text.count(delta['after'])==1\n+ inverse=text.replace(anchor+addition,anchor).replace(delta['after'],delta['before'])".replace('\n+ ','\n ')
b="delta=d['checker_source_delta']\n assert text.count(delta['after'])==1\n inverse=text.replace(delta['after'],delta['before'])"
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace("assert inverse==runpy.run_path(str(base),run_name='root_definition_only')['s']","assert inverse==base.read_text()")
t=t.replace('Two genuine positive-file extensions require whole inverse and actual source-derived callback/page union; every inherited file remains required','Actual successful compiler command, project source/IntDir, linked byte identity and worker tlog ownership required; consumed266 domain preserved')
q=p.with_name('root_admit_schema_v5.py');assert not q.exists();q.write_text(t)
