"""Prepare a separate lighting-only study using unchanged local sprite references."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-comparison',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    source=args.reference_comparison.resolve();out=args.output.resolve()
    if out.exists():p.error('Choose a fresh lighting-study output')
    if not (source.parent/'weapon-effects-lab.marker').is_file():
        p.error('Reference must be an existing isolated local lab comparison')
    if source.stat().st_size>32*1024*1024:raise ValueError('Reference exceeds bounded input size')
    raw=source.read_bytes()
    match=re.search(r'const DATA=(.*?);\r?\nif\(!DATA\)',raw.decode('utf-8'),re.S)
    if not match:raise ValueError('Reference payload missing')
    references=json.loads(match.group(1))['references']
    for bank in ('stock','current'):
        if len(references[bank])!=31:raise ValueError('Unexpected reference image coverage')
    payload=json.dumps(dict(references=references),separators=(',',':')).replace('<','\\u003c')
    template=(HERE/'sprite_lighting.html').read_text(encoding='utf-8')
    if template.count('/*SPRITE_LIGHT_DATA*/null')!=1:raise ValueError('Ambiguous template marker')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(template.replace('/*SPRITE_LIGHT_DATA*/null',payload),encoding='utf-8')
    receipt=dict(reference=str(source),reference_sha256=hashlib.sha256(raw).hexdigest(),
        sprite_policy='Byte-identical embedded stock/current source PNGs; no particle replacements',
        lighting_scope='CPU diffuse point-light receiver fixture; not the game lighting engine',
        colors=dict(ppc=[.2,.1,1.],gauss=[.9,1.,.9],fire=[1.,.32,.06]),
        color_basis='PPC/Gauss original impact LightState definitions; fire authored warm light',
        timing='Authored review curves; native animation timing/branch execution unverified')
    out.with_suffix('.sources.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Lighting-only preview: {out}\nOriginal sprite pixels retained. No game/lighting-engine changes.')


if __name__=='__main__':main()
