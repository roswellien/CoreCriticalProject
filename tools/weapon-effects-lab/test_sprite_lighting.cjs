// Actual lighting math + offline UI contracts. Does not automate a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(process.argv[2],'utf8'),script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let sprites=0,receivers=0;const nodes=new Map();
const context=new Proxy({}, {get(t,k){
 if(k==='createImageData')return (w,h)=>({data:new Uint8ClampedArray(w*h*4)});
 if(k==='putImageData')return data=>{assert(data.data.length===320*220*4);receivers++;};
 return t[k]||((...args)=>{for(const x of args)if(typeof x==='number')assert(Number.isFinite(x));if(k==='drawImage'&&args[0].src)sprites++;});
},set(t,k,v){t[k]=v;return true;}});
function node(id){if(!nodes.has(id))nodes.set(id,{value:id==='radius'?'2.7':id==='strength'?'1.5':'0',clientWidth:640,clientHeight:440,getContext:()=>context});return nodes.get(id);}
const sandbox={console,performance:{now:()=>0},devicePixelRatio:1,requestAnimationFrame(){},window:{addEventListener(){}},document:{hidden:false,getElementById:node,createElement:tag=>tag==='img'?{complete:true,naturalWidth:512}:{getContext:()=>context}}};
vm.createContext(sandbox);vm.runInContext(script,sandbox,{timeout:20000});
const off=vm.runInContext('receiverPixels(0)',sandbox),on=vm.runInContext('receiverPixels(1.5)',sandbox);
let changed=0;for(let i=0;i<off.length;i+=4){assert.equal(off[i+3],255);if(off[i]!==on[i]||off[i+1]!==on[i+1]||off[i+2]!==on[i+2])changed++;}
assert(changed>500,'Light does not illuminate a visible receiver region');
for(const effect of ['ppc','gauss','fire'])for(const bank of ['stock','current']){
 node('effect').onchange({target:{value:effect}});node('bank').onchange({target:{value:bank}});
 for(const time of [0,.12,.4,.9])node('timeline').oninput({target:{value:String(time)}});
}
vm.runInContext("effect='gauss';age=1.3;",sandbox);
assert.deepEqual(Array.from(vm.runInContext('receiverPixels(0)',sandbox)),Array.from(vm.runInContext('receiverPixels(3)',sandbox)),'Expired flash continues illuminating');
vm.runInContext("effect='ppc';age=.12;",sandbox);
assert.deepEqual(Array.from(off),Array.from(vm.runInContext('receiverPixels(0)',sandbox)),'Disabled receiver image changes with selected light color');
node('strength').value='0';node('strength').oninput();node('radius').value='.5';node('radius').oninput();
node('replay').onclick();vm.runInContext('tick(100);',sandbox);assert(vm.runInContext('age>0',sandbox));
assert(sprites>20&&receivers>20,'Receiver/sprite drawing not exercised');
assert(!html.includes('/*SPRITE_LIGHT_DATA*/null'));
console.log(`Sprite lighting checks passed: ${changed} receiver pixels respond; ${sprites} unchanged sprite draws. Browser pixels unverified.`);
