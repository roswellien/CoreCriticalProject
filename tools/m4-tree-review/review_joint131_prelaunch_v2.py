"""Bind exact initialized TLS cell of the retained direct phase observer."""
from pathlib import Path
parent=Path(__file__).with_name('review_joint131_prelaunch.py')
source=parent.read_text()
anchor="exec(compile(text,str(__file__),'exec'),globals())"
assert source.count(anchor)==1
source=source.replace(anchor, "text=text.replace(\"TLS_names={\",\"TLS_names={'?current@DirectPhaseWriter@@2PEAU1@EA',\");text=text.replace(\"  pin(BASE);pin(V2);pin(V3);pin(V4);\",\"  pin(R/'tools/m4-tree-review/review_joint131_prelaunch.py');pin(BASE);pin(V2);pin(V3);pin(V4);\");"+anchor)
exec(compile(source,str(parent),'exec'),globals())
