"""Create only new private build recipes from the accepted mainargs recipes."""
import pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;OLD=ROOT/'tools/m4-crt-entry-mainargs'
for name in ('build.ps1','capture.s'):
 assert not(HERE/name).exists();shutil.copyfile(OLD/name,HERE/name)
(HERE/'native').mkdir();shutil.copyfile(OLD/'native/CMakeLists.txt',HERE/'native/CMakeLists.txt')
p=HERE/'build.ps1';s=p.read_text().replace("$cpBase=Join-Path $cpRoot 'reports/m4-crt-mainargs'","$cpBase=Join-Path $cpRoot 'reports/m4-crt-filename'").replace('reports/m4-crt-mainargs/$cpName','reports/m4-crt-filename/$cpName').replace("'preparation-r2'","'preparation-r1'").replace("'entry_mainargs.exe'","'entry_filename.exe'").replace('Source/build-only full bounded CRT entry plus actual mainargs/helper provider prefix; no worker executed','Source/build-only actual native filename bridge and literal continuation; no worker executed');p.write_text(s)
p=HERE/'native/CMakeLists.txt';s=p.read_text().replace('MW34EntryMainargs','MW34CRTFilename').replace('entry_mainargs','entry_filename');p.write_text(s)
