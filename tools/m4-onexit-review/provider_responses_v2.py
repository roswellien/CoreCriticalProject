"""Retain literal malloc source request independently of its rounded API size."""
import provider_responses as prior
I=prior.I
B=prior.B
NEW_CONTRACTS=prior.NEW_CONTRACTS
class ActualResponses(prior.ActualResponses):
 def __call__(self,m,target):
  site=m.PCs[-1];source_request=None
  if site not in NEW_CONTRACTS and self.contracts.get(site,{}).get('name')=='HeapAlloc':
   frames=[f for f in m.call_stack if f[0]==0x780012b3]
   I.need(frames,'Original malloc source frame owns its independently derived request')
   source_request=int.from_bytes(m.bytes(frames[-1][1]+4,4),'little')
  before=self.index;super().__call__(m,target)
  if source_request is not None and self.index==before+1:
   allocation=self.allocations[-1];rounded=(source_request+15)&~15
   if not rounded:rounded=16
   I.need(0<=source_request<=1048576 and allocation['extent']==rounded,
          'Literal original malloc request and exact mode1 API rounding')
   allocation['requested']=source_request
