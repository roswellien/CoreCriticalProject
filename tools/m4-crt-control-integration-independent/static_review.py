"""Root static source/ABI/compiled-object association for the connected gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];GATE=ROOT/'reports/m4-crt-control-integration';PINS={}

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p,h=None):
    p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Independent static physical identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting static identity');PINS[str(p)]=got;return p
def read(p,h=None):return json.loads(bind(p,h).read_text(encoding='utf-8-sig'))
def own(p,name):
    p=bind(p);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def prove_link(crt,game,linked):
    # These four exact aliases are the complete measured llvm-link difference.
    # No arbitrary suffix stripping, helper merging, opcode masking or operand
    # normalization is permitted. Each function retains its own internal ABI.
    aliases={
        '__remill_flag_computation_carry.6':'__remill_flag_computation_carry',
        '__remill_flag_computation_zero.2':'__remill_flag_computation_zero',
        '__remill_flag_computation_sign.4':'__remill_flag_computation_sign',
        '__remill_flag_computation_overflow.8':'__remill_flag_computation_overflow',
    }
    need(len(set(aliases.values()))==len(aliases),'Bijective exact helper alias mapping')
    a,b=crt.strip_body(game),crt.strip_body(linked)
    types=lambda text:dict(re.findall(r'^(%[\w.]+) = type (.+)$',text,re.M))
    ta,tb=types(game),types(linked)
    need(len(ta)==34 and ta==tb,'All34 linked type names and complete definitions literally equal')
    attrs=lambda text:dict(re.findall(r'^attributes #(\d+) = \{([^\n]+)\}',text,re.M))
    aa,ba=attrs(game),attrs(linked)
    headers=lambda text:dict(re.findall(r'^(define[^\n]*@([\w.]+)\([^\n]*\)[^\n]*\{)$',text,re.M))
    # Above tuple order is header/name; retain exact complete signature strings.
    ah={name:head for head,name in headers(game).items()}
    bh={name:head for head,name in headers(linked).items()}
    def signature(header,attributes):
        return re.sub(r'#(\d+)\b',lambda m:'{'+attributes[m[1]]+'}',header)
    for alias,source in aliases.items():
        need(alias in b and source in a,'Every precise alias has actual complete definitions')
        need(signature(bh[alias].replace('@'+alias+'(', '@'+source+'('),ba)==signature(ah[source],aa),'Exact internal helper ABI/attributes '+alias)
        need(a[source]==b[alias] and re.fullmatch(r'identity:\s+ret i1 %0\s*',a[source]) is not None,'Exact identity body '+alias)
    need(set(a)=={'sub_5ac5a0','sub_5ac5d6',*aliases.values()},'Complete standalone game/helper set is two+four')
    def reverse(body):
        return re.sub(r'@([\w.]+)',lambda m:'@'+aliases.get(m[1],m[1]),body)
    for name in ('sub_5ac5a0','sub_5ac5d6'):
        need(signature(ah[name],aa)==signature(bh[name],ba),'Complete linked game ABI '+name)
        need(crt.canonical(reverse(b[name]))==crt.canonical(a[name]),'Actual linked game body equality after proven exact aliases')
    return {'helper_aliases':aliases,'helper_bijection_count':4,'type_aliases':{x:x for x in ta},'literal_type_definition_count':34,'game_bodies_equal_after_only_proven_aliases':True}

def link_controls(crt,game,linked):
    controls=[]
    mutations=[('helper-body',linked.replace('identity:\n  ret i1 %0','identity:\n  ret i1 true',1)),
        ('helper-signature',linked.replace('@__remill_flag_computation_carry.6(i1 noundef zeroext %0, ...)', '@__remill_flag_computation_carry.6(i8 noundef zeroext %0, ...)',1)),
        ('crossbound-helper-call',linked.replace('@__remill_flag_computation_carry.6(i1 noundef zeroext %48','@__remill_flag_computation_sign.4(i1 noundef zeroext %48',1)),
        ('State-type-field',linked.replace('%struct.Reg = type { %union.anon.1, i32 }','%struct.Reg = type { %union.anon.1, i64 }',1)),
        ('game-stack-store',linked.replace('store i32 %47, ptr %ESP, align 4','store i32 %45, ptr %ESP, align 4',1))]
    # Source identifiers vary between printed bodies; exact token corruption
    # must have actually changed the module before it can receive credit.
    for name,changed in mutations:
        need(changed!=linked,'Causal static mutation changed exact module '+name)
        try:prove_link(crt,game,changed)
        except (ValueError,KeyError) as e:controls.append({'name':name,'rejected':True,'diagnostic':str(e)})
        else:raise ValueError('Static mutation accepted '+name)
    return controls

def main(out):
    need(not out.exists() and out.is_relative_to(GATE),'Fresh independent connected static review')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'review-source.py')
    try:
        crt=own(ROOT/'tools/m4-crt-control-independent/review.py','own_root_crt_static')
        layout=own(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','own_root_numeric_layout')
        # The two reused reviewer sources must match their earlier passing pins.
        previous=read(ROOT/'reports/m4-fp-numeric-max/independent-native-review-r6/pins.json')
        need(previous['files'][str(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py')]==sha(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py'),'Frozen root layout reviewer')
        need(sha(ROOT/'tools/m4-crt-control-independent/review.py')=='49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61','Frozen root provider reviewer')
        guest=bind(GATE/'preparation-r1/guest.ll').read_text();game=bind(GATE/'research-r1/game-host.ll').read_text();linked=bind(GATE/'research-r1/host.ll').read_text()
        old_provider=bind(ROOT/'reports/m4-crt-control/research-r1/host.ll','49e25a2cd2f9279970fac099141a08742ab678eb9b041be6b1368effc55ea5a9').read_text()
        g=crt.strip_body(guest);h=crt.strip_body(game);l=crt.strip_body(linked);p=crt.strip_body(old_provider)
        link_proof=prove_link(crt,game,linked)
        controls=link_controls(crt,game,linked)
        need(set(g)=={'sub_5ac5a0','sub_5ac5d6'},'Only complete two original game definitions')
        results=[]
        types,layouts=layout.layout_model(guest);htypes,hlayouts=layout.layout_model(game)
        need(types==htypes and layouts==hlayouts,'Independent complete guest/host ABI field layout equality')
        author=read(GATE/'research-r1/game-layout.json')
        need(len(types)==34 and set(author['layouts'])=={x[1:] for x in types},'All34 declared State types')
        for name in types:
            n,a,offsets=layouts[name]
            need(author['layouts'][name[1:]]=={'size':n,'align':a,'offsets':list(offsets)},'Independent ABI size/alignment/offsets '+name)
        for name in g:
            entry=int(name[4:],16);host=h[name]
            host,n=re.subn(r'^  %checked_game_entry = call ptr @mw34_ci_enter\(ptr %state, i32 %program_counter, ptr %memory\)\n','',host,flags=re.M)
            need(n==1 and crt.canonical(host)==crt.canonical(g[name]),'Exact entry-observer removal and original body reversal')
            # The module-wide precise alias proof above closes this equality.
            pcs,calls=crt.cfg_model(g[name],entry)
            need(pcs==({0x5ac5a0,0x5ac5a5,0x5ac5aa,0x5ac5af,0x5ac5b2} if entry==0x5ac5a0 else {0x5ac5d6}),'Independent complete six source PCs')
            need(calls==([(0x5ac5aa,0x5ac5d6)] if entry==0x5ac5a0 else []),'Actual game CALL and thunk tail route')
            store=crt.state_store_audit(host,types,layouts)
            results.append({'entry':entry,'source_PCs':sorted(pcs),'direct_calls':calls,'all_state_stores':store,'source_body_reversal':True})
        for entry in (0x780042e1,0x780042f7,0x7800432c,0x7800439f):
            name=f'sub_{entry:x}';need(crt.canonical(l[name])==crt.canonical(p[name]),'Unchanged accepted provider body in actual linked module')
        helpers={name:body for name,body in h.items() if name not in g}
        need(len(helpers)==4,'Exactly four game flag identity helper definitions')
        for name,body in helpers.items():need(re.fullmatch(r'identity:\s+ret i1 %0\s*',body) is not None,'Only actual scalar flag identity helper '+name)
        rb=read(ROOT/'reports/m4-runtime/context-r9/build.json','12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5')
        for path,digest in rb['source_files'].items():bind(path,digest)
        build=read(GATE/'native-build-r1/build.json','5df2ad8c63acbc2236a1760b2fc8fe62770a304ae6eb5f1fb8ed70e9262ed524')
        need(build['passed'] and all(c['exit_code']==0 for c in build['commands']),'Actual complete build commands')
        for key in ('source_files','tool_files','artifacts'):
            for path,digest in build[key].items():bind(path,digest)
        for candidate in (game,linked):
            need('__remill_missing_block' not in candidate and not re.search(r'\b(?:inttoptr|ptrtoint)\b',candidate),'No missing block/guest host-pointer conversion')
            attrs={m[1]:m[2] for m in re.finditer(r'^attributes #(\d+) = \{([^\n]+)\}',candidate,re.M)}
            for declaration in re.findall(r'^(?:define|declare)[^\n]+@(?:sub_[a-f0-9]+|__remill_[a-z0-9_]+|mw34_c[fi]_[a-z0-9_]+)\([^\n]*\)[^\n]*',candidate,re.M):
                a=re.search(r'#(\d+)',declaration);flags=attrs[a[1]] if a else ''
                need('nounwind' not in flags and 'willreturn' not in flags,'Required complete entry/bridge fault escape attributes')
        objects=[];tool=bind(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe')
        for i,path in enumerate(p for p in build['artifacts'] if Path(p).suffix=='.obj'):
            cp=subprocess.run([str(tool),'--disassemble','--reloc','--x86-asm-syntax=intel',path],capture_output=True);log=out/f'object-{i}.txt';log.write_bytes(cp.stdout);log.with_suffix('.stderr').write_bytes(cp.stderr);bind(log);bind(log.with_suffix('.stderr'))
            need(cp.returncode==0 and re.search(rb'^\s*[0-9a-f]+:',cp.stdout,re.M) is not None,'Actual freshly decoded built object')
            objects.append({'path':path,'sha256':sha(path),'review_decode':str(log)})
        need(any(b'mw34_ci_enter' in Path(x['review_decode']).read_bytes() and b'mw34_cf_load_cw' in Path(x['review_decode']).read_bytes() for x in objects),'Actual linked object contains complete game plus accepted typed provider')
        PINS.update(layout.PINS)
        report={'passed':True,'scope':'Independent connected game/provider static source, layout, complete compiled-object and unchanged r9 association; final author/cause closure pending',
            'game_functions':results,'complete_State_bytes':3504,'complete_IR_State_alignment':8,'complete_layout_types':34,'accepted_provider_bodies_unchanged':4,'game_flag_identity_helpers':4,'linker_alias_proof':link_proof,'static_causal_controls':controls,'object_decodes':objects,'shared_r9_sources_unchanged':True,
            'final_integration_accepted':False,'following_numerical_callbacks_executed':False,'whole_M4_complete':False,
            'identity_scope':'Recorded actual build/log/source/object association and post-build hashes, not historical per-instruction tool identity attestation.'}
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');bind(p);bind(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'objects':len(objects),'report_sha256':sha(p),'pins_sha256':sha(out/'pins.json'),'bindings':len(PINS)}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
