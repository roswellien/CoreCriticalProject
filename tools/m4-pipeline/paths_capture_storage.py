"""Original publication guards with one explicit local capture-storage root."""
import os
from pathlib import Path
import paths
ROOT=paths.ROOT
REPORTS=paths.REPORTS
STORAGE_ROOT=Path('G:/Projects/MW34Recomp-Captures')
logical_name=paths.logical_name
reject_reparse=paths.reject_reparse

def workspace_path(path, *, reports=False):
    path=Path(os.path.abspath(path))
    if path.is_relative_to(ROOT):return paths.workspace_path(path,reports=reports)
    base=STORAGE_ROOT/'reports'if reports else STORAGE_ROOT
    try:relative=path.relative_to(base)
    except ValueError:raise ValueError('Path must remain beneath a declared project reports root')from None
    if not relative.parts and reports:raise ValueError('A reports child path is required')
    cursor=Path(path.anchor)
    for part in path.parts[1:]:
        cursor/=part
        if cursor.exists()or cursor.is_symlink():reject_reparse(cursor)
    return path

def publish_new_file(temporary,output):
    temporary=workspace_path(temporary,reports=True);output=workspace_path(output,reports=True)
    if temporary.parent!=output.parent:raise ValueError('Publication requires a private sibling temporary file')
    if os.name=='nt':os.rename(temporary,output)
    else:os.link(temporary,output)

def publish_bytes(output,data):
    import uuid
    output=workspace_path(output,reports=True);output.parent.mkdir(parents=True,exist_ok=True);workspace_path(output.parent,reports=True)
    temporary=output.with_name('.'+output.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        publish_new_file(temporary,output)
    finally:temporary.unlink(missing_ok=True)
    return output
