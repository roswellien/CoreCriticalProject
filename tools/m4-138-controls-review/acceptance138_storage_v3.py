"""acceptance138_storage_v2 plus an ordered-parallel Union.verify (v3).

Everything else is re-exported unchanged from v2. Union.verify keeps the base
per-file contract (stat, whole SHA-256, stat, exact equality and stability) and
the same final completeness checks; only the measurement may run in worker threads
through an optional ordered ``mapper`` (tools/m4-parallel-measure/ordered_pool).
UPDATEs, counters and progress stay in the calling thread, in path order.
"""
from pathlib import Path
import time
from acceptance138_storage_v2 import *  # noqa: F401,F403  (ScopedFiles, ScopeIndex, read_report, base, sha, load, ...)
from acceptance138_storage_v2 import sha
from acceptance138_storage import Union as BaseUnion

def _serial(work,rows,prepare=None):
    for row in rows:
        if prepare is not None:prepare(row)
        yield row,work(row)

def _measure(row):
    p,h=row;before=Path(p).stat();actual=sha(p);after=Path(p).stat()
    if actual!=h or (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):raise ValueError('Whole stable physical dependency '+p)
    return True

class Union(BaseUnion):
    mapper=None
    def verify(self,progress=None):
        self.db.commit();start=time.monotonic();count=0
        # Same live-cursor pattern as the base verify; the main thread alone touches SQLite.
        for(p,h),_ in(self.mapper or _serial)(_measure,self.items()):
            self.db.execute('UPDATE dependencies SET measured=1 WHERE path=?',(p,));count+=1
            if progress and count%5000==0:progress(count)
        self.db.commit();assert count==len(self) and self.db.execute('SELECT COUNT(*) FROM dependencies WHERE measured<>1').fetchone()[0]==0
        return dict(passed=True,unique_physical_dependencies=count,whole_dependency_rows_measured=count,verify_seconds=time.monotonic()-start,metadata_only_cache_used=False,parallel_mapper=self.mapper is not None)
