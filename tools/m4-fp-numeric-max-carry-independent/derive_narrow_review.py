"""Mechanical root observer derivation for the unchanged narrow canonical corpus.

Changes only evidence namespaces/filenames. Carry-domain behavior and Boolean
guard controls are separate, and receive no credit from this narrow review.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
    assert out.parent==ROOT/'reports/m4-fp-numeric-max-carry' and not out.exists();out.mkdir();files={}
    def bind(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
    derivations=[]
    for name,wanted in (('persistent_model.py','86fa5de668633b1073415ebfc6cbbabc82557df4d677fe308ad5df13d1d364a8'),('replay_model.py','03f7f56f96988ad2e4109fdec9b86e888ea84ecd6059630b2e7489c40ff63b90')):
        source=bind(ROOT/'tools/m4-fp-numeric-max-host-boundary-independent'/name,wanted);text=source.read_text();(out/('ancestor-'+name)).write_bytes(source.read_bytes());bind(out/('ancestor-'+name))
        changed=text.replace("reports/m4-fp-numeric-max-host-boundary'","reports/m4-fp-numeric-max-carry'")
        if name=='persistent_model.py':changed=changed.replace("f'unit-{level}/persistent.bin'","f'legacy-unit-{level}/persistent.bin'")
        else:changed=changed.replace("f'replay-{mode}-{level}/replay.bin'","f'legacy-replay-{mode}-{level}/replay.bin'")
        target=ROOT/'tools/m4-fp-numeric-max-carry-independent'/name
        assert not target.exists();target.write_text(changed);bind(target)
        derivations.append(dict(ancestor=str(source),derivative=str(target),evidence_namespace_and_filename_only=True,guest_and_original_model_unchanged=True))
    bind(__file__);bind(sys.executable)
    report=dict(passed=True,scope='Mechanical root observer derivation for canonical narrow native/replay streams; no author fixture imports and no carry/guard admission',derivations=derivations,whole_M4_complete=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
