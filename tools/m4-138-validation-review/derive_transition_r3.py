from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-validation-review/diagnose_transition_r2.py'
t=p.read_text().replace('mfc-transition-r2','mfc-transition-r3')
a="if symbol['section']==section:"
z="if symbol['section']==section and symbol['name'].startswith(('_fs_hook_', '_nullfree_entry_hook', '_nullfree_ret_hook')):"
assert t.count(a)==1;t=t.replace(a,z)
q=p.with_name('diagnose_transition_r3.py');assert not q.exists();q.write_text(t)
