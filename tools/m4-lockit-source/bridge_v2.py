"""Frozen bootstrap source plus an explicit unchanged-guest resource seam."""
import inspect
import provider_bridge as B

def bootstrap(*args,resource_association,**kwargs):
 source=inspect.getsource(B.bootstrap)
 anchor=" I.need(len(responses.sections)==4 and responses.index==4,'Genuine four static lock initializations')"
 assert source.count(anchor)==1
 source=source.replace(anchor,anchor+'\n _RESOURCE_ASSOCIATION(m,responses)')
 source=source.replace("I.need(responses.index==5 and empty['begin']==empty['next']", "I.need(responses.index==6 and empty['begin']==empty['next']")
 namespace=dict(vars(B));namespace['_RESOURCE_ASSOCIATION']=resource_association
 exec(compile(source,'<frozen-bootstrap-with-resource-seam>','exec'),namespace)
 return namespace['bootstrap'](*args,**kwargs)
