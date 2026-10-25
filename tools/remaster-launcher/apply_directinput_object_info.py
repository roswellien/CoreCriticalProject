"""Marshal the pointer-free ANSI DirectInput object query across the guest ABI."""
import argparse
from pathlib import Path

HANDLER = '''    if(n=="GetObjectInfo") {
     const unsigned out=arg(1);
     if(!readable(out,4))deny("GetObjectInfo size outside the memory contract",out);
     const unsigned size=load(out);
     static_assert(sizeof(DIDEVICEOBJECTINSTANCEA)==316 && sizeof(DIDEVICEOBJECTINSTANCE_DX3A)==292);
     static_assert(offsetof(DIDEVICEOBJECTINSTANCEA,tszName)==32 && offsetof(DIDEVICEOBJECTINSTANCEA,dwFFMaxForce)==292);
     if(size!=sizeof(DIDEVICEOBJECTINSTANCEA) && size!=sizeof(DIDEVICEOBJECTINSTANCE_DX3A))
      deny("DIDEVICEOBJECTINSTANCEA size outside the model",size);
     if(!writable(out,size))deny("GetObjectInfo output outside the memory contract",out);
     // Both ANSI layouts contain only DWORDs, WORDs, GUIDs and inline characters;
     // they have identical x86/x64 offsets. Never expose a guest pointer to COM.
     DIDEVICEOBJECTINSTANCEA info{};info.dwSize=size;
     const HRESULT hr=dv->GetObjectInfo(&info,arg(2),arg(3));
     if(SUCCEEDED(hr))for(unsigned i=0;i<size;++i)
      runtime.memory().store<unsigned char>({out+i},reinterpret_cast<const unsigned char*>(&info)[i]);
     apis.back()+="(size="+std::to_string(size)+",object="+std::to_string(arg(2))+",how="+std::to_string(arg(3))+")="+std::to_string(unsigned(hr));
     return done(unsigned(hr),4);
    }
'''


def apply(host: Path):
    path=host/'mfc_stage.hpp'
    source=path.read_text(encoding='utf-8')
    if 'if(n=="GetObjectInfo")' in source:
        if source.count(HANDLER)!=1:
            raise ValueError('Unknown or partial DirectInput object-info adapter')
        return
    anchor='    if(n=="GetDeviceInfo"){const unsigned a=arg(1);'
    if source.count(anchor)!=1:
        raise ValueError('Original DirectInput device-info dispatch changed')
    source=source.replace(anchor,HANDLER+anchor,1)
    path.write_text(source,encoding='utf-8',newline='\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
