"""Exact delimiter-only repair; inherited physical lifecycle recipe retained."""
from pathlib import Path
p=Path(__file__).with_name('prepare_lifecycle_source.py');s=p.read_text();before="not present in bytes')},\n },provider_witnesses";after="not present in bytes'),\n },provider_witnesses";assert s.count(before)==1;s=s.replace(before,after);exec(compile(s,str(p),'exec'))
