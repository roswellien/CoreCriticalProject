"""Ordered bounded thread pool for whole-file measurement loops.

Workers only run the caller's unchanged per-file measurement (stat, full SHA-256,
stat, compare). Everything order- or state-sensitive (SQLite reads/writes, union
registration, counters, progress, pre-open metadata checks) stays in the calling
thread, which consumes results strictly in input order.

Failure order equals the serial loop: an optional ``prepare(item)`` runs in the
calling thread before an item is submitted (so files that must never be opened are
refused first); if it raises, every earlier pending measurement is consumed in
order first, so an earlier measurement failure still wins. Later in-flight work is
discarded; it has no effect beyond reading files.

Measured 2026-10-12 on the composite inventory (average ~4 KB files): serial about
1,000 files/s, 8 threads about 4,800 files/s; processes did not do better, so the
ceiling is per-file filesystem cost rather than the GIL or SHA-256 compute.
"""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import os

DEFAULT_WORKERS=int(os.environ.get('MW34_MEASURE_WORKERS','8'))

def ordered_map(fn,items,workers=None,window=4096,prepare=None):
    """Yield (item, fn(item)) in input order using a bounded in-flight window."""
    workers=DEFAULT_WORKERS if workers is None else workers
    if workers<=1:
        for item in items:
            if prepare is not None:prepare(item)
            yield item,fn(item)
        return
    pending=deque()
    with ThreadPoolExecutor(max_workers=workers,thread_name_prefix='mw34-measure')as pool:
        try:
            for item in items:
                if prepare is not None:
                    try:prepare(item)
                    except BaseException:
                        while pending:
                            head,future=pending.popleft();yield head,future.result()
                        raise
                pending.append((item,pool.submit(fn,item)))
                if len(pending)>=window:
                    head,future=pending.popleft();yield head,future.result()
            while pending:
                head,future=pending.popleft();yield head,future.result()
        finally:
            for _,future in pending:future.cancel()
