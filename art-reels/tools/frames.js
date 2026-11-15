const {chromium}=require('playwright');
(async()=>{const [,,html,out,fps,dur,only]=process.argv;
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+html);await p.waitForTimeout(2000);
const ts= only? only.split(',').map(Number) : Array.from({length:Math.round(dur*fps)},(_,i)=>i/fps);
for(let i=0;i<ts.length;i++){await p.evaluate(t=>render(t),ts[i]);await p.screenshot({path:`${out}/f${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92});}
await b.close()})();
