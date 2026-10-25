"""Local startup acceleration; pack admission and path checks still run each launch.

Unchanged-file receipts trust local filesystem metadata, not remote attestations.
This is not protection against a process that can modify the player's cache and
files. Missing receipts, changed identities, or changed producers cause rechecks.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import uuid
from contextlib import contextmanager


def fingerprint(path):
    path = Path(path)
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise ValueError('Links are not supported in startup cache inputs')
    s = path.stat()
    if not stat.S_ISREG(s.st_mode):
        raise ValueError('Startup input is not a regular file')
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def read_receipt(path):
    try:
        if path.is_symlink() or path.stat().st_size > 8 * 1024**2:
            return {}
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_receipt(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, separators=(',', ':')))
    os.replace(temp, path)


class VerificationCache:
    def __init__(self, directory, progress=None):
        self.path = Path(directory) / 'verified-pack-files-v1.json'
        self.entries = read_receipt(self.path)
        self.progress = progress or (lambda message: None)
        self.checked = 0
        self.reused = 0
        self.hashed = 0
        self.last_progress = 0

    def digest(self, path, expected):
        path = Path(path)
        before = fingerprint(path)
        key = str(path.resolve())
        previous = self.entries.get(key)
        if previous == [expected, before]:
            digest = expected
            self.reused += 1
        else:
            if time.monotonic() - self.last_progress > 0.5:
                self.progress('Checking changed content: ' + path.name)
                self.last_progress = time.monotonic()
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if fingerprint(path) != before:
                raise ValueError('Pack file changed while being checked: ' + path.name)
            if digest == expected:
                self.entries[key] = [digest, before]
            self.hashed += 1
        self.checked += 1
        if self.checked % 25 == 0:
            self.progress(f'Checked {self.checked} content files ({self.reused} unchanged).')
        return digest

    def save(self):
        write_receipt(self.path, self.entries)


@contextmanager
def cache_writer(cache_root):
    root = Path(cache_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / '.startup-cache-lock'
    if path.is_symlink():
        raise ValueError('Linked startup cache lock')
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('Another launcher is preparing content. Wait for it to finish.') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def environment_resources(selected, host, cache_root, progress=None):
    with cache_writer(cache_root):
        return _environment_resources(selected, host, cache_root, progress)


def _environment_resources(selected, host, cache_root, progress=None):
    """Reuse complete merged normal/lighting resources for an identical selection."""
    from prepared_environment_packs import prepare, profile_bindings, RESOURCE_KEYS
    progress = progress or (lambda message: None)
    # Include source implementation identities so reader/writer changes invalidate
    # the cache, even when no installed pack changes.
    source = Path(__file__).parent
    producers = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                 for name in ('startup_cache.py', 'prepared_environment_packs.py',
                              'normal_materials.py', 'mission_lighting.py')}
    # Only resource-generation inputs belong in this identity. The full host
    # includes fresh session/log paths and player controls on every launch.
    # Those bindings must remain current without rebuilding identical images.
    # Pack admission/capability checks run before this function. The EXE hash
    # identifies an admitted runtime, not generated resource bytes; a new host
    # using the same readers must not force all normal pages to be rebuilt.
    # Reader/writer changes still invalidate through the producer pins above.
    resource_host = dict(authored_normal_catalog_budget_bytes=host.get(
                             'authored_normal_catalog_budget_bytes', 536870912))
    identity = dict(selected=selected, host=resource_host, producers=producers)
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    directory = Path(cache_root) / 'environment-cache' / key
    receipt_path = directory / 'ready.json'
    receipt = read_receipt(receipt_path)
    try:
        if (receipt.get('identity') == key and receipt.get('complete') is True and
                isinstance(receipt.get('files'), dict) and isinstance(receipt.get('environment'), dict)):
            for name, pin in receipt['files'].items():
                # Only immediate, generated filenames are registered.
                if Path(name).name != name or '/' in name or '\\' in name:
                    raise ValueError('Invalid cached resource name')
                path = directory / name
                if fingerprint(path) != pin['stat']:
                    with path.open('rb') as stream:
                        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                    if digest != pin['sha256']:
                        raise ValueError('Cached resource changed')
                    pin['stat'] = fingerprint(path)
            write_receipt(receipt_path, receipt)
            progress('Reusing prepared textures, surface detail and mission lighting.')
            bindings = profile_bindings(selected, host)
            bindings.update({key: value for key, value in receipt['environment'].items()
                             if key in RESOURCE_KEYS})
            from presentation_policy import environment as presentation_environment
            return presentation_environment(host, selected, bindings)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    # Preserve incomplete/corrupt attempts, never publish a partial ready receipt.
    if directory.exists():
        directory.rename(directory.with_name(key + '-incomplete-' + uuid.uuid4().hex))
    progress('Preparing textures and lighting. First startup can take several minutes depending on your PC and storage speed.')
    environment = prepare(selected, host, directory)
    files = {}
    for path in directory.iterdir():
        if path.is_file():
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            files[path.name] = dict(sha256=digest, stat=fingerprint(path))
    # Empty selections can produce no files; still publish an explicit receipt.
    write_receipt(receipt_path, dict(identity=key, environment=environment, files=files, complete=True))
    return environment
