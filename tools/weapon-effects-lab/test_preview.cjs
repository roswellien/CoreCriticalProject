// Offline adapter test only. Does not launch/control a browser or prove appearance.
const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
if(process.argv.length!==3)throw Error('Usage: node test_preview.cjs built-preview.html');
const html=fs.readFileSync(process.argv[2],'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let draws=0,requests=0,fieldDraws=0,ribbonStrokes=0;
const gradient={addColorStop(offset,color){assert(Number.isFinite(offset));assert.equal(typeof color,'string');}};
const context=new Proxy({}, {get(target,key){
 if(key in target)return target[key];
 if(key==='createRadialGradient'||key==='createLinearGradient')return (...args)=>{args.forEach(x=>assert(Number.isFinite(x)));return gradient;};
 return (...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a),'Nonfinite canvas coordinate');
  if(key==='drawImage'){draws++;if(args[0].src?.startsWith('data:image/png;base64,'))fieldDraws++;}
  if(key==='stroke'&&target.globalCompositeOperation==='lighter')ribbonStrokes++;
 };
},set(target,key,value){if(typeof value==='number')assert(Number.isFinite(value));target[key]=value;return true;}});
const nodes=new Map();
const node=(id)=>{
 if(!nodes.has(id))nodes.set(id,{checked:true,value:id==='speed'?'1':'0',textContent:'',setAttribute(k,v){this[k]=v;}});
 return nodes.get(id);
};
const canvas=Object.assign(node('view'),{width:0,height:0,clientWidth:1000,clientHeight:540,getContext:()=>context,setPointerCapture(){}});
const tabs=[0,1,2,3].map(x=>({dataset:{scene:String(x)},setAttribute(k,v){this[k]=v;}}));
const sandbox={console,performance:{now:()=>0},devicePixelRatio:1,
 matchMedia:()=>({matches:true}),requestAnimationFrame(){requests++;},
 window:{addEventListener(){}},document:{hidden:false,
 querySelector:q=>q==='#view'?canvas:node(q.slice(1)),getElementById:node,
 querySelectorAll:()=>tabs,addEventListener(){},
 createElement:tag=>tag==='img'?{complete:true,naturalWidth:64,naturalHeight:96}:
   ({width:0,height:0,getContext:()=>context})}};
vm.createContext(sandbox);vm.runInContext(script,sandbox,{timeout:10000});
assert.equal(node('play').textContent,'Play','Reduced motion does not start paused');
assert(draws>0,'Reduced-motion initial preview is empty');
assert.match(node('playback-status').textContent,/Paused for reduced motion/);
assert.equal(vm.runInContext('impactColor',sandbox),'mixed','Initial impact must mix all four requested colors');
assert.equal(vm.runInContext('scene',sandbox),1,'Preview must open on the requested Gauss impact');
assert(vm.runInContext('DATA.scenes[1].frames[21].p.filter(p=>p[11]>=0xffff0000&&p[11]<0xffff0009&&p[6]>.12&&p[7]>.6).length===9',sandbox),'Gauss initial review lacks its opaque conical hot body');
assert(vm.runInContext('(()=>{const p=DATA.scenes[1].frames[21].p.find(p=>p[8]===4);return impactParticle(p)===p;})()',sandbox),'Spark palette tints the white-orange hot body');
for(const tab of tabs){
 const before=draws;
 tab.onclick();assert.equal(tab['aria-pressed'],'true');
 assert(draws>before,`Selecting scene ${tab.dataset.scene} shows an empty frame`);
 for(const time of [0,.25,.3,.5,1,1.2,1.7,2.4,3.5,4]){
  node('timeline').oninput({target:{value:String(time)}});
  assert(node('stats').textContent.includes('particles'));
 }
 for(const id of ['particles','light','bounds']){node(id).checked=false;node(id).onchange();node(id).checked=true;node(id).onchange();}
}
node('angle').oninput({target:{value:'65'}});
canvas.onpointerdown({clientX:100,pointerId:1});canvas.onpointermove({clientX:200});canvas.onpointerup();
node('restart').onclick();node('play').onclick();
assert.equal(node('play').textContent,'Pause');
vm.runInContext('animate(100);',sandbox,{timeout:10000});
assert(requests>=2&&draws>100,'Preview never renders particle sprites');
vm.runInContext('scene=1;t=loopRanges[1][1]-.01;playing=true;last=100;animate(200);',sandbox,{timeout:10000});
assert(vm.runInContext('t>=loopRanges[1][0]&&t<loopRanges[1][1]',sandbox),'Short burst loops through blank full-duration tail');
tabs[0].onclick();node('impact-replay').onclick();
assert(vm.runInContext('playing&&t<impactTimes[0]&&t>impactTimes[0]-.1',sandbox),'PPC impact replay does not start before hit');
tabs[1].onclick();node('impact-replay').onclick();
assert(vm.runInContext('playing&&t<impactTimes[1]&&t>impactTimes[1]-.1',sandbox),'Gauss impact replay does not start before hit');
tabs[2].onclick();assert.equal(node('impact-replay').disabled,true);
for(const palette of ['green','orange','purple','teal','mixed']){
 tabs[1].onclick();node('impact-color').onchange({target:{value:palette}});
 assert.equal(vm.runInContext('impactColor',sandbox),palette);
 const result=vm.runInContext('impactTint([1,2,3],1)',sandbox);
 assert(result.every(Number.isFinite));assert.equal(Math.max(...result),3);
}
assert(vm.runInContext('impactTint([1,2,3],0).join()!==impactTint([1,2,3],1).join()',sandbox),'Mixed palette does not distribute colors');
assert(vm.runInContext('(()=>{const p=[0,0,0,.3,.2,.1,.1,.5,3,0,1,5];return impactParticle(p)===p;})()',sandbox),'Palette recolors physical metal debris');
assert(vm.runInContext('(()=>{const p=[0,0,0,.3,.2,.1,.1,.5,1,0,0,5];return impactParticle(p)===p;})()',sandbox),'Palette recolors unrelated launch/travel');
tabs[0].onclick();assert.equal(node('impact-color').disabled,true);
assert(vm.runInContext('(()=>{const p=[0,0,0,.3,.2,.1,.1,.5,1,0,1,5];return impactParticle(p)===p;})()',sandbox),'Gauss palette recolors PPC impact');
tabs[2].onclick();assert.equal(node('impact-color').disabled,true);
assert(fieldDraws>10,'Baked fluid sheets never reach the renderer');
assert(ribbonStrokes>10,'Connected trails/impact rings never reach the renderer');
console.log(`Offline viewer controls passed; ${draws} image draws (${fieldDraws} fluid sheets), ${ribbonStrokes} ribbon strokes. Browser appearance unverified.`);
