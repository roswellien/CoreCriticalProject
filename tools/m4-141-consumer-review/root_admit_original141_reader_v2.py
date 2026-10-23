"""Exact current COFF shim identities; fresh strict reader admission only."""
from pathlib import Path
import ast,copy,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-original141';T=R/'tools/m4-141-consumer-review'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h,(p,v,h);assert files.setdefault(str(p),v)==v;return p
for rel,h in [('root-strict-reader-admission-r1','dcc4268650b1298b0d96321199b8a85fef8417d63ace08b979ddf483147a57f0'),('constructor-input141-preparation-r1','7490fe66e993236952406ac18d77ed2d5b3eb3b150bf7c4c19967d6366d13785'),('root-constructor-input141-cell-controls-r1','b8dcfe1d7c27d48f28fb7c5631745de2cdf79de6e33e7095720020d02a80b1da')]:
 v=json.loads(pin(B/rel/'report.json',h).read_bytes());assert v['passed']
 for p,h in v['files'].items():pin(p,h)
links=json.loads(pin(B/'root-compiled-review-r2/physical-links.json').read_bytes());res={}
for row in links:
 for x in row['relocations']:
  if x['symbol_section']==0 and x['resolution_kind']=='virtual address':assert x['symbol']not in res or res[x['symbol']]==x['actual_symbol_address'];res[x['symbol']]=x['actual_symbol_address']
exact=tuple(res['_registry_API_'+str(i)]for i in range(8));section=next(x for x in links if x['symbol']=='reference_x86 whole source');assert len(set(exact))==8 and all(section['address']<=x<section['address']+section['bytes']for x in exact)
helper=pin(T/'constructor_input141_v1.py','1ecdf12dbd7049e2bb4f7c4405910e7cdb0b2191da400e24004d034b9939088f');s=helper.read_text();parent=pin(R/'tools/m4-138-validation-review/constructor_input_capture_phase_v1.py').read_text();assert s.replace('EXACT_SHIMS='+repr(exact)+'\n','',1).replace('and shim==EXACT_SHIMS[i]','and 0x18000000<=shim<0x19000000',1)==parent
v=pin(T/'validate_original141_v8.py','7883a49606ffcba7687123b0a31f83c53850a6953b01f061ebe0bb33248d1d7b').read_text();ds=json.loads(pin(B/'constructor-input141-preparation-r1/finite-deltas.json').read_bytes())
for d in reversed(ds['validator']):assert v.count(d['new'])==1;v=v.replace(d['new'],d['old'])
assert v==pin(T/'validate_original141_v7.py').read_text()
# Execute the complete authored 80-case production-AST block using independently
# resolved physical targets; never import a capture reader or helper module.
body=pin(T/'prepare_constructor_input141_v1.py').read_text();start=body.index(' tree=ast.parse(s);');end=body.index(' before=next(',start);block='\n'.join(x[1:]for x in body[start:end].splitlines());env=dict(ast=ast,copy=copy,s=s,helper=helper,exact=exact);exec(compile(block,'ROOT current linked identity production-AST controls','exec'),env);assert len(env['controls'])==80
pin(__file__);assert all(sha(p)==h for p,h in files.items())
out=B/'root-strict-reader-admission-r2';out.mkdir();c=out/'current-eight-shim-controls.json';c.write_text(json.dumps(env['controls'],indent=2)+'\n',encoding='utf-8');pin(c)
p=out/'report.json';p.write_text(json.dumps(dict(passed=True,original141_validator_admitted=True,reader_only_admission=True,capture_preflight_path=str(B/'root-capture-admission-r2/report.json'),capture_preflight_sha256='2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697',actual_terminal_capture_sha256='2897d2f5e3a6607e1609ea15a661a0cc76bffd12e2c9017a5b2993c7bb590820',exact_compiled_shims=exact,whole_helper_two_delta_inverse=True,whole_validator_two_binding_inverse=True,ROOT_production_identity_controls=80,ROOT_own_BEFORE_cell_controls=16,worker_relaunch_admitted=False,worker_executed=False,reader_opened=False,initializer_credit=0,accepted_function_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(sha(p),len(files))
