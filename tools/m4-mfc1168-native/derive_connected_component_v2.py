from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=R/'reports/m4-mfc1168-native/connected-component-preparation-r1/connected_component.cpp'
text=p.read_text();assert hashlib.sha256(p.read_bytes()).hexdigest()=='102092ededcff7072c9b6cc454d666870bdbb4980b77fbc8eee26b629309b3bc'
a='CS.RecursionCount==CS_depth';b='static_cast<unsigned>(CS.RecursionCount)==CS_depth';assert text.count(a)==1;text=text.replace(a,b)
a='throw std::runtime_error("Unentered cold/padded source instruction denied");';b='std::terminate(); /* Intrinsic is nothrow; this unreachable cold exit fails closed. */';assert text.count(a)==1;text=text.replace(a,b)
out=R/'tools/m4-mfc1168-native/connected_component_v2.cpp';assert not out.exists();out.write_text(text)
