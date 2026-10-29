"""Prepare a local source-animation/particle comparison; never launch/edit the game."""
from pathlib import Path
import argparse,base64,hashlib,json,struct,sys

from page_data import append_page_script, fill_page_data

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/asset-inventory'))
import decode_images


def images(path,names):
    result={}
    before=path.stat()
    with path.open('rb') as f:
        header=f.read(24)
        count=struct.unpack('<6I',header)[3]
        if not 0<count<=65536:raise ValueError('Invalid image-table count')
        toc=f.read(count*40)
        if len(toc)!=count*40:raise ValueError('Truncated image table')
        found={}
        for i in range(count):
            raw,offset,marker=struct.unpack_from('<32sII',toc,i*40)
            end=struct.unpack_from('<I',toc,(i+1)*40+32)[0] if i+1<count else before.st_size
            name=raw.split(b'\0')[0].decode('ascii')
            if name.lower() in names:
                if not 24+count*40<=offset<end<=before.st_size or end-offset>4*1024*1024:
                    raise ValueError('Selected image span outside bounds')
                found[name.lower()]=(offset,end-offset,marker)
        for name in names:
            offset,size,marker=found[name]
            f.seek(offset);raw=f.read(size);blob=bytearray(raw)
            flags=struct.unpack_from('<I',blob)[0]
            if flags==43:struct.pack_into('<I',blob,0,11)
            info,rgba=decode_images.decode(blob,dict(offset=0,span_bytes=size,table_marker=marker))
            png=decode_images.png_bytes(info['width'],info['height'],rgba)
            result[name]=dict(uri='data:image/png;base64,'+base64.b64encode(png).decode('ascii'),
                width=info['width'],height=info['height'],offset=offset,flags=flags,
                entry_sha256=hashlib.sha256(raw).hexdigest())
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('Source bank changed during comparison preparation')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--particle-preview',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    preview=args.particle_preview.resolve();out=args.output.resolve()
    if not (preview.parent/'weapon-effects-lab.marker').is_file():
        p.error('Use a built isolated effects-lab preview')
    if out.exists():p.error('Choose a fresh comparison output file')
    if out.parent!=preview.parent:p.error('Keep the comparison beside its isolated lab preview')
    names=['gausmuz','gaustrail','ppcmuz','ppc_trail','green_exp01','blue_starburst','spark_part5']
    names += [f'plsbrn{i:02d}' for i in range(1,9)]+[f'fire_f{i:02d}' for i in range(1,17)]
    stock=ROOT/'MW3/zbd/c1/rtexture.zbd'
    if hashlib.sha256(stock.read_bytes()).hexdigest()!='56afd5738562ffd51596ce4b3557b734cacedfd187b09307e9b94281dd39269f':
        raise ValueError('Stock texture identity changed')
    rows=json.loads((ROOT/'local/work-ahead/texture-launcher-audit-v2/configured-banks.json').read_text(encoding='utf-8-sig'))
    row=next(r for r in rows if r['target'].replace('\\','/').lower().endswith('/c1/rtexture.zbd'))
    data=dict(stock=images(stock,names),current=images(Path(row['source']),names))
    native=preview.read_text(encoding='utf-8')
    bridge="""
window.addEventListener('message',event=>{
 if(event.source!==parent||event.data?.type!=='mw34-comparison')return;
 const d=event.data;if(!Number.isInteger(d.scene)||d.scene<0||d.scene>2||!Number.isFinite(d.time)||d.time<0||d.time>4)return;
 scene=d.scene;t=d.time;playing=false;playLabel();draw();
});
"""
    native=append_page_script(native,bridge)
    native=native.replace('<main>', '<style>main{padding:0;max-width:none}header,aside,.transport,.detail,.stamp{display:none}.layout{display:block;border:0}.stage{height:500px}canvas{height:500px!important}</style><main>',1)
    template=(HERE/'comparison.html').read_text(encoding='utf-8')
    out.write_text(fill_page_data(template,dict(references=data,native=native)),encoding='utf-8')
    receipt=dict(stock_path=str(stock),current_path=row['source'],current_manifest_sha256=row['expected_sha256'],
        current_whole_bank_hash_recomputed=False,particle_preview=str(preview),particle_sha256=hashlib.sha256(preview.read_bytes()).hexdigest(),
        method='Bounded texture-entry decoding and offline illustrative composition; not native playback',
        images={bank:{name:{k:v for k,v in image.items() if k!='uri'} for name,image in values.items()} for bank,values in data.items()})
    out.with_suffix('.sources.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Comparison: {out}\n31 textures per bank, stock/current switch; source reconstruction, not gameplay capture.')


if __name__=='__main__':main()
