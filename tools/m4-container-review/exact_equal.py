"""Full byte equality; enumerate diagnostic differences only after failure."""
def equal(a,b,label):
 if len(a)==len(b)and a==b:return
 differences=[]
 for i,(x,y)in enumerate(zip(a,b)):
  if x!=y:
   differences.append((i,x,y))
   if len(differences)==16:break
 raise ValueError(label+' '+str(differences))

def selfcheck():
 passed=0;refused=0
 for a,b in((b'',b''),(b'abc',b'abc'),(bytes(range(256))*16,bytes(range(256))*16),(bytearray(b'abc'),b'abc')):
  equal(a,b,'same full bytes');passed+=1
 for a,b in((b'',b'a'),(b'a',b''),(b'abc',b'abd'),(b'abc',b'abcd'),(bytes(4095)+b'x',bytes(4096)),(bytes(4096),bytes(4095)+b'x')):
  try:equal(a,b,'whole byte difference')
  except ValueError:refused+=1
  else:raise AssertionError('Full extent/bytes comparison weakened')
 return dict(equal_cases=passed,difference_refusals=refused)
