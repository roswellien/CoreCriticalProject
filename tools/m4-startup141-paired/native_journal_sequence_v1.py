"""Exact list/tuple representation normalization of the entire typed operand sequence."""
def normalized(rows):
 if type(rows)not in(list,tuple):raise ValueError('Whole operand sequence must be list or tuple')
 result=[]
 for row in rows:
  if type(row)not in(list,tuple)or len(row)!=5 or any(type(v)is not int for v in row):raise ValueError('Exactly five scalar integers per operand; Booleans refused')
  pc,address,value,width,write=row
  if not(0<=pc<=0xffffffff and 0<=address<=0xffffffff and 0<=value<=0xffffffffffffffff and width in(1,2,4,8)and write in(0,1)):raise ValueError('Exact unsigned source operand schema')
  result.append(tuple(row))
 return tuple(result)
def equal(actual,carried):return normalized(actual)==normalized(carried)
