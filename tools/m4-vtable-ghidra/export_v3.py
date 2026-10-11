"""Additive export with one explicit literal-source function annotation, never saved."""
from pathlib import Path
base=Path(__file__).with_name('export_v2.py')
text=base.read_text()
anchor="script.write_text(template.read_text().replace('MW34ContainerExport','MW34VtableExport'));pin(script)"
assert text.count(anchor)==1
replacement='''
        java=template.read_text().replace('MW34ContainerExport','MW34VtableExport')
        anchor='Function f = currentProgram.getFunctionManager().getFunctionAt(a);'
        assert java.count(anchor)==1
        java=java.replace(anchor,anchor+"\\n        boolean created=false;\\n        if(f==null && entry==0x59ff80L) {\\n            disassemble(a);\\n            f=createFunction(a,\\\"MW34_literal_59FF80\\\");\\n            if(f!=null) {f.setBody(new AddressSet(a,address(0x59ffa3L)));created=true;}\\n        }")
        anchor='return map("entry",entry,"present",true,"name",f.getName()'
        assert java.count(anchor)==1
        java=java.replace(anchor,'return map("entry",entry,"present",true,"created_from_literal_entry",created,"annotation_saved",false,"name",f.getName()')
        script.write_text(java);pin(script)
'''
text=text.replace(anchor,replacement.strip('\n'))
text=text.replace("scope='Warm exact-SHA retained Ghidra project function/pseudocode corroboration; literal source rows remain primary and decompiler omissions do not narrow source'", "scope='Warm exact-SHA retained Ghidra export with unsaved explicit source entry/body annotation for missing59FF80 only; all15 decompilers remain corroborative and literal596B rows primary'")
text=text.replace("pin(target,h);pin(__file__);pin(ROOT/'tools/analysis/pe.py')", "pin(target,h);pin(__file__);pin(base);pin(ROOT/'tools/analysis/pe.py')")
exec(compile(text,str(Path(__file__)), 'exec'),globals())
