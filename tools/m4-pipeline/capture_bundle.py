"""Deterministic, pinned, non-extracting capture bundles. No execution credit."""
import argparse
import ctypes
import hashlib
import json
import mmap
import os
import stat
import struct
import time
import uuid
from pathlib import Path
from paths import logical_name, publish_new_file, reject_reparse, workspace_path

MAGIC = b'MW34CAP1'
HEADER = struct.Struct('<8sQ32s')
MAX_FILES = 200_000
MAX_INDEX = 64 * 1024 * 1024
MAX_FILE = 256 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
FORMAT = 'mw34.capture.v1'


def sha_file(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _digest(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('A lowercase SHA256 digest is required')
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def _scan(source):
    files = []
    keys = set()
    for current, directories, filenames in os.walk(source, followlinks=False):
        for name in directories + filenames:
            info = reject_reparse(Path(current) / name)
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError('Only regular capture files/directories are supported')
        for name in filenames:
            path = Path(current) / name
            name = logical_name(path.relative_to(source).as_posix())
            if name.casefold() in keys:
                raise ValueError('Duplicate normalized capture name')
            keys.add(name.casefold())
            size = path.stat().st_size
            if size > MAX_FILE:
                raise ValueError('Capture file exceeds size limit')
            files.append((name, path, size))
            if len(files) > MAX_FILES:
                raise ValueError('Capture count exceeds limit')
    if not files:
        raise ValueError('Capture tree must contain files')
    return sorted(files)


def pack_capture(source_dir, output_file):
    source = workspace_path(source_dir)
    output = workspace_path(output_file, reports=True)
    if not source.is_dir():
        raise ValueError('A capture directory is required')
    if output.is_relative_to(source):
        raise ValueError('Bundle output cannot be inside its source tree')
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    workspace_path(output.parent, reports=True)
    started = time.perf_counter_ns()
    files = _scan(source)
    entries = []
    offset = 0
    for name, path, size in files:
        digest = sha_file(path)
        entries.append(dict(path=name, offset=offset, size=size, sha256=digest))
        offset += size
        if offset > MAX_TOTAL:
            raise ValueError('Capture payload exceeds limit')
    index = _json(dict(format=FORMAT, files=entries, total_bytes=offset))
    if len(index) > MAX_INDEX:
        raise ValueError('Capture index exceeds limit')
    temporary = output.with_name('.' + output.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(HEADER.pack(MAGIC, len(index), hashlib.sha256(index).digest()))
            stream.write(index)
            for entry, (_, path, size) in zip(entries, files):
                digest = hashlib.sha256()
                written = 0
                reject_reparse(path)
                with path.open('rb') as original:
                    while block := original.read(1024 * 1024):
                        written += len(block)
                        if written > size:
                            raise ValueError('Capture changed during packing')
                        stream.write(block)
                        digest.update(block)
                if written != size or digest.hexdigest() != entry['sha256']:
                    raise ValueError('Capture changed during packing')
            if _scan(source) != files:
                raise ValueError('Capture inventory changed during packing')
            for entry, (_, path, _) in zip(entries, files):
                if sha_file(path) != entry['sha256']:
                    raise ValueError('Capture bytes changed before publication')
            stream.flush()
            os.fsync(stream.fileno())
        digest = sha_file(temporary)
        with CaptureBundle(temporary, digest) as bundle:
            if bundle.names() != tuple(entry['path'] for entry in entries):
                raise ValueError('Bundle roundtrip inventory mismatch')
        publish_new_file(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return dict(passed=True, format=FORMAT, bundle_path=str(output), sha256=digest,
        logical_files=len(entries), payload_bytes=offset, bundle_bytes=output.stat().st_size,
        pack_seconds=(time.perf_counter_ns() - started) / 1e9,
        source_directory=str(source), source_files_modified=False,
        sources_match_at_final_verification=True, concurrent_source_writers_supported=False,
        authenticity='External bundle SHA pin plus whole index/entry integrity; no semantic/native execution credit')


def _locked_stream(path):
    if os.name != 'nt':
        return path.open('rb')
    import msvcrt
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    api.CreateFileW.restype = ctypes.c_void_p
    handle = api.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except Exception:
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        api.CloseHandle(handle)
        raise
    return os.fdopen(descriptor, 'rb')


class CaptureBundle:
    def __init__(self, path, expected_sha256):
        self.path = workspace_path(path, reports=True)
        self._stream = None
        self._map = None
        self._entries = {}
        _digest(expected_sha256)
        try:
            info = reject_reparse(self.path)
            if not stat.S_ISREG(info.st_mode) or not HEADER.size <= info.st_size <= HEADER.size + MAX_INDEX + MAX_TOTAL:
                raise ValueError('Invalid capture bundle size/type')
            self._stream = _locked_stream(self.path)
            opened_info = os.fstat(self._stream.fileno())
            if not stat.S_ISREG(opened_info.st_mode) or not HEADER.size <= opened_info.st_size <= HEADER.size + MAX_INDEX + MAX_TOTAL:
                raise ValueError('Invalid opened capture bundle size/type')
            self._map = mmap.mmap(self._stream.fileno(), 0, access=mmap.ACCESS_READ)
            if hashlib.sha256(self._map).hexdigest() != expected_sha256:
                raise ValueError('External capture bundle SHA256 mismatch')
            magic, index_size, index_sha = HEADER.unpack(self._map[:HEADER.size])
            if magic != MAGIC or not 1 <= index_size <= MAX_INDEX or HEADER.size + index_size > len(self._map):
                raise ValueError('Invalid capture bundle header')
            raw_index = self._map[HEADER.size:HEADER.size + index_size]
            if hashlib.sha256(raw_index).digest() != index_sha:
                raise ValueError('Capture index hash mismatch')
            index = json.loads(raw_index.decode('utf-8'))
            if _json(index) != raw_index or set(index) != {'format', 'files', 'total_bytes'} or index['format'] != FORMAT:
                raise ValueError('Noncanonical capture index')
            if type(index['total_bytes']) is not int or not 0 <= index['total_bytes'] <= MAX_TOTAL:
                raise ValueError('Invalid total capture payload')
            entries = index['files']
            if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_FILES:
                raise ValueError('Invalid capture file count')
            self._payload = HEADER.size + index_size
            offset = 0
            names = []
            keys = set()
            for entry in entries:
                if not isinstance(entry, dict) or set(entry) != {'path', 'offset', 'size', 'sha256'}:
                    raise ValueError('Invalid capture entry')
                name = logical_name(entry['path'])
                if name.casefold() in keys:
                    raise ValueError('Duplicate normalized capture name')
                keys.add(name.casefold())
                if type(entry['offset']) is not int or type(entry['size']) is not int or entry['offset'] != offset or not 0 <= entry['size'] <= MAX_FILE:
                    raise ValueError('Noncontiguous/invalid capture entry extent')
                digest = _digest(entry['sha256'])
                offset += entry['size']
                if offset > MAX_TOTAL or self._payload + offset > len(self._map):
                    raise ValueError('Capture entry exceeds payload')
                self._entries[name] = (self._payload + entry['offset'], entry['size'], digest)
                names.append(name)
            if names != sorted(names) or offset != index['total_bytes'] or self._payload + offset != len(self._map):
                raise ValueError('Capture order/length mismatch or trailing bytes')
            for name in names:
                self.read_bytes(name)
        except Exception:
            self.close()
            raise

    def names(self):
        self._require_open()
        return tuple(self._entries)

    def exists(self, name):
        self._require_open()
        return logical_name(name) in self._entries

    def read_bytes(self, name):
        self._require_open()
        start, size, digest = self._entries[logical_name(name)]
        data = self._map[start:start + size]
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Capture entry bytes changed or hash mismatch')
        return data

    def _require_open(self):
        if self._map is None:
            raise ValueError('Capture bundle is closed')

    def close(self):
        if self._map is not None:
            self._map.close()
            self._map = None
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    pack = sub.add_parser('pack')
    pack.add_argument('source')
    pack.add_argument('output')
    check = sub.add_parser('verify')
    check.add_argument('bundle')
    check.add_argument('--sha256', required=True)
    args = parser.parse_args()
    if args.action == 'pack':
        result = pack_capture(args.source, args.output)
    else:
        start = time.perf_counter_ns()
        with CaptureBundle(args.bundle, args.sha256) as bundle:
            result = dict(passed=True, logical_files=len(bundle.names()),
                verify_seconds=(time.perf_counter_ns() - start) / 1e9)
    print(json.dumps(result, indent=2))
