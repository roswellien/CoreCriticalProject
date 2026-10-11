"""Assembly observers preserve incoming source stack/CPU/FX/ENV, then replay exact spans."""
def assembly():
    text='.686p\n.xmm\n.model flat,C\nassume fs:nothing\noption casemap:none\n'
    for name,type_ in [('mixed_host_esp','DWORD'),('format_head','DWORD'),('format_cpu','BYTE'),('format_fx','BYTE'),('format_env','BYTE'),('format_kind','DWORD'),('format_targets','DWORD'),('format_continues','DWORD'),('format_observe','PROC')]:text+='EXTERN '+name+':'+type_+'\n'
    text+='.code\n'
    rows=[('strrchr',0,0x780264a9,0x4dea1b,'83c4083bc3'),('malloc',1,0x780012b3,0x4deab7,'83c4043bc3'),('sprintf',2,0x78022b9a,0x4dead7,'83c4108b442420')]
    for name,index,entry,ret,raw in rows:
      for after in (0,1):
        fn='format_'+('return_' if after else 'entry_')+name
        text+='PUBLIC '+fn+'\n'+fn+' PROC\n'
        for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):text+=f' mov DWORD PTR format_cpu[{i*4}],{reg}\n'
        text+=f' mov DWORD PTR format_cpu[36],0{(ret if after else entry):x}h\n mov format_kind,{index*2+after}\n mov esp,mixed_host_esp\n pushfd\n pop DWORD PTR format_cpu[32]\n cld\n mov eax,DWORD PTR fs:[0]\n mov format_head,eax\n fxsave format_fx\n fnstenv format_env\n fldenv format_env\n call format_observe\n fxrstor format_fx\n fldenv format_env\n push DWORD PTR format_cpu[32]\n popfd\n'
        for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):
          if reg!='esp':text+=f' mov {reg},DWORD PTR format_cpu[{i*4}]\n'
        text+=' mov esp,DWORD PTR format_cpu[16]\n'
        if after:text+=' db '+','.join('0'+raw[j:j+2]+'h' for j in range(0,len(raw),2))+'\n'
        text+=f' jmp DWORD PTR '+('format_continues' if after else 'format_targets')+f'[{index*4}]\n'+fn+' ENDP\n'
    return text+'END\n'
