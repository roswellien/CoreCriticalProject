"""Exact retained predicate identities; explicit independently allowed finite deltas.

This validates configuration data only. It executes no evidence checker or
physical union. An allowance is authoritatively supplied by the separately
sealed independent configuration review, never inferred from gate success.
"""
def need(value,label):
 if not value:raise ValueError(label)

def typed(a,b):return type(a)is type(b)and a==b

IDENTITY_REASON='Exact unchanged accepted131 typed predicate'
DELTA_KEYS={'baseline_expected','current_field','current_expected','physical_domain','reason'}

def named_delta(delta):
 need(set(delta)==DELTA_KEYS,'Exact explicit finite predicate delta schema')
 for key in ('current_field','physical_domain','reason'):
  need(isinstance(delta[key],str)and delta[key].strip()==delta[key]and delta[key],'Named finite predicate delta '+key)
 need(len(delta['physical_domain'])>=12 and len(delta['reason'])>=24,'Substantive physical domain and causality reason')
 need(delta['physical_domain'].lower()not in ('current report','current value','independently reviewed'),'No generic success/domain allowance')
 need(delta['reason'].lower()not in ('independently reviewed','current value independently reviewed','same current receipt predicate path; current domain/value independently reviewed'),'No blanket review assertion')

def relation(field,old,value,delta=None):
 if delta is None:
  need(typed(old,value),'Unchanged baseline typed value requires explicit finite delta '+field)
  return dict(baseline_field=field,baseline_expected=old,current_field=field,current_expected=value,kind='identity',physical_domain=None,reason=IDENTITY_REASON)
 named_delta(delta)
 need(typed(delta['baseline_expected'],old)and typed(delta['current_expected'],value),'Explicit physical delta old/current typed expectations '+field)
 need(type(old)is type(value),'Retained predicate type '+field)
 need(not isinstance(old,bool)or old==value,'Retained boolean acceptance invariant '+field)
 need(delta['current_field']!='passed'or field=='passed','No predicate collapsed to success '+field)
 need(delta['current_field']!=field or not typed(old,value),'Only necessary explicit finite delta '+field)
 return dict(baseline_field=field,kind='finite_delta',**delta)

def validate(config,baseline,base_required):
 coverage=config['baseline_criteria'];need(set(coverage)==base_required,'Every accepted131 gate retained');deltas={};count=0
 for label,gate in baseline['gates'].items():
  need(set(coverage[label])==set(gate['equal']),'Every accepted baseline predicate retained '+label)
  targets=set()
  for field,old in gate['equal'].items():
   row=coverage[label][field]
   need(set(row)=={'baseline_field','baseline_expected','current_field','current_expected','kind','physical_domain','reason'},'Exact retained predicate relation')
   need(row['baseline_field']==field and typed(row['baseline_expected'],old),'Actual accepted baseline path/typed expectation '+label+'.'+field)
   target=row['current_field'];need(isinstance(target,str)and target not in targets,'Distinct current predicate path '+label+'.'+field);targets.add(target)
   need(target in config['gates'][label]['equal']and typed(row['current_expected'],config['gates'][label]['equal'][target]),'Exact configured current typed expectation '+label+'.'+field)
   if row['kind']=='identity':
    need(row==relation(field,old,row['current_expected'])and target==field,'Literal unchanged predicate relation '+label+'.'+field)
   else:
    need(row['kind']=='finite_delta','Only identity or finite delta')
    delta={key:row[key]for key in DELTA_KEYS};need(row==relation(field,old,row['current_expected'],delta),'Exact finite delta relation')
    deltas.setdefault(label,{})[field]=delta
   count+=1
 need(count==841,'All841 actual accepted typed predicates')
 return deltas

def review_allowances(review,deltas):
 need('criteria_delta_allowances'in review,'Separately sealed independent finite delta allowances required')
 def equal(a,b):
  if type(a)is not type(b):return False
  if isinstance(a,dict):return set(a)==set(b)and all(equal(a[k],b[k])for k in a)
  if isinstance(a,list):return len(a)==len(b)and all(equal(x,y)for x,y in zip(a,b))
  return a==b
 need(equal(review['criteria_delta_allowances'],deltas),'All-and-only exact separately reviewed finite predicate deltas')
