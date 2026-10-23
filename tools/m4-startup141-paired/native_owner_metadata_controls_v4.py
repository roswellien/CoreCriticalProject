"""Pure causal metadata controls, no actual reader or native/source machine."""
import copy
def controls(derive):
 resource=[1,1,5,0x78145640,24,40,1,0];facts=[];mfc=[];strings=[];contracts={}
 def api(slot,site,raw,argc,args,result=0,guest=0,extent=0):
  w=[0]*32;w[:8]=[1,len(facts),site,slot,raw,0x20001700,site+6,argc];w[8]=result;w[12]=guest;w[13]=extent;w[14:16]=[1,1];w[20:20+len(args)]=args;facts.append(w);contracts[site]=['typed',slot,raw,argc,0];return w
 for n in range(4):api(0x7802e03c,0x78003c00+n*8,0x3444e,1,[0x780370e8+n*24])
 life=api(0x78146190,0,0x866ce,0,[],1);life[16]=0x300000;life[31]=1
 api(0x7802e094,0x7800137f,0x345c6,3,[0x48450001,0,128],0x100000,0x31000000,128)
 for n in range(7):
  guest=0x31001000+n*4096;native=0x110000+n*16;api(0x7802e094,0x7800137f,0x345c6,3,[0x48450001,0,16],native,guest,16);m=[0]*32;m[0]=1;m[3]=0x5f401ea0;m[7]=m[13]=12;m[16]=m[20]=guest;m[17]=native;m[18]=7+n;m[19]=16;m[21]=1;mfc.append(m)
 baseline=dict(facts=facts,mfc=mfc,strings=strings,resource=resource,growth=[],cut=len(facts),contracts=contracts)
 def run(d):return derive(**d)
 result=run(copy.deepcopy(baseline));assert result['owners'][0x31000000]['generation']==6 and result['owners'][0x31000000]['requested']==128 and result['owners'][0x31000000]['native']==0x100000 and len(result['owners'])==8 and sum(o['kind']==4 for o in result['owners'].values())==7 and result['generation']==13
 assert [(v['event'],v['generation'])for v in result['events'][:6]]==[('CS-birth',1),('CS-birth',2),('CS-birth',3),('CS-birth',4),('distinct-Lockit-association',5),('HeapAlloc-birth',6)]
 assert run(dict(copy.deepcopy(baseline),cut=0))['generation']==0 and run(dict(copy.deepcopy(baseline),cut=4))['generation']==4
 prior=run(dict(copy.deepcopy(baseline),cut=6));assert len(prior['owners'])==1 and prior['generation']==6
 # A future OLD growth witness is not consulted or used to seed this cut.
 future=[0]*32;future[:3]=[1,100,0x78011c27];future[5]=999;assert run(dict(copy.deepcopy(baseline),growth=[future]))['owners']==result['owners']
 mutations=[]
 def add(n,f):mutations.append((n,f))
 add('wrong-heap-token',lambda d:d['facts'][5].__setitem__(20,0x48450002));add('wrong-heap-flags',lambda d:d['facts'][5].__setitem__(21,1))
 for offset,value in [(2,0x78003c01),(3,0x78146194),(4,0x866cf),(5,0x20001700),(6,0x410a80),(7,1),(8,0),(16,0),(31,0),(20,1)]:add('lifecycle-word-'+str(offset),lambda d,i=offset,v=value:d['facts'][4].__setitem__(i,v))
 add('lifecycle-late-generic-marker',lambda d:d['facts'][5].__setitem__(31,1))
 add('resource-generation',lambda d:d['resource'].__setitem__(2,9));add('resource-identity',lambda d:d['resource'].__setitem__(3,0x78145644));add('resource-state',lambda d:d['resource'].__setitem__(1,0));add('cut-past-prefix',lambda d:d.__setitem__('cut',len(d['facts'])+1));add('wrong-API-index',lambda d:d['facts'][5].__setitem__(1,6));add('incomplete-birth',lambda d:d['facts'][5].__setitem__(14,0));add('unknown-sourcePC',lambda d:d['facts'][5].__setitem__(2,0));add('wrong-rawtarget',lambda d:d['facts'][5].__setitem__(4,1));add('wrong-IAT',lambda d:d['facts'][5].__setitem__(3,1));add('wrong-arity',lambda d:d['facts'][5].__setitem__(7,4));add('manager-not128',lambda d:d['facts'][5].__setitem__(22,112));add('manager-wrong-guest',lambda d:d['facts'][5].__setitem__(12,0x31001000));add('manager-pointer-unaligned',lambda d:d['facts'][5].__setitem__(8,0x100001));add('manager-wrong-extent',lambda d:d['facts'][5].__setitem__(13,127));add('missing-MFC-source',lambda d:d['mfc'].pop());add('wrong-MFC-request',lambda d:d['mfc'][0].__setitem__(7,4));add('wrong-MFC-native',lambda d:d['mfc'][0].__setitem__(17,1));add('future-MFC-generation',lambda d:d['mfc'][0].__setitem__(18,999));add('wrong-MFC-extent',lambda d:d['mfc'][0].__setitem__(19,32));add('wrong-MFC-return',lambda d:d['mfc'][0].__setitem__(20,0));add('duplicate-MFC-role',lambda d:d['mfc'].append(copy.deepcopy(d['mfc'][0])));add('duplicate-CS',lambda d:d['facts'][1].__setitem__(20,d['facts'][0][20]));add('future-generation-gap',lambda d:d['facts'][0].__setitem__(3,0x7802e044))
 refused=[]
 for name,mutation in mutations:
  d=copy.deepcopy(baseline);mutation(d)
  try:run(d)
  except (AssertionError,ValueError,KeyError):refused.append(name)
  else:raise AssertionError('Causal metadata adverse accepted '+name)
 def add_fact(d,slot,site,raw,argc,args,actual,result,extent,native):
  w=[0]*32;w[:8]=[1,len(d['facts']),site,slot,raw,0x20001700,site+6,argc];w[8]=actual;w[12]=result;w[13]=extent;w[14:16]=[1,1];w[16]=native;w[20:20+len(args)]=args;d['facts'].append(w);d['contracts'][site]=['typed',slot,raw,argc,0];d['cut']=len(d['facts']);return w
 sized=copy.deepcopy(baseline);size=add_fact(sized,0x7802e1dc,0x780015b5,0x34bd0,3,[0x48450001,0,0x31000000],128,128,128,0x100000);size[17]=128;assert run(sized)['owners'][0x31000000]['capacity']==128
 grown=copy.deepcopy(sized);w=add_fact(grown,0x7802e0b4,0x78011c27,0x3464a,4,[0x48450001,0,0x31000000,144],0x200000,0x31008000,144,0x100000);w[17]=128;g=[0]*32;g[:11]=[1,14,0x78011c27,0x31000000,0x100000,6,128,128,128,144,144];g[11]=0x200000;g[13:18]=[0x31008000,0x200000,14,144,0];g[18:23]=[1,1,144,0,1];grown['growth']=[g];predicted=run(grown);assert 0x31000000 not in predicted['owners']and predicted['owners'][0x31008000]['generation']==14 and predicted['owners'][0x31008000]['requested']==144
 freed=copy.deepcopy(baseline);add_fact(freed,0x7802e090,0x78001430,0x345ba,3,[0x48450001,0,0x31000000],1,1,0,0x100000);assert 0x31000000 not in run(freed)['owners']
 for label,d in [('HeapSize',sized),('HeapReAlloc',grown),('HeapFree',freed)]:
  for index,value in [(20,0x48450002),(21,1),(16,0x100010)]:
   bad=copy.deepcopy(d);bad['facts'][-1][index]=value
   try:run(bad)
   except (AssertionError,ValueError,KeyError):refused.append(label+'-association-'+str(index))
   else:raise AssertionError('Heap association mutation accepted')
 bad=copy.deepcopy(freed);bad['facts'][-1][12]=2
 try:run(bad)
 except (AssertionError,ValueError,KeyError):refused.append('HeapFree-exact-BOOL')
 else:raise AssertionError('HeapFree mismatched actual BOOL accepted')
 for offset,value in [(5,999),(6,112),(15,999),(24,1),(12,1)]:
  bad=copy.deepcopy(grown);bad['growth'][0][offset]=value
  try:run(bad)
  except (AssertionError,ValueError,KeyError):refused.append('growth-corroboration-'+str(offset))
  else:raise AssertionError('Growth metadata mutation accepted')
 return dict(passed=True,scope='Synthetic causal owner metadata only; no actual source replay or reader',negative_controls=len(refused),refused=refused,positive_manager_generation6=True,positive_ordered_fourCS_then_Lockit5_then_registry6=True,positive_before_association_cuts_not_seeded=True,positive_HeapSize_capacity=True,positive_grown_generation14=True,positive_actual_HeapFree=True,positive_total8_registry1_MFC7=True,positive_pre_cut6_registry_only=True,future_OLD_growth_witness_not_seed=True,source_execution=False,reader_opened=False)
