from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'build_connected_fixture.py';text=parent.read_text()
text=text.replace("writer=pin(R/'reports/m4-capture-direct/build-r5/capture_direct.lib');", "writer_receipt=pin(R/'reports/m4-capture-direct/build-r4/build.json','909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96');wr=json.loads(writer_receipt.read_bytes());assert wr['passed'];[pin(q,h)for q,h in (wr['sources']|wr['objects']).items()];")
text=text.replace("tree=out/('build-'+level);flags=", "writer=pin(R/('reports/m4-capture-direct/build-r4/capture_direct-'+level+'.obj'));tree=out/('build-'+level);flags=")
text=text.replace("pin(__file__);pin(R/'tools/m4-mfc1168-native/build_connected_fixture.ps1');", "pin(__file__);pin(parent);pin(R/'tools/m4-mfc1168-native/build_connected_fixture.ps1');pin(R/'tools/m4-mfc1168-native/build_connected_fixture_v2.ps1');")
exec(compile(text,str(parent),'exec'),globals())
