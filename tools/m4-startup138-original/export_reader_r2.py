"""Read sealed raw equality targets exported by the sole source reader.

This is deliberately a loose contiguous byte transport, not a model or a
capture producer. Source consumers must independently declare which genuine
BEFORE bytes are inputs and which AFTER bytes are equality targets.
"""
from pathlib import Path
import hashlib, json

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

class ExportReader:
    def __init__(self, report_path, report_sha256, branch, pin):
        self.report_path = Path(report_path).resolve()
        need(self.report_path.suffix.lower() != '.mwb', 'Export report is not a capture archive')
        report = json.loads(pin(self.report_path, report_sha256).read_bytes())
        need(report['passed'] and (report.get('paired_export_readers_closed') or report.get('reader_closed')), 'Producer source/export reader is sealed and closed')
        matches = [row for row in report['paired_exports'] if row['branch'] == branch]
        need(len(matches) == 1, 'One exact current branch export')
        row = matches[0]
        self.path = Path(row['transport_path']).resolve()
        self.transport_sha256 = row['transport_sha256']
        self.branch = branch
        self.index_path = Path(row['index_path']).resolve()
        self.payload_path = Path(row['payload_path']).resolve()
        need(self.index_path.suffix.lower() != '.mwb' and self.payload_path.suffix.lower() != '.mwb', 'No archive opened by the raw export adapter')
        for path, field in [(self.index_path, 'index_sha256'), (self.payload_path, 'payload_sha256')]:
            need(report['files'][str(path)] == row[field], 'Actual producer files map binds raw transport')
            pin(path, row[field])
        index = json.loads(self.index_path.read_bytes())
        need(index['version'] == 1 and index['logical_files'] == len(index['entries']), 'Complete declared logical extent index')
        need(index['payload_bytes'] == self.payload_path.stat().st_size, 'No truncated or trailing payload bytes')
        self.entries = index['entries']
        cursor = 0
        # Empty logical files are genuine observations too. Place them before
        # nonempty files sharing the same offset for strict gap-free geometry.
        for name, item in sorted(self.entries.items(), key=lambda pair: (pair[1]['offset'], bool(pair[1]['bytes']), pair[0])):
            need(isinstance(name, str) and name and not name.startswith('/') and '..' not in name.split('/'), 'Finite logical source transport key')
            need(type(item['offset']) is int and type(item['bytes']) is int and item['offset'] == cursor and item['bytes'] >= 0, 'Every extent exactly contiguous without overlaps/gaps')
            need(len(item['sha256']) == 64, 'Complete individual equality-target identity')
            cursor += item['bytes']
        need(cursor == index['payload_bytes'], 'Every payload byte belongs to an indexed raw target')
        self.payload_sha256 = row['payload_sha256']
        self.stream = self.payload_path.open('rb')
        self.bundles = {}
        self.reads = {}
        self.closed = False

    def data(self, logical):
        need(not self.closed and logical in self.entries, 'Exact existing raw equality target ' + logical)
        item = self.entries[logical]
        self.stream.seek(item['offset'])
        raw = self.stream.read(item['bytes'])
        need(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], 'Whole individual copied target identity ' + logical)
        self.reads[logical] = dict(item)
        return raw

    def close(self):
        if self.closed:
            return
        self.stream.close()
        self.closed = True
        need(digest(self.payload_path) == self.payload_sha256, 'Whole immutable raw export after all equality reads')
