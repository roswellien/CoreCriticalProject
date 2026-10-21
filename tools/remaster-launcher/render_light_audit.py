"""Render a completed local texture audit into private review artifacts."""
from pathlib import Path
import argparse, base64, collections, io, json, math, re, textwrap, zipfile
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader

def render(folder):
    data=json.loads((folder/'audit.json').read_text());rows=data['rows']
    focus=lambda r:r['id'].startswith('M') or r['fixture_matches'] or r['status']=='UNMATCHED FIXTURE VARIANT' or any(re.search(r'light|lite(?!ning)|lamp|beacon|glow|runway|window|screen|panel|reactor|hangar|mechbay|strt',n,re.I) for n in r['names']) or any(n.lower() in ['tredtruck07','missle_turret06','cpit05','cpit06','madcat_cpit03'] for n in r['names'])
    # Put the user's Training atlas examples first, without claiming a mesh/UV trace.
    primary=sorted([r for r in rows if focus(r)],key=lambda r:(not any(n.lower() in ['c5strt18','c5strt23'] for n in r['names']),not any('/t1/' in b for b in r['banks']),r['id']))
    broad=[r for r in rows if r['candidate']]
    pdfdir=folder/'output/pdf';pdfdir.mkdir(parents=True,exist_ok=True)
    def pdf(name,selected,cols,lines,title):
        path=pdfdir/name;c=canvas.Canvas(str(path),pagesize=(842,1191),pageCompression=1)
        c.setTitle(title);cellw=790/cols;cellh=1040/lines;per=cols*lines
        for page,start in enumerate(range(0,len(selected),per),1):
            c.setFillColorRGB(.05,.09,.14);c.rect(0,0,842,1191,fill=1,stroke=0)
            c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',17);c.drawString(26,1158,title)
            c.setFont('Helvetica',9);c.drawString(26,1138,f'{len(selected)} exact pixel variants | page {page}/{math.ceil(len(selected)/per)} | IDs refer to review.csv / gallery')
            c.drawString(26,1123,'Registered = catalog match, not verified UV placement. Unmatched = known name, no matching pixels.')
            c.drawString(26,1108,'Not registered = no fixture match. Effect only = weapon/effect catalog; not a permanent fixture.')
            for i,r in enumerate(selected[start:start+per]):
                x=26+(i%cols)*cellw;y=1086-(i//cols)*cellh
                c.setFillColorRGB(.12,.17,.22);c.rect(x,y-cellh+8,cellw-8,cellh-6,fill=1,stroke=0)
                c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',10 if cols==2 else 8)
                label=r['id']+'  '+' / '.join(r['names']);label=label[:68] if cols==2 else label[:40]
                c.drawString(x+8,y-16,label)
                image=Image.open(folder/r['image']).convert('RGB');image.thumbnail((360,250) if cols==2 else (180,130))
                stream=io.BytesIO();image.save(stream,format='JPEG',quality=83 if cols==2 else 65)
                iw,ih=cellw-24,cellh-91
                c.drawImage(ImageReader(stream),x+8,y-25-ih,width=iw,height=ih,preserveAspectRatio=True,anchor='c')
                color=(.55,.95,.7) if r['status']=='REGISTERED FIXTURE' else (1,.73,.35)
                c.setFillColorRGB(*color);c.setFont('Helvetica-Bold',8 if cols==2 else 6.8);c.drawString(x+8,y-cellh+57,r['status'])
                c.setFillColorRGB(.82,.87,.92);c.setFont('Helvetica',8 if cols==2 else 6.5)
                c.drawString(x+8,y-cellh+43,f"{r['width']}x{r['height']} | "+', '.join(r['banks'])[:(80 if cols==2 else 42)])
                c.drawString(x+8,y-cellh+29,' / '.join(r['signals'])[:(78 if cols==2 else 42)])
                c.drawString(x+8,y-cellh+15,'Decision: add/correct light / glow only / not a light / keep')
            c.setFillColorRGB(.8,.85,.9);c.setFont('Helvetica',8);c.drawString(26,20,'MW3 private upgraded texture audit - 2026-10-20 - No new lights enabled; false positives require review.')
            c.showPage()
        c.save();reader=PdfReader(path);assert len(reader.pages)==math.ceil(len(selected)/per)
        assert selected[0]['id'] in reader.pages[0].extract_text()
        return dict(file=str(path),textures=len(selected),pages=len(reader.pages))
    outputs=[pdf('01-focused-light-review.pdf',primary,2,3,'MW3 - Focused light candidates and existing fixtures'),pdf('02-broad-candidate-review.pdf',broad,4,6,'MW3 - Broad candidate review (includes false positives)')]
    # A single offline HTML file avoids a separate image folder or web server.
    # High-detail originals remain in the local gallery and focused PDF.
    html=(folder/'index.html').read_text();compact=[]
    for r in rows:
        item={k:r[k] for k in ['id','names','banks','width','height','signals','fixture_types','status','candidate']}
        im=Image.open(folder/r['image']);im.thumbnail((256,256));stream=io.BytesIO();im.save(stream,format='JPEG',quality=72)
        item['image']='data:image/jpeg;base64,'+base64.b64encode(stream.getvalue()).decode();compact.append(item)
    start=html.index('const rows=')+len('const rows=');end=html.index(';const decisions=',start)
    html=html[:start]+json.dumps(compact).replace('</','<\\/')+html[end:]
    html=html.replace('mw3-light-audit-v1','mw3-light-audit-20261020-r2')
    html=html.replace("link.href=r.image;link.target='_blank';", "link.href='#';link.onclick=(ev)=>{ev.preventDefault();let d=document.createElement('dialog');d.style.cssText='width:90vw;max-width:1024px;background:#111820;color:white;border:1px solid #8292a1';let label=document.createElement('p');label.textContent=r.id+' '+r.names.join(' / ')+' - click to close';d.append(label);let large=document.createElement('img');large.src=r.image;large.style.height='80vh';d.append(large);d.onclick=()=>{d.close();d.remove();};document.body.append(d);d.showModal();};")
    html=html.replace('<option value="candidates">','<option value="focused">Focused lights</option><option value="candidates">')
    focused_ids=[r['id'] for r in primary]
    html=html.replace("scope.value==='all'||", "scope.value==='focused'&&"+json.dumps(focused_ids)+".includes(r.id)||scope.value==='all'||")
    html=html.replace('function save(){','function save(){')
    (folder/'all-textures-review.html').write_text(html,encoding='utf-8')
    note=f'''MW3 LIGHT TEXTURE REVIEW - 2026-10-20

Start with 01-focused-light-review.pdf ({len(primary)} texture variants).
The opening C5STRT18/C5STRT23 pages show the red indicators on Training wall
atlases. They are not registered. Their appearance is consistent with the bay
panels reported by the user; exact live polygon/UV placement has not been traced.

REGISTERED FIXTURE: exact runtime texture pixels match the permanent fixture
catalog. This does not verify every intended bulb/UV island or visible result.
UNMATCHED FIXTURE VARIANT: the name is known, but this pixel variant does not
match. EFFECT CATALOG ONLY: covered as weapon/effect light, not permanent fixture.
NOT REGISTERED: no permanent fixture catalog match.

02-broad-candidate-review.pdf includes {len(broad)} heuristic candidates. Painted
markings, reflections, skies, effects and non-light textures are intentional
review false positives. This is not a count of missed physical lamps.

Open all-textures-review.html after downloading/extracting the ZIP. It contains
all {len(rows)} decoded exact-pixel texture variants, searchable by ID/name/bank.
Use the selectors to view focused candidates, broad candidates or all textures.
Choose Add/correct light, Glow only, Not a light or Keep current light, then click
Export decisions. Choices are stored in that browser until exported. Return the
JSON or tell the agent IDs and decisions. review.csv provides the same IDs.

No texture artwork, fixture registration, light budget or runtime lighting was
changed by this audit. The current selected build SHA-256 is
{data['executable_sha256']}.
Replacement-model atlases are included as M IDs. These bypass the source-world
fixture observer and have no fixture registration; their inclusion does not mean
all bright paint or reflective windows should become light sources. Model PNGs
are previews of the registered upgraded sources; bank previews use stored rows.
'''
    (folder/'README.txt').write_text(note)
    archive=folder.parent/'texture-light-review.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for name in ['all-textures-review.html','review.csv','README.txt']:z.write(folder/name,name)
    result=dict(outputs=outputs,all_decoded=len(rows),focused=len(primary),broad=len(broad),zip=str(archive),zip_bytes=archive.stat().st_size,status_counts=dict(collections.Counter(r['status'] for r in rows)))
    (folder/'review-artifacts.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);render(p.parse_args().folder)
