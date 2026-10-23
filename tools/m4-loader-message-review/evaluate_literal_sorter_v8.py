"""Invoke the materialized finite evaluator explicitly in its isolated namespace."""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter_v7.py');s=p.read_text();exec(compile(s,str(p),'exec'));ns['main']()
