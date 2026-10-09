"""Private, fresh report publication and Windows-safe logical capture paths."""
import os
import re
import stat
import unicodedata
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / 'reports'


def workspace_path(path, *, reports=False):
    path = Path(os.path.abspath(path))
    base = REPORTS if reports else ROOT
    try:
        relative = path.relative_to(base)
    except ValueError:
        raise ValueError('Path must remain beneath ' + str(base)) from None
    if not relative.parts:
        raise ValueError('A child path is required')
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        if cursor.exists() or cursor.is_symlink():
            reject_reparse(cursor)
    return path


def reject_reparse(path):
    info = Path(path).lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Reparse/symlink input or output is unsupported: ' + str(path))
    return info


def logical_name(name):
    if not isinstance(name, str) or not name or len(name) > 1024:
        raise ValueError('Invalid logical capture path')
    if unicodedata.normalize('NFC', name) != name:
        raise ValueError('Capture names must use NFC')
    if '\\' in name or any(unicodedata.category(c) in ('Cc', 'Cf', 'Cs') for c in name) or any(c in name for c in ':<>"|?*'):
        raise ValueError('Unsupported Windows capture path')
    for part in name.split('/'):
        stem = part.split('.')[0].upper()
        if (not part or part in ('.', '..') or part[-1] in '. '
                or stem in ('CON', 'PRN', 'AUX', 'NUL', 'CLOCK$')
                or re.fullmatch(r'(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]', stem)):
            raise ValueError('Unsupported Windows capture component')
    return name


def publish_bytes(output, data):
    output = workspace_path(output, reports=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    workspace_path(output.parent, reports=True)
    temporary = output.with_name('.' + output.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        publish_new_file(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def publish_new_file(temporary, output):
    temporary = workspace_path(temporary, reports=True)
    output = workspace_path(output, reports=True)
    if temporary.parent != output.parent:
        raise ValueError('Publication requires a private sibling temporary file')
    if os.name == 'nt':
        # Windows rename fails if the target exists; it does not replace it.
        os.rename(temporary, output)
    else:
        os.link(temporary, output)
