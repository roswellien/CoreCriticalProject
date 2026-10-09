"""Conflict-checked dependency union and full physical verification."""
import hashlib
import json
import ntpath
import time
from pathlib import Path


def normalized(path):
    if not isinstance(path, str) or not ntpath.isabs(path) or ntpath.splitdrive(path)[0].startswith('\\\\'):
        raise ValueError('An absolute local dependency path is required')
    drive, tail = ntpath.splitdrive(path)
    if len(drive) != 2 or drive[1] != ':' or ':' in tail or '\x00' in path:
        raise ValueError('Invalid local dependency path')
    return ntpath.normcase(ntpath.normpath(path))


def digest(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('Invalid dependency SHA256')
    return value


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON manifest key')
        value[key] = item
    return value


def merge_manifests(paths):
    merged = {}
    for path in paths:
        value = json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
        if set(value) != {'files'} or not isinstance(value['files'], dict):
            raise ValueError('Expected an exact files manifest')
        for name, value in value['files'].items():
            key = normalized(name)
            value = digest(value)
            if key in merged and merged[key] != value:
                raise ValueError('Conflicting dependency digest: ' + key)
            merged[key] = value
    if not merged:
        raise ValueError('A nonempty manifest union is required')
    return dict(sorted(merged.items()))


def verify_manifest(files):
    started = time.perf_counter_ns()
    normalized_files = {}
    for path, expected in files.items():
        key = normalized(path)
        expected = digest(expected)
        if key in normalized_files and normalized_files[key] != expected:
            raise ValueError('Conflicting dependency digest: ' + key)
        normalized_files[key] = expected
    if not normalized_files:
        raise ValueError('A nonempty dependency set is required')
    for path, expected in normalized_files.items():
        with Path(path).open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError('Physical dependency SHA256 mismatch: ' + path)
    return dict(passed=True, unique_physical_dependencies=len(normalized_files),
        verify_seconds=(time.perf_counter_ns() - started) / 1e9,
        metadata_only_cache_used=False, process_file_open_attestation=False)
