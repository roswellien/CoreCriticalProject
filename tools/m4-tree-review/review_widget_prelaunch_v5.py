"""One independent checker with exact physical finite page domain amendments."""
from pathlib import Path
import ast, hashlib
BASE=Path(__file__).with_name('review_widget_prelaunch.py')
BASE_SHA='4fc0ac68444b2fd77a471be5e7357695d9838eb4006a9976929326012492ca9c'
V2=BASE.with_name('review_widget_prelaunch_v2.py')
V2_SHA='875632f69885f756e3421f72f6ebc5ed30fe843537eff3d37fc418de88ab4637'
V3=BASE.with_name('review_widget_prelaunch_v3.py')
V3_SHA='c497a2152cb51c44a6727f2cc25212db798bfd3d3edcec466067c0a82222beda'
V4=BASE.with_name('review_widget_prelaunch_v4.py')

def literal(path, name):
    node=ast.parse(path.read_text())
    values=[ast.literal_eval(x.value) for x in node.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==name for y in x.targets)]
    if len(values)!=1:raise ValueError('Exactly one reviewed literal '+name)
    return values[0]

for path,digest in [(BASE,BASE_SHA),(V2,V2_SHA),(V3,V3_SHA)]:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Immutable checker source')
source=BASE.read_text()
before="'const std::array<NullHook,0>null_hooks{};'"
after="'const std::array<NullHook,0> null_hooks{};'"
if source.count(before)!=1:raise ValueError('One literal spacing amendment')
source=source.replace(before,after,1)
anchor="        eq(len(sparse_pages), 159, 'Exact current sparse page inventory')"
if source.count(anchor)!=1:raise ValueError('One page split proof seam')
source=source.replace(anchor,anchor+'\n'+literal(V2,'addition'),1)
for wrapper,old_key,new_key in [(V3,'old_parent','new_parent'),(V4,'old_pages','new_pages')]:
    transform=literal(wrapper,'transform')
    def value(name):
        node=ast.parse(transform)
        return next(ast.literal_eval(x.value) for x in node.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==name for y in x.targets))
    before=value(old_key);after=value(new_key)
    if source.count(before)!=1:raise ValueError('One bounded physical source/page amendment')
    source=source.replace(before,after,1)
anchor='        pin(__file__); pin(sys.executable)'
if source.count(anchor)!=1:raise ValueError('One complete independent code pin seam')
source=source.replace(anchor,'        pin(V4);\n'+anchor,1)
exec(compile(source,str(BASE),'exec'),globals())
