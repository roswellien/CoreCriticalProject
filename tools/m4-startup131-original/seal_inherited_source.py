"""Freeze aggregate adapter and exact physical130-to131 source continuity."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def need(value,label):
    if not value:raise ValueError(label)
def main(name):
    out=ROOT/'reports/m4-startup131-original'/name;need(not out.exists(),'Fresh source continuity preparation');out.mkdir(parents=True);pins={}
    def pin(path,digest=None):
        path=Path(path).resolve();need(path.suffix.lower()!='.mwb','No archive in continuity review');actual=sha(path);need(digest is None or actual==digest,'Exact physical input');pins[str(path)]=actual;return path
    def read(path,digest=None):return json.loads(pin(path,digest).read_bytes())
    previous=read(ROOT/'reports/m4-startup131-original/inherited-source-preparation-r1/report.json','d916ec8bb96161eb70cd7de9869185ff1c13cce9d614b9b7be1c39546619de2f')
    for path,digest in previous['files'].items():pin(path,digest)
    old_path=ROOT/'reports/m4-startup130-original/preparation-r2/report.json';old=read(old_path,'8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
    current_path=ROOT/'reports/m4-startup131-original/preparation-r4/report.json';current=read(current_path,'1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
    need(current['selected_order'][13]['entry']==0x5ae3e4 and current['selected_order'][:13]+current['selected_order'][14:]==old['selected_order'],'Exactly130 original root table/order pairs survive insertion')
    need(current['observed_pages']==old['observed_pages']and current['extra_whole_source_pages']==old['extra_whole_source_pages'],'Exact existing46 whole source-page inventory')
    identity=lambda row:(row['pc'],row['size'],row['image_offset'],row.get('origin',0))
    old_spans={identity(row)for row in old['source_spans']};new_spans={identity(row)for row in current['source_spans']}
    need(old_spans<=new_spans and len(new_spans-old_spans)==25,'All inherited physical3955 spans retained plus25 exact new MFC game rows')
    need(len(old_spans)==3955 and len(new_spans)==3980,'Complete physical source inventory')
    for filename in ['old4_source.py','format_source_v4.py','tree_source.py','current_inherited_source.py','export_reader.py','prepare_inherited_source.py']:
        pin(ROOT/'tools/m4-startup131-original'/filename)
    pin(__file__)
    report=dict(passed=True,scope='Current131 inherited130 physical source continuity and raw-export literal-comparison preparation only. All130 exact relative table entries,3955 physical spans and46 page inventory retained. Actual semantic fresh comparers are unexecuted until sealed exporter is available.',counts=dict(inherited_exact_source_spans=3955,new_MFC_game_spans=25,whole_source_spans=3980,inherited_root_table_pairs=130,current_root_table_pairs=131,ordinary_original_pages=43,additional_original_pages=3,current_original_semantic_phases=786),previous_preparation_sha256=sha(ROOT/'reports/m4-startup131-original/inherited-source-preparation-r1/report.json'),original_validation_sha256='9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f',files=pins,capture_reader_opened=False,source_comparison_executed=False,initializer_credit=0)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
