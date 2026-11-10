/* ============================== bangun dunia + HUD ============================== */
let PROG=[],PAGES=[];
function build(){
  const xs=SCN.map(s=>s.cx),ys=SCN.map(s=>s.cy),x0=Math.min(...xs)-2300,x1=Math.max(...xs)+2300,y0=Math.min(...ys)-3000,y1=Math.max(...ys)+3000;
  const pp=document.createElement('div');pp.className='paper';pp.style.cssText=`left:${x0}px;top:${y0}px;width:${x1-x0}px;height:${y1-y0}px`;world.appendChild(pp);
  SCN.forEach(s=>SCENES[s.jenis].build(s));
  $('#mascot').innerHTML=mascotSVG();
  $('#lens').innerHTML=`<svg width="1400" height="800" viewBox="-20 -400 1400 800" style="overflow:visible">${leafG(1340,480)}</svg>`;
  PROG=SCN.filter(s=>['langkah','banding','twist'].includes(s.jenis));
  $('#prog').innerHTML=PROG.map((s,i)=>`<div class="sg${s.jenis==='twist'?' w':''}"><i id="pg${i}"></i></div>`).join('');
  const subs=$('#subs');PAGES=(TL.pages||[]).map(p=>{const ws=LANG==='en'?p.en_words:p.words;const el=document.createElement('div');el.className='sp';
    el.innerHTML=ws.map(w=>`<span class="sw">${esc(w.w)}</span>`).join(' ');subs.appendChild(el);return {p,ws,el,spans:$$('.sw',el)};});
  const noise=`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .32 0 0 0 0 .27 0 0 0 0 .2 0 0 0 .55 0'/%3E%3C/filter%3E%3Crect width='260' height='260' filter='url(%23n)'/%3E%3C/svg%3E")`;
  const fiber=`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='520' height='520'%3E%3Cfilter id='f'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.012 .05' numOctaves='3' seed='4'/%3E%3CfeColorMatrix values='0 0 0 0 .55 0 0 0 0 .45 0 0 0 0 .3 0 0 0 .10 0'/%3E%3C/filter%3E%3Crect width='520' height='520' filter='url(%23f)'/%3E%3C/svg%3E")`;
  document.documentElement.style.setProperty('--noise',noise);document.documentElement.style.setProperty('--fiber',fiber);
}

/* ============================== koreografi ============================== */
function choreo(){
  C.x=SCN[0].cx;C.y=SCN[0].cy-60;C.z=1;
  mascotFromTags();
  SCN.forEach(s=>SCENES[s.jenis].choreo(s));
  SCN.forEach(s=>{const f=SCENES[s.jenis].sfx;if(f)f(s);});
  const cta=SCN.find(s=>s.jenis==='cta');
  if(PROG.length)PROG.on=PROG[0].cut,PROG.off=cta?cta.cut+.3:DUR;
  tl.to({},{duration:.001},DUR);
  MPOS.sort((a,b)=>a.t-b.t);MEXP.sort((a,b)=>a.t-b.t);SFX.sort((a,b)=>a.t-b.t);
}
/* pupil maskot mengikuti sorotan rolet */
function mascotLook(t){for(const s of SCN){if(s.jenis!=='kuis'||!s.roul||t<s.roul.t[0]||t>=s.roul.end)continue;
  const k=roulAt(s,t);if(k<0)return null;const G=s.G,x=G.xs[k]+G.w/2;return [x<500?-12:x>580?12:0,-3];}return null;}

/* ============================== render(t): semua efek fungsi murni dari t ============================== */
let grainK=-1;
function render(t){
  applyCam(t);
  const bx=FX.whipX,by=FX.whipY,cam=$('#cam');
  if(bx>.4||by>.4){$('#whipG').setAttribute('stdDeviation',`${bx.toFixed(1)} ${by.toFixed(1)}`);cam.style.filter='url(#whip)';}else cam.style.filter='none';
  const k=Math.floor(t*12);if(k!==grainK){grainK=k;$('#grain').style.transform=`translate(${(k*37)%60-30}px,${(k*61)%60-30}px)`;}
  $('#light').style.background=`radial-gradient(55% 32% at ${f1(30+Math.sin(t*.21)*16)}% ${f1(24+Math.sin(t*.17+1)*8)}%,rgba(255,236,190,.26),transparent 70%)`;
  SCN.forEach(s=>{const f=SCENES[s.jenis].render;if(f)f(s,t);});
  /* layar meredup saat open loop */
  {let o=0;for(const s of SCN)if(s.dim)o=Math.max(o,Math.min(clamp((t-s.dim.t0)/.4),clamp((s.dim.t1-t)/.35))*.8);$('#dim').style.opacity=o.toFixed(3);}
  /* daun raksasa melintas lensa (transisi ke CTA) */
  {const p=FX.lensP,L=$('#lens');L.style.opacity=p>0&&p<1?1:0;
    if(p>0&&p<1)L.style.transform=`translate(${f1(lerp(-2700,1500,p))}px,${f1(lerp(2400,-1300,p))}px) rotate(-38deg) scale(${lerp(1.9,3.0,Math.sin(p*Math.PI)).toFixed(3)})`;}
  /* progress bar */
  if(PROG.length){const o=Math.min(clamp((t-PROG.on)/.3),clamp((PROG.off-t)/.3));$('#prog').style.opacity=o.toFixed(3);
    PROG.forEach((s,i)=>{$('#pg'+i).style.width=f1(clamp((t-s.cut)/(s.end-s.cut))*100)+'%';});}
  /* denyut ketukan */
  {const on=new Set();for(const p of PULSES){if(t<p.t0||t>p.t1)continue;const ph=(t/T)%1;on.add(p.el);p.el.style.scale=(1+p.amp*Math.exp(-ph*5)).toFixed(4);}
    for(const p of PULSES)if(!on.has(p.el)&&p.el.style.scale)p.el.style.scale='';}
  renderMascot(t);
  /* subtitle per kata: muncul 120 ms sebelum kata pertama, halaman berikut mengganti teks di kotak yang sama */
  const SL=.08;
  for(let i=0;i<PAGES.length;i++){const q=PAGES[i],p=q.p,nx=PAGES[i+1],pv=PAGES[i-1],a0=p.t-SL,cutNext=!!nx&&nx.p.t-SL<=p.out+.12,end=cutNext?nx.p.t-SL:p.out,
      swap=!!pv&&a0<=pv.p.out+.12;
    if(t<a0||t>=end){if(q.v){q.el.style.visibility='hidden';q.v=false;}continue;}
    q.v=true;const e=swap?1:E.outB(clamp((t-a0)/.16),2.2),fo=cutNext?1:clamp((end-t)/.08),fi=swap?1:Math.min(1,(t-a0)/.07);q.el.style.visibility='visible';q.el.style.opacity=(fi*fo).toFixed(3);
    q.el.style.transform=`translate(-50%,-50%) translateY(${f1((1-e)*20)}px) scale(${(.93+.07*e).toFixed(4)})`;
    q.spans.forEach((sp,j)=>{const w=q.ws[j],on=t>=w.t-.03,n2=q.ws[j+1],cur=on&&(n2?t<n2.t-.03:t<w.e+.3);const c='sw'+(on?' on':'')+(cur?' cur':'');if(sp.className!==c)sp.className=c;});}
}

/* ============================== kontrol: autoplay + loop; ?debug=1 scrub; ?clean=1 export; ?lang=en ============================== */
const q=new URLSearchParams(location.search),vo=$('#vo');let audioOn=false,hasVO=!!vo.getAttribute('src');
function fit(){const s=Math.min(innerWidth/W,innerHeight/H);$('#stage').style.transform=`translate(-50%,-50%) scale(${s})`;}
addEventListener('resize',fit);fit();
function start(){tl.play(0);if(hasVO){vo.currentTime=0;vo.play().then(()=>audioOn=true).catch(()=>{});}}
window.OPENER={W,H,DURATION:DUR,tl,ready:false,seek(t){tl.pause(t,false);render(t);},play:start};
Promise.all(['640 100px Fraunces','italic 600 100px Fraunces','800 72px Fraunces','800 64px "Plus Jakarta Sans"','700 40px "Plus Jakarta Sans"','600 40px "Plus Jakarta Sans"','700 60px Kalam','400 40px Kalam']
  .map(s=>document.fonts.load(s))).then(()=>document.fonts.ready).then(()=>{
  build();choreo();window.OPENER.sfx=SFX;
  tl.eventCallback('onComplete',()=>start());
  gsap.ticker.add(()=>{render(tl.time());if(audioOn&&!tl.paused()&&Math.abs(vo.currentTime-tl.time())>.12)vo.currentTime=tl.time();});
  tl.pause(0);render(0);window.OPENER.ready=true;
  addEventListener('keydown',e=>{if(/^[rR]$/.test(e.key))start();if(e.code==='Space'){e.preventDefault();if(tl.paused()){tl.play();if(hasVO)vo.play();}else{tl.pause();vo.pause();}}});
  if(q.has('debug')){const dbg=$('#dbg');dbg.style.display='flex';const sc=$('#dScrub'),ck=$('#dClock');let drag=false;
    gsap.ticker.add(()=>{if(!drag)sc.value=String(tl.time()/DUR*1000);ck.textContent=tl.time().toFixed(2)+'s';$('#dPlay').textContent=tl.paused()?'Play':'Pause';});
    sc.addEventListener('pointerdown',()=>{drag=true;tl.pause();vo.pause();});addEventListener('pointerup',()=>drag=false);
    sc.addEventListener('input',()=>{tl.pause();tl.time(sc.value/1000*DUR);render(tl.time());});$('#dPlay').onclick=()=>{if(tl.paused()){tl.play();if(hasVO){vo.currentTime=tl.time();vo.play();}}else{tl.pause();vo.pause();}};}
  if(q.has('clean'))return;
  if(!hasVO){start();return;}
  vo.play().then(()=>{audioOn=true;vo.currentTime=0;tl.play(0);}).catch(()=>{const go=()=>{removeEventListener('pointerdown',go);removeEventListener('keydown',go);start();};addEventListener('pointerdown',go);addEventListener('keydown',go);});
});
