"""Correct the exact existing status declaration; no worker execution."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;prior=P/'derive_fixture_v9.py';s=prior.read_text()
old="old='status{1,1,6,51,0,0,0,0}';new='status{1,1,6,52,0,0,0,0}'"
new="old='status{1,unsigned(!failed),6,51,unsigned(r.poisoned()),0,0,0}';new='status{1,unsigned(!failed),6,52,unsigned(r.poisoned()),0,0,0}'"
assert s.count(old)==1
exec(compile(s.replace(old,new),str(prior),'exec'),globals())
