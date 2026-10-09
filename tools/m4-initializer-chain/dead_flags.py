"""Prove each undefined intermediate flag is dead across the complete CFG."""
import re
SSA=r'%[A-Za-z0-9_.$]+'
def require(ok,why):
    if not ok:raise ValueError(why)
def prove(body,offsets):
    blocks={'entry':[]};current='entry'
    for raw in body.splitlines():
        line=raw.split(';',1)[0].strip()
        if not line:continue
        label=re.fullmatch(r'([A-Za-z0-9_.$]+):',line)
        if label:current=label[1];require(current not in blocks,'Duplicate CFG block');blocks[current]=[]
        else:blocks[current].append(line)
    edges={}
    for block,lines in blocks.items():
        term=lines[-1]
        if term.startswith('ret ptr '):edges[block]=[]
        else:
            require(term.startswith('br '),'Unreviewed CFG terminator')
            edges[block]=re.findall(r'label %([A-Za-z0-9_.$]+)',term)
            require(1<=len(edges[block])<=2 and all(x in blocks for x in edges[block]),'Unknown CFG successor')
    visited={'entry'};pending=['entry']
    while pending:
        for target in edges[pending.pop()]:
            if target not in visited:visited.add(target);pending.append(target)
    require(visited==set(blocks),'Unreachable guest block')
    roots=[];taints={};terminals=[];uses={}
    for block,lines in blocks.items():
        for index,line in enumerate(lines):
            definition=re.match(r'('+SSA+r') = (.*)',line)
            target,rhs=(definition[1],definition[2]) if definition else (None,line)
            operands=re.findall(SSA,rhs)
            origins=set().union(*(taints.get(x,set()) for x in operands))
            for operand in operands:
                if operand in taints and taints[operand]:uses[operand]=uses.get(operand,0)+1
            if '@__remill_undefined_8' in rhs:
                require(target and re.fullmatch(r'call(?: zeroext)? i8 @__remill_undefined_8\(\)(?: #\d+)?',rhs),'Unknown undefined root')
                roots.append(target);taints[target]={target}
            elif origins:
                if target:
                    require(re.fullmatch(r'(?:icmp ne i8 '+SSA+r', 0|zext i1 '+SSA+r' to i8)',rhs),'Undefined value escapes reviewed scalar conversion')
                    taints[target]=origins
                else:
                    store=re.fullmatch(r'store i8 ('+SSA+r'), ptr ('+SSA+r'), align 1',rhs)
                    require(store and offsets.get(store[2]) in (2069,2077),'Undefined value reaches non-flag observable')
                    terminals.append((block,index,offsets[store[2]],store[1],sorted(origins)))
            elif target:taints[target]=set()
    require(all(uses.get(x,0)>0 for x in taints if taints[x]),'Unconsumed undefined SSA chain')
    require(set(roots)==set().union(*(set(x[4]) for x in terminals)) if roots else not terminals,'Missing undefined terminal')
    proofs=[]
    for start,index,offset,value,origins in terminals:
        pending=[(start,index+1)];seen=set();overwrites=[]
        while pending:
            block,position=pending.pop()
            if (block,position) in seen:continue
            seen.add((block,position));cleared=False
            for number in range(position,len(blocks[block])):
                line=blocks[block][number]
                load=re.search(r'load i(\d+), ptr ('+SSA+r'), align ',line)
                if load and load[2] in offsets:
                    lo=offsets[load[2]];width=int(load[1])//8
                    require(not(lo<=offset<lo+width),'Undefined flag loaded before overwrite')
                store=re.fullmatch(r'store i(\d+) ([^,]+), ptr ('+SSA+r'), align \d+',line)
                if store and store[3] in offsets:
                    lo=offsets[store[3]];width=int(store[1])//8
                    if lo<=offset<lo+width:
                        require(width==1 and lo==offset,'Unknown overlapping flag store')
                        if not taints.get(store[2],set()):
                            overwrites.append({'block':block,'instruction_index':number,'instruction':line});cleared=True;break
                require(not re.search(r'@(?:sub_[0-9a-f]+|__remill_function_return)\(',line),'Undefined flag escapes via State boundary')
                require(not line.startswith('ret ptr '),'Undefined flag escapes final return')
            if not cleared:
                require(edges[block],'Undefined flag reaches CFG exit')
                pending.extend((target,0) for target in edges[block])
        require(overwrites,'No defined overwrite for undefined flag')
        proofs.append({'root_values':origins,'terminal_block':start,'terminal_instruction_index':index,'flag_offset':offset,'terminal_value':value,'overwrites':overwrites})
    return {'policy':'complete-CFG-dead-SSA-and-State-flag-v1','blocks':list(blocks),'edges':edges,
            'all_blocks_reachable':True,'undefined_calls':len(roots),'observable_undefined_values':0,
            'replacement_value':0,'proofs':proofs}
