"""Read active upgraded banks and make a review-only texture-light inventory.

No texture, catalog or light setting is changed. Catalog registration is not
proof that a particular bulb/UV island receives the intended runtime light.
"""
from pathlib import Path
import argparse, collections, csv, hashlib, html, json, re, struct
import numpy as np
from PIL import Image
from prepare_effect_lights import banks
from prepare_surface_normals import bank_entries
from prepare_world_normals import accelerated_hash
from campaign_material_source import converted_color

ROOT=Path(__file__).resolve().parents[2]
SHA=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()

def append_models(data,folder,profile):
    """Include registered replacement atlases, which bypass source fixture scans."""
    cfg=json.loads(profile.read_text(encoding='utf-8-sig'));n=cfg['native']
    registry=ROOT/n.get('model_registry','local/remaster/models.json')
    models=json.loads(registry.read_text())['models'];unique={}
    for model in models:
        if model.get('id') not in n['model_ids'] or model.get('backend')!='native':continue
        for skin in [dict(id='default',textures=model.get('textures',{}))]+model.get('skins',[]):
            for material,relative in skin['textures'].items():
                path=ROOT/relative;before=path.stat();im=Image.open(path).convert('RGB');im.load()
                identity=(im.size,hashlib.sha256(im.tobytes()).hexdigest());source=dict(bank='replacement-model/'+model['id']+'/'+skin['id'],name=model['id']+'/'+material,path=str(path),source_sha256=SHA(path))
                assert (before.st_size,before.st_mtime_ns)==(path.stat().st_size,path.stat().st_mtime_ns)
                if identity in unique:unique[identity]['sources'].append(source);continue
                notes=signals(im.copy());idx=len(unique)+1;image=f'images/model-{idx:04d}.jpg';size=im.size;im.thumbnail((512,512));im.save(folder/image,quality=92,subsampling=0)
                unique[identity]=dict(id=f'M{idx:04d}',width=size[0],height=size[1],pixel_sha256=identity[1],sources=[source],signals=notes,name_signal=True,fixture_matches=[],fixture_types=[],status='MODEL MATERIAL - NOT REGISTERED',effect_catalog=False,runtime_keys=[],candidate=True,decision='unreviewed',image=image,category='replacement-model atlas; no source-fixture observation')
    for row in unique.values():
        row['names']=sorted(set(s['name'] for s in row['sources']));row['banks']=sorted(set(s['bank'] for s in row['sources']))
    data['unique_bank_textures']=data['unique_textures'];data['replacement_material_variants']=len(unique)
    data['rows'].extend(unique.values());data['unique_textures']=len(data['rows']);data['candidates']=sum(r['candidate'] for r in data['rows'])
    data['model_registry']=str(registry);data['model_registry_sha256']=SHA(registry)

def signals(image):
    image.thumbnail((128,128),Image.Resampling.BOX)
    a=np.asarray(image,dtype=np.float32);r,g,b=np.moveaxis(a,-1,0)
    masks={'red patches':(r>90)&(r>g*1.65)&(r>b*1.65),
           'green patches':(g>115)&(g>r*1.5)&(g>b*1.25),
           'blue/cyan patches':(b>120)&(b>r*1.45)&(b>g*.85),
           'amber patches':(r>155)&(g>85)&(b<g*.65)&(r>g*1.08),
           'bright white patches':(np.minimum.reduce([r,g,b])>190)}
    result=[]
    for label,m in masks.items():
        fraction=float(m.mean())
        # Broad recall; painted markings/reflections remain explicit false positives.
        if .0008<=fraction<=.35 and m.sum()>=4:result.append(label)
    return result

def audit(profile,out,library):
    if out.exists():raise ValueError('Choose a fresh audit folder')
    out.mkdir(parents=True);(out/'images').mkdir()
    cfg=json.loads(profile.read_text(encoding='utf-8-sig'));n=cfg['native'];env=n['runtime_environment']
    exe=ROOT/n['executable'];assert SHA(exe)==n['executable_sha256']
    host=exe.parent.parent/'host-source';catalog=(host/'fixture_lighting.hpp').read_text()
    pattern=r'\{\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*0x([0-9a-f]+)ULL\s*,[^\n]*?\b(true|false)\s*\}'
    fixtures=[dict(name=m[0],w=int(m[1]),h=int(m[2]),fmt=int(m[3]),hash=int(m[4],16),kind='spot' if m[5]=='true' else 'point') for m in re.findall(pattern,catalog,re.I)]
    assert fixtures
    fx=(ROOT/env['MW34_EFFECT_LIGHT_CATALOG']).read_bytes();assert fx[:8]==b'MWFX1\0\0\0'
    effects={(w,h,f,d) for w,h,f,k,d,*rest in struct.iter_unpack('<IIIIQ6f',fx[12:])}
    digest=accelerated_hash(library);records={};skipped=[];pins=[];total=0
    active=ROOT/env['MW34_REMASTER_BANKS'];banklist=banks(active)
    for bank,path in banklist:
        print('Scanning',bank,flush=True);before=path.stat();table=bank_entries(path)
        with path.open('rb') as stream:
            for name,(offset,span) in table.items():
                total+=1;stream.seek(offset);desc=stream.read(16)
                flags,w,h,res,pal,stretch=struct.unpack('<IHHIHH',desc);base=flags&~96
                # The stretch field controls mapping, not the RGB565 plane layout.
                if base not in (3,5,11) or res or pal or not 0<w<=4096 or not 0<h<=4096 or span!=16+w*h*(3 if base==11 else 2):
                    skipped.append(dict(bank=bank,name=name,flags=flags,width=w,height=h,span=span));continue
                raw=stream.read(w*h*2);coverage=stream.read(w*h) if base==11 else None
                identity=(w,h,hashlib.sha256(raw+(coverage or b'')).hexdigest())
                source=dict(bank=bank,name=name,offset=offset)
                if identity in records:records[identity]['sources'].append(source);continue
                words=np.frombuffer(raw,'<u2').reshape(h,w).astype('uint32')
                alpha=np.frombuffer(coverage,'uint8').reshape(h,w) if coverage is not None else np.where(words!=0,255,0).astype('uint8') if base==3 else None
                rgb=np.stack(((words>>11)*255//31,((words>>5)&63)*255//63,(words&31)*255//31),axis=-1).astype('uint8')
                im=Image.fromarray(rgb);notes=signals(im.copy());name_signal=bool(re.search(r'light|lamp|glow|flare|beacon|runway|bay|hangar|control|panel|screen|window|reactor|\bled\b',name,re.I))
                keys=[];matches=[];effect=False
                for fmt in ([1,2,3] if alpha is not None else [1]):
                    pixels=converted_color(words,alpha,fmt);variants=[pixels]
                    if fmt!=1:
                        zeroed=np.frombuffer(pixels,'<u2').copy().reshape(h,w);zeroed[alpha==0]=0;variants.append(zeroed.tobytes())
                    for variant in set(variants):
                        key=(w,h,fmt,digest(variant));keys.append([w,h,fmt,f'{key[3]:016x}'])
                        matches.extend(f for f in fixtures if (f['w'],f['h'],f['hash'])==(w,h,key[3]) and f['fmt'] in (0,fmt))
                        effect|=key in effects
                same_name=any(f['name'].lower()==name.lower() for f in fixtures)
                status='REGISTERED FIXTURE' if matches else 'UNMATCHED FIXTURE VARIANT' if same_name else 'EFFECT CATALOG ONLY' if effect else 'NOT REGISTERED'
                rec=dict(width=w,height=h,pixel_sha256=identity[2],sources=[source],signals=notes,name_signal=name_signal,fixture_matches=sorted(set(f['name'] for f in matches)),fixture_types=sorted(set(f['kind'] for f in matches)),status=status,effect_catalog=effect,runtime_keys=keys,candidate=bool(notes or name_signal or matches or same_name or effect),decision='unreviewed')
                # High detail preview, preserving original colors. No light masks are authored here.
                im.thumbnail((512,512),Image.Resampling.LANCZOS)
                rec['image']=f'images/{len(records)+1:05d}.jpg';im.save(out/rec['image'],quality=92,subsampling=0)
                records[identity]=rec
        after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Bank changed during audit'
        pins.append(dict(bank=bank,path=str(path),size=before.st_size,mtime_ns=before.st_mtime_ns,sha256=SHA(path)))
    rows=list(records.values())
    rows.sort(key=lambda r:(not any('/t1/' in s['bank'] for s in r['sources']),not r['candidate'],r['sources'][0]['name'].lower(),r['pixel_sha256']))
    for i,r in enumerate(rows,1):
        r['id']=f'T{i:04d}';r['names']=sorted(set(s['name'] for s in r['sources']));r['banks']=sorted(set(s['bank'] for s in r['sources']))
        if r['status']=='NOT REGISTERED' and any(f['name'].lower()==name.lower() for f in fixtures for name in r['names']):
            r['status']='UNMATCHED FIXTURE VARIANT';r['candidate']=True
        if any(re.search(r'light|lite|lamp|glow|flare|beacon|runway|bay|hangar|control|panel|screen|window|reactor|\bled\b',name,re.I) for name in r['names']):
            r['name_signal']=True;r['candidate']=True
    data=dict(schema_version=1,scope='Active upgraded launcher texture banks; exact pixel variants deduplicated, all bank/name occurrences retained. Heuristic candidates require user review. No new lights enabled.',profile=str(profile),executable_sha256=SHA(exe),bank_map=str(active),bank_map_sha256=SHA(active),fixture_header_sha256=SHA(host/'fixture_lighting.hpp'),effect_catalog_sha256=hashlib.sha256(fx).hexdigest(),catalog_entries=len(fixtures),bank_pins=pins,total_bank_entries=total,unique_textures=len(rows),candidates=sum(r['candidate'] for r in rows),skipped=skipped,rows=rows)
    append_models(data,out,profile)
    (out/'audit.json').write_text(json.dumps(data,indent=2)+'\n')
    with (out/'review.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['ID','Texture names','Banks','Width','Height','Current coverage','Candidate reasons','Decision','Notes'])
        for r in rows:writer.writerow([r['id'],' / '.join(r['names']),' / '.join(r['banks']),r['width'],r['height'],r['status'],', '.join(r['signals']),r['decision'],''])
    # Inline metadata allows local file viewing with no fetch/server dependency.
    payload=json.dumps(rows).replace('</','<\\/')
    page='''<!doctype html><meta charset="utf-8"><title>MW3 texture light audit</title><style>body{background:#111820;color:#e3e9ef;font:16px system-ui;margin:24px}header{position:sticky;top:0;background:#111820;padding:12px;z-index:1}input,select,button{padding:8px;margin:4px;background:#25313e;color:white;border:1px solid #8292a1}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:16px}article{background:#202b36;padding:14px;border:1px solid #495b6e}img{width:100%;height:240px;object-fit:contain;background:#080c11}small{display:block;color:#b6c4d2;overflow-wrap:anywhere}.status{color:#ffd38a}h2{font-size:18px}a{color:#a6d6ff}</style><header><h1>MW3 texture light audit</h1><p>Upgraded active banks. Registration does not verify every bulb/UV island or guarantee a visible runtime light. No new lights enabled.</p><input id="q" placeholder="Search ID, name or bank"><select id="scope"><option value="candidates">Possible lights</option><option value="all">All textures</option><option value="training">Training textures</option><option value="registered">Registered fixtures</option><option value="unmatched">Unmatched variants</option></select><button onclick="save()">Export decisions</button><span id="count"></span></header><main id="grid"></main><script>const rows=PAYLOAD;const decisions=JSON.parse(localStorage.getItem('mw3-light-audit-v1')||'{}');function set(id,value){decisions[id]=value;localStorage.setItem('mw3-light-audit-v1',JSON.stringify(decisions));}function draw(){let text=q.value.toLowerCase();let filtered=rows.filter(r=>(scope.value==='all'||scope.value==='candidates'&&r.candidate||scope.value==='training'&&r.banks.some(b=>b.includes('/t1/'))||scope.value==='registered'&&r.status==='REGISTERED FIXTURE'||scope.value==='unmatched'&&r.status==='UNMATCHED FIXTURE VARIANT')&&[r.id,...r.names,...r.banks].join(' ').toLowerCase().includes(text));count.textContent=filtered.length+' textures';grid.replaceChildren();for(const r of filtered){let a=document.createElement('article');let h=document.createElement('h2');h.textContent=r.id+' · '+r.names.join(' / ');a.append(h);let link=document.createElement('a');link.href=r.image;link.target='_blank';let im=document.createElement('img');im.src=r.image;im.loading='lazy';link.append(im);a.append(link);let p=document.createElement('p');p.className='status';p.textContent=r.status+(r.fixture_types.length?' · '+r.fixture_types.join('/'):'');a.append(p);let small=document.createElement('small');small.textContent=r.width+'×'+r.height+' · '+r.banks.join(', ')+' · '+r.signals.join(', ');a.append(small);let s=document.createElement('select');for(const [v,l] of [['unreviewed','Needs your review'],['yes','Add / correct light'],['emission','Glow only'],['no','Not a light'],['keep','Keep current light']]){let o=document.createElement('option');o.value=v;o.textContent=l;s.append(o);}s.value=decisions[r.id]||'unreviewed';s.onchange=()=>set(r.id,s.value);a.append(s);grid.append(a);}}function save(){let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({schema_version:1,decisions},null,2)],{type:'application/json'}));a.download='light-decisions.json';a.click();}q.oninput=draw;scope.onchange=draw;draw();</script>'''.replace('PAYLOAD',payload)
    (out/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps({k:data[k] for k in ['total_bank_entries','unique_textures','candidates','catalog_entries']},indent=2));print('Skipped entries:',len(skipped))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,default=ROOT/'local/remaster/launcher.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--hash-library',type=Path,default=ROOT/'build/default/mw34_normal_hash.dll');a=p.parse_args();audit(a.profile,a.output,a.hash_library)
