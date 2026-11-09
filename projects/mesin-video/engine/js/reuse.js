/* Bagian yang dipakai ulang dari projects/daun-katuk-v2 (teruji): maskot, kamera, tween, tinta, penanda. */
/* ---- daun kecil (konfeti) & coretan spidol ---- */
const leafD=(L,w)=>`M0 0C${f1(L*.16)} ${f1(-w*.64)} ${f1(L*.6)} ${f1(-w*.62)} ${f1(L)} 0C${f1(L*.6)} ${f1(w*.62)} ${f1(L*.16)} ${f1(w*.64)} 0 0Z`;
function leafG(L,w,under=false){
  const b=under?PAL.under:PAL.leaf,h=under?PAL.under2:PAL.leaf2,mid=under?'#6C8C59':'#93C06A';
  let v='';for(let k=1;k<=5;k++){const x=L*(.11+k*.135);v+=`M${f1(x)} 0Q${f1(x+L*.06)} ${f1(-w*.17)} ${f1(x+L*.13)} ${f1(-w*.29)}M${f1(x)} 0Q${f1(x+L*.06)} ${f1(w*.17)} ${f1(x+L*.13)} ${f1(w*.29)}`;}
  return `<path d="${leafD(L,w)}" fill="${b}"/><path d="M0 0C${f1(L*.16)} ${f1(-w*.64)} ${f1(L*.6)} ${f1(-w*.62)} ${f1(L)} 0Q${f1(L*.5)} ${f1(-w*.05)} 0 0Z" fill="${h}"/>`+
    `<path d="${v}" stroke="${mid}" stroke-width="2.2" fill="none" opacity=".55" stroke-linecap="round"/>`+
    `<path d="M${f1(L*.02)} 0Q${f1(L*.5)} ${f1(-w*.05)} ${f1(L*.96)} 0" stroke="${mid}" stroke-width="3.4" fill="none" stroke-linecap="round"/>`+
    `<path d="${leafD(L,w)}" fill="none" stroke="${PAL.ink}" stroke-width="2.6" opacity=".5" transform="translate(3.5 2.5)"/>`;
}
function markerD(len,seed,k=1){const R=mulberry32(seed),N=40,top=[],bot=[],wob=Array.from({length:N+1},()=>R()-.5);
  for(let i=0;i<=N;i++){const t=i/N,x=t*len,mid=19-t*9+Math.sin(t*Math.PI*1.6+.4)*2.6+wob[i]*1.6,wb=14+Math.sin(t*Math.PI)*6-Math.max(0,t-.86)*46,w=Math.max(2.2,wb+wob[i]*3);
    top.push(`${f1(x)},${f1((mid-w/2)*k)}`);bot.push(`${f1(x)},${f1((mid+w/2)*k)}`);}
  return `M${top.join('L')}L${bot.reverse().join('L')}Z`;}


/* ---- maskot "Si Katuk" (SVG) ---- */
const BODY='M0 -360C128 -292 150 -140 0 -44C-150 -140 -128 -292 0 -360Z';
function mascotSVG(){
  const star=(x,y,r)=>`<path transform="translate(${x} ${y})" d="M0 ${-r}Q${r*.18} ${-r*.18} ${r} 0Q${r*.18} ${r*.18} 0 ${r}Q${-r*.18} ${r*.18} ${-r} 0Q${-r*.18} ${-r*.18} 0 ${-r}Z" fill="${PAL.marker}" stroke="${PAL.ink}" stroke-width="3"/>`;
  let veins='';for(let k=0;k<5;k++){const y=-310+k*44,w=70-k*4;veins+=`M0 ${y}Q${w*.5} ${y-10} ${w} ${y-26}M0 ${y}Q${-w*.5} ${y-10} ${-w} ${y-26}`;}
  return `<svg viewBox="-220 -440 440 460" width="440" height="460" style="overflow:visible;position:absolute;left:-220px;top:-440px">
  <ellipse cx="0" cy="4" rx="92" ry="15" fill="rgba(30,42,34,.20)"/>
  <g stroke="${PAL.stem}" stroke-width="12" stroke-linecap="round" fill="none"><path d="M-26 -50L-34 -8"/><path d="M26 -50L34 -8"/></g>
  <ellipse cx="-40" cy="-4" rx="25" ry="11" fill="${PAL.leaf}"/><ellipse cx="40" cy="-4" rx="25" ry="11" fill="${PAL.leaf}"/>
  <g id="mzB">
   <path id="mzArmL" stroke="${PAL.stem}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
   <path id="mzArmR" stroke="${PAL.stem}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
   <path d="${BODY}" fill="${PAL.leaf}"/>
   <path d="M0 -360C128 -292 150 -140 0 -44Q24 -200 0 -360Z" fill="${PAL.leaf2}"/>
   <path d="${veins}" stroke="#5F8F4E" stroke-width="3" fill="none" opacity=".45" stroke-linecap="round"/>
   <path d="M0 -356Q7 -300 0 -246" stroke="#93C06A" stroke-width="7" fill="none" stroke-linecap="round"/>
   <path d="M0 -360Q-18 -392 6 -404" stroke="${PAL.stem}" stroke-width="8" fill="none" stroke-linecap="round"/>
   <path d="${BODY}" fill="none" stroke="${PAL.ink}" stroke-width="3.5" opacity=".5" transform="translate(4 3)"/>
   <ellipse cx="-66" cy="-146" rx="19" ry="11" fill="${PAL.blush}" opacity=".75"/><ellipse cx="66" cy="-146" rx="19" ry="11" fill="${PAL.blush}" opacity=".75"/>
   <g id="mzEyeL" transform="translate(-40 -198)"><g class="eo"><ellipse rx="27" ry="32" fill="#FFFDF7" stroke="${PAL.ink}" stroke-width="3"/><g class="pu"><circle r="13" fill="${PAL.ink}"/><circle cx="5" cy="-5" r="4.5" fill="#fff"/></g></g><path class="ec" d="M-20 4Q0 -16 20 4" stroke="${PAL.ink}" stroke-width="7" fill="none" stroke-linecap="round"/></g>
   <g id="mzEyeR" transform="translate(40 -198)"><g class="eo"><ellipse rx="27" ry="32" fill="#FFFDF7" stroke="${PAL.ink}" stroke-width="3"/><g class="pu"><circle r="13" fill="${PAL.ink}"/><circle cx="5" cy="-5" r="4.5" fill="#fff"/></g></g><path class="ec" d="M-20 4Q0 -16 20 4" stroke="${PAL.ink}" stroke-width="7" fill="none" stroke-linecap="round"/></g>
   <path id="mzBrowL" d="M-58 -246L-22 -250" stroke="${PAL.ink}" stroke-width="8" stroke-linecap="round" fill="none"/>
   <path id="mzBrowR" d="M22 -250L58 -246" stroke="${PAL.ink}" stroke-width="8" stroke-linecap="round" fill="none"/>
   <path id="mzMouth" fill="#6E1F2A" stroke="${PAL.ink}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
   <g id="mzGlasses" opacity="0" stroke="${PAL.ink}" stroke-width="6" fill="rgba(255,255,255,.18)"><circle cx="-40" cy="-198" r="38"/><circle cx="40" cy="-198" r="38"/><path d="M-2 -204Q0 -212 2 -204" fill="none"/></g>
   <path id="mzSweat" opacity="0" d="M96 -276C104 -258 112 -246 112 -236A16 16 0 0 1 80 -236C80 -246 88 -258 96 -276Z" fill="#9CD3F0" stroke="${PAL.ink}" stroke-width="3"/>
   <g id="mzStars" opacity="0">${star(-150,-330,22)}${star(150,-350,16)}${star(162,-262,11)}</g>
  </g>
  <circle id="mzHandL" r="16" fill="${PAL.lit}" stroke="${PAL.ink}" stroke-width="3"/><circle id="mzHandR" r="16" fill="${PAL.lit}" stroke="${PAL.ink}" stroke-width="3"/>
 </svg>`;
}
/* kartu kuis A/B */
const sealSVG=()=>`<svg viewBox="0 0 120 120" width="120" height="120"><circle cx="60" cy="60" r="50" fill="${PAL.maroon}"/><circle cx="60" cy="60" r="38" fill="none" stroke="#B4505B" stroke-width="5"/><text x="60" y="84" text-anchor="middle" font-family="Fraunces" font-weight="800" font-size="70" fill="${PAL.cream}">!</text></svg>`;
const leafMini=(L=46,under=false)=>`<svg viewBox="-6 -24 ${L+16} 48" width="${L+16}" height="48" style="overflow:visible"><g>${leafG(L,L*.36,under)}</g></svg>`;
/* ---- penempatan elemen ---- */
function put(parent,html,{x=0,y=0,w,h,cls='ab o0',id,rot,z,sc}={}){const d=document.createElement('div');d.className=cls;if(id)d.id=id;d.style.left=x+'px';d.style.top=y+'px';
  if(w)d.style.width=w+'px';if(h)d.style.height=h+'px';if(z!=null)d.style.zIndex=z;
  if(rot||sc){const inn=document.createElement('div');if(rot)inn.style.rotate=rot+'deg';if(sc){inn.style.scale=sc+'';inn.style.transformOrigin='0 0';}inn.innerHTML=html;d.appendChild(inn);}else d.innerHTML=html;
  parent.appendChild(d);return d;}
function line(parent,html,{x,y,size,id,cls='',align='left',w}={}){const d=put(parent,'',{x,y,id,cls:'ab line ttl '+cls});d.style.fontSize=size+'px';if(w){d.style.width=w+'px';d.style.textAlign=align;}
  const tmp=document.createElement('div');tmp.innerHTML=html;
  tmp.childNodes.forEach(n=>{if(n.nodeType===3){n.textContent.split(/\s+/).filter(Boolean).forEach(t=>{const s=document.createElement('span');s.className='w';s.textContent=t;d.appendChild(s);});}
    else{const s=document.createElement('span');s.className='w';s.appendChild(n.cloneNode(true));d.appendChild(s);}});return d;}
function addMarker(hl,seed,k=1){const len=hl.offsetWidth*1.08+10,hh=f1(44*k),svg=`<svg class="mk" width="${f1(len)}" height="${hh}" viewBox="0 0 ${f1(len)} ${hh}"><defs><clipPath id="mc${seed}"><rect class="mkr" x="0" y="-20" width="0" height="${f1(80*k+40)}"/></clipPath></defs><path d="${markerD(len,seed,k)}" fill="${PAL.marker}" opacity=".92" clip-path="url(#mc${seed})"/></svg>`;
  hl.insertAdjacentHTML('beforeend',svg);return {rect:$('.mkr',hl),len};}

/* ---- timeline, kamera, tween bantu ---- */
const tl=gsap.timeline({paused:true});
const C={x:540,y:-1760,z:1};                       // kamera: fokus (koordinat dunia) + zoom
const FX={whipX:0,whipY:0,lensP:0,pulse:0};
function applyCam(t){const z=C.z*(1+.006*Math.sin(t*.9))*(1+FX.pulse);world.style.transform=`translate(${f1(540-C.x*z)}px,${f1(960-C.y*z)}px) scale(${z.toFixed(5)})`;}
const look=(at,x,y,z,dur=1,ease='power2.inOut')=>tl.to(C,{x,y,z,duration:dur,ease},at);
const camSet=(at,x,y,z)=>tl.set(C,{x,y,z},at);
const pw=(k,x,y)=>WP(k,x,y);

/* motion blur berarah (bang-motion): filter SVG per tween, dilepas saat selesai */
const defs=$('#filters defs');let fc=0;
function makeBlur(){const id='mb'+(fc++),NS='http://www.w3.org/2000/svg',fl=document.createElementNS(NS,'filter');fl.id=id;
  fl.setAttribute('x','-60%');fl.setAttribute('y','-60%');fl.setAttribute('width','220%');fl.setAttribute('height','220%');
  const g=document.createElementNS(NS,'feGaussianBlur');g.setAttribute('stdDeviation','0 0');fl.appendChild(g);defs.appendChild(fl);return{url:`url(#${id})`,node:g};}
function blurTween(targets,at,from,to,dur,{ease='power3.out',ax=1,ay=.08}={}){const b=makeBlur(),o={v:from};tl.set(targets,{filter:b.url},at);
  tl.fromTo(o,{v:from},{v:to,duration:dur,ease,immediateRender:false,onUpdate(){b.node.setAttribute('stdDeviation',`${(o.v*ax).toFixed(2)} ${(o.v*ay).toFixed(2)}`);}},at);tl.set(targets,{filter:'none'},at+dur);}
const VERT={ax:.08,ay:1},HORZ={ax:1,ay:.08};
const words=el=>$$('.w',el);
function say(sel,at,{dur=.6,st=.09,mode='up'}={}){const el=$(sel),ws=words(el);tl.set(el,{opacity:1},at);
  if(mode==='scale')tl.fromTo(ws,{opacity:0,scale:.6,rotate:-4},{opacity:1,scale:1,rotate:0,duration:dur,ease:'back.out(1.7)',stagger:st,immediateRender:false},at);
  else if(mode==='left'){tl.fromTo(ws,{opacity:0,xPercent:-45},{opacity:1,xPercent:0,duration:dur,ease:'power4.out',stagger:st,immediateRender:false},at);blurTween(el,at,40,0,dur+st*ws.length,{ease:'power4.out'});return;}
  else if(mode==='right'){tl.fromTo(ws,{opacity:0,xPercent:45},{opacity:1,xPercent:0,duration:dur,ease:'power4.out',stagger:st,immediateRender:false},at);blurTween(el,at,40,0,dur+st*ws.length,{ease:'power4.out'});return;}
  else tl.fromTo(ws,{opacity:0,yPercent:60,scaleY:1.3},{opacity:1,yPercent:0,scaleY:1,duration:dur,ease:'power4.out',stagger:st,immediateRender:false},at);
  blurTween(el,at,24,0,dur+st*ws.length,VERT);}
function unsay(sel,at,{dur=.32}={}){const el=$(sel),ws=words(el);tl.to(ws,{opacity:0,yPercent:-55,duration:dur,ease:'power2.in',stagger:.025},at);blurTween(el,at,0,30,dur+.12,{ease:'power2.in',...VERT});}
/* paper-title-card (video-shotcraft): per kata scale 1.28->1 + blur 7->0, 9f, jeda 4f, bezier(.2,.75,.3,1) */
const PTC=bez(.2,.75,.3,1);
function press(sel,at){const el=$(sel),ws=words(el);tl.set(el,{opacity:1},at);
  ws.forEach((w,i)=>tl.fromTo(w,{opacity:0,scale:1.28,filter:'blur(7px)'},{opacity:1,scale:1,filter:'blur(0px)',duration:9/FPS,ease:PTC,immediateRender:false},at+(4+i*4)/FPS));}
function fly(sel,at,{from={y:420,rotate:8,scale:.9},dur=.85,ease='power4.out'}={}){const el=$(sel);
  tl.fromTo(el,{opacity:0,x:0,y:0,rotate:0,scale:1,...from},{opacity:1,x:0,y:0,rotate:0,scale:1,duration:dur,ease,immediateRender:false},at);
  blurTween(el,at,30,0,dur*.7,Math.abs(from.x||0)>Math.abs(from.y||0)?HORZ:VERT);}
function pop(sel,at,{dur=.55,from=.3,ease='back.out(2)',rot=-8}={}){tl.fromTo($(sel),{opacity:0,scale:from,rotate:rot},{opacity:1,scale:1,rotate:0,duration:dur,ease,immediateRender:false},at);}
function out(sels,at,{to={y:-300,rotate:-6},dur=.38,st=.04}={}){const els=sels.map(s=>$(s));tl.to(els,{opacity:0,...to,duration:dur,ease:'power2.in',stagger:st},at);blurTween(els,at,0,36,dur+st*els.length,{ease:'power2.in',...VERT});}
function label(sel,at,{dur=.45}={}){tl.fromTo($(sel),{opacity:0,y:18},{opacity:1,y:0,duration:dur,ease:'power3.out',immediateRender:false},at);}
function drawPaths(sel,at,dur=.45,st=.12){$$(sel+' .dr').forEach((p,i)=>tl.fromTo(p,{strokeDashoffset:1},{strokeDashoffset:0,duration:dur,ease:'power2.inOut',immediateRender:false},at+i*st));
  $$(sel+' .tx').forEach(p=>tl.fromTo(p,{opacity:0,scale:.5,transformOrigin:'50% 50%'},{opacity:1,scale:1,duration:.4,ease:'back.out(2.2)',immediateRender:false},at+dur+.05));}
function demote(sel,at,{s=.5,y=-60,x=0}={}){tl.to($(sel),{scale:s,x,y,transformOrigin:'0% 0%',duration:.55,ease:'power3.inOut'},at);}


/* ---- jadwal maskot ---- */
const SCH={};
const MPOS=[];   // posisi maskot: {t, x, y, s, dur}
const MEXP=[];   // ekspresi maskot: {t, e, p}  e = ekspresi wajah, p = pose lengan
const mpos=(t,x,y,s,dur=.5,arc=110)=>MPOS.push({t,x,y,s,dur,arc});
const MHIDE=[];   // selang [t0,t1] maskot disembunyikan (kamera menyelam)
const mexp=(t,e,p='idle')=>MEXP.push({t,e,p});
const SPOT={BC:[540,1395,.52],BR:[930,1382,.5],TR:[944,470,.44],BL:[170,1385,.52]};
const wiggle=(sel,at,amp=6,dur=.5)=>tl.fromTo($(sel),{rotate:0},{rotate:amp,duration:dur/4,ease:'sine.inOut',yoyo:true,repeat:3,immediateRender:false},at);
/* ---- bantu render ---- */
const fr=t=>t*FPS;
function flight(t,{t0,dur,from,to},arc=-260){
  const p=clamp((t-t0)/dur),e=E.outC(p),[sx,sy,sa]=from,[ex,ey,ea]=to;
  const mx=(sx+ex)/2,my=(sy+ey)/2+arc,x=(1-e)**2*sx+2*(1-e)*e*mx+e*e*ex,y=(1-e)**2*sy+2*(1-e)*e*my+e*e*ey;
  const a=lerp(sa,ea,e)+Math.sin(p*Math.PI*3.2)*(1-p)*38,s=1+Math.sin(p*Math.PI)*.16;return{x,y,a,s,p};}
function marker(m,t,t0){const p=clamp((t-t0)/(10/FPS)),e=1-Math.pow(1-p,2.2);m.rect.setAttribute('width',f1(e*(m.len+6)));}
function inkPath(f,cx=380,cy=330){/* ink-bleed-reveal: lingkaran + tepi berserabut; r 0->Rmax out(quad), wobble +-8% sin(.32f) meredam di 20f akhir */
  const R=lerp(0,2350,E.outQ(clamp(f/78)))*(1+.08*Math.sin(f*.32)*(1-clamp((f-58)/20))),A=lerp(30,80,clamp(f/78)),N=180;
  if(R<1)return 'path("M0 0Z")';let d='';
  for(let i=0;i<N;i++){const th=i/N*6.2832;let n=0;for(let k=0;k<INKH.length;k++){const h=INKH[k];n+=h.a*Math.sin(h.k*th+h.p+f*h.w);}
    for(const s of INKS)n+=s.a*Math.exp(-Math.pow((th-s.th)/.035,2));const r=Math.max(0,R+A*n);d+=(i?'L':'M')+f1(cx+Math.cos(th)*r)+' '+f1(cy+Math.sin(th)*r);}
  return `path("${d}Z")`;}
const INKH=(()=>{const R=mulberry32(7),a=[];for(let k=3;k<=46;k+=1)a.push({k,a:(R()-.2)*.9/Math.pow(k,.65),p:R()*6.283,w:(R()-.5)*.02});return a;})();
const INKS=(()=>{const R=mulberry32(19),a=[];for(let i=0;i<9;i++)a.push({th:R()*6.283,a:.6+R()*.9});return a;})();
/* ---- maskot: posisi, ekspresi, pose (IK), lip-sync ---- */
/* ============================== maskot: posisi (hop), ekspresi, pose lengan (IK), lip-sync ============================== */
const EXPR={
  happy:{b:[-6,0,6,0],m:'smile',pu:[0,0]}, think:{b:[-14,-10,4,2],m:'flat',pu:[-7,-9]},
  nervous:{b:[16,-4,-16,-4],m:'wavy',pu:[0,5],sweat:1}, excited:{b:[-10,-14,10,-14],m:'open',pu:[0,-2],stars:1},
  proud:{b:[-8,-6,8,-6],m:'grin',pu:[0,0],stars:1}, sad:{b:[18,0,-18,0],m:'frown',pu:[0,9]},
  whisper:{b:[-4,0,14,-6],m:'o',pu:[10,0]}, surprised:{b:[-10,-18,10,-18],m:'O',pu:[0,0]},
  laugh:{b:[-8,-10,8,-10],m:'open',closed:[1,1]}, smart:{b:[-6,-4,10,-8],m:'smile',pu:[0,0],glasses:1},
  mischief:{b:[-14,2,10,-8],m:'smirk',pu:[8,0]}, wink:{b:[-6,-4,6,2],m:'grin',closed:[0,1]},
  shock:{b:[-12,-20,12,-20],m:'O',pu:[0,0],sweat:1}, serious:{b:[-12,6,12,6],m:'flat',pu:[0,0]}};
const POSE={idle:{L:[-122,-74],R:[122,-74]},think:{L:[-120,-80],R:[22,-118]},nervous:{L:[-26,-96],R:[26,-96]},excited:{L:[-150,-292],R:[150,-292]},
  flex:{L:[-168,-226],R:[168,-226]},sad:{L:[-104,-60],R:[104,-60]},whisper:{L:[-120,-80],R:[58,-128]},surprised:{L:[-124,-236],R:[124,-236]},
  laugh:{L:[-60,-96],R:[60,-96]},point:{L:[-122,-74],R:[200,-210]},thumbs:{L:[-122,-74],R:[150,-236]},present:{L:[-122,-74],R:[186,-140]},
  shock:{L:[-80,-150],R:[80,-150]},wag:{L:[-122,-74],R:[128,-262]},wave:{L:[-122,-74],R:[150,-292]}};
const ell=(cx,cy,rx,ry)=>`M${f1(cx-rx)} ${f1(cy)}A${f1(rx)} ${f1(ry)} 0 1 0 ${f1(cx+rx)} ${f1(cy)}A${f1(rx)} ${f1(ry)} 0 1 0 ${f1(cx-rx)} ${f1(cy)}Z`;
function mouthPath(kind,m){const y0=-140;
  if(['smile','grin','flat','frown','smirk'].includes(kind)&&m>.06){const w=26+8*m+(kind==='grin'?6:0),h=8+40*m;
    return [`M${f1(-w)} ${y0}Q0 ${y0-6} ${f1(w)} ${y0}Q${f1(w*.8)} ${f1(y0+h)} 0 ${f1(y0+h)}Q${f1(-w*.8)} ${f1(y0+h)} ${f1(-w)} ${y0}Z`,1];}
  switch(kind){
    case 'open':{const w=34+6*m,h=26+30*m;return [`M${f1(-w)} ${y0-4}Q0 ${y0-12} ${f1(w)} ${y0-4}Q${f1(w*.85)} ${f1(y0+h)} 0 ${f1(y0+h)}Q${f1(-w*.85)} ${f1(y0+h)} ${f1(-w)} ${y0-4}Z`,1];}
    case 'O':return [ell(0,y0+8,14+8*m,18+16*m),1];
    case 'o':return [ell(0,y0+4,9,11+5*m),1];
    case 'grin':return [`M-36 ${y0-8}Q0 ${y0+30} 36 ${y0-8}`,0];
    case 'smirk':return [`M-26 ${y0+4}Q4 ${y0+16} 32 ${y0-12}`,0];
    case 'flat':return [`M-24 ${y0+2}L24 ${y0+2}`,0];
    case 'frown':return [`M-26 ${y0+12}Q0 ${y0-12} 26 ${y0+12}`,0];
    case 'wavy':return [`M-30 ${y0+2}q7.5 -9 15 0t15 0t15 0t15 0`,0];
    default:return [`M-30 ${y0-6}Q0 ${y0+22} 30 ${y0-6}`,0];}}
function ik(S,H,side){const L1=64,L2=60,dx=H[0]-S[0],dy=H[1]-S[1];let d=Math.hypot(dx,dy);d=clamp(d,Math.abs(L1-L2)+2,L1+L2-2);
  const a=Math.atan2(dy,dx),b=Math.acos(clamp((L1*L1+d*d-L2*L2)/(2*L1*d),-1,1))*side,E=[S[0]+Math.cos(a+b)*L1,S[1]+Math.sin(a+b)*L1];
  const Hh=[S[0]+Math.cos(a)*d,S[1]+Math.sin(a)*d];return [E,Hh];}
const MZ={};let mzLast={};
function setA(el,k,v){if(mzLast[el.id+k]!==v){el.setAttribute(k,v);mzLast[el.id+k]=v;}}
function renderMascot(t){
  if(!MZ.root){MZ.root=$('#mascot');['mzB','mzArmL','mzArmR','mzHandL','mzHandR','mzEyeL','mzEyeR','mzBrowL','mzBrowR','mzMouth','mzGlasses','mzSweat','mzStars'].forEach(k=>MZ[k]=$('#'+k));
    MZ.eo=[$('#mzEyeL .eo'),$('#mzEyeR .eo')];MZ.ec=[$('#mzEyeL .ec'),$('#mzEyeR .ec')];MZ.pu=[$('#mzEyeL .pu'),$('#mzEyeR .pu')];}
  if(!MPOS.length||t<MPOS[0].t){MZ.root.style.opacity=0;return;}
  let i=0;while(i+1<MPOS.length&&MPOS[i+1].t<=t)i++;const cur=MPOS[i],prev=i>0?MPOS[i-1]:null,p=clamp((t-cur.t)/cur.dur),e=E.ioC(p);
  let x,y,s;
  if(!prev){const q=E.outB(p,1.6);x=cur.x;y=cur.y+(1-clamp(q,0,1.2))*260;s=cur.s*Math.max(.01,Math.min(1.1,q));}
  else{const moved=prev.x!==cur.x||prev.y!==cur.y;x=lerp(prev.x,cur.x,e);y=lerp(prev.y,cur.y,e)-(moved?Math.sin(p*Math.PI)*cur.arc:0);s=lerp(prev.s,cur.s,e);}
  let k=0;while(k+1<MEXP.length&&MEXP[k+1].t<=t)k++;const X=MEXP[k],ex=EXPR[X.e]||EXPR.happy,since=t-X.t;
  const pop=Math.max(0,1-since/.22),sq=.09*pop*Math.sin(Math.min(1,since/.22)*Math.PI*1.5+.5);
  let bob=Math.sin(t*3.1)*5,sx=0;
  if(X.e==='laugh')bob=-Math.abs(Math.sin(t*9))*20;if(X.e==='excited'&&since<1.2)bob=-Math.abs(Math.sin(t*7.5))*26*(1-since/1.2)+bob;
  if(X.e==='shock'&&since<.55)sx=Math.sin(t*55)*5*(1-since/.55);
  let hid=0;for(const [h0,h1] of MHIDE)hid=Math.max(hid,Math.min(clamp((t-h0)/.15),clamp((h1-t)/.15)));
  MZ.root.style.opacity=(1-hid).toFixed(3);MZ.root.style.transform=`translate(${f1(x+sx)}px,${f1(y)}px) scale(${s.toFixed(4)})`;
  setA(MZ.mzB,'transform',`translate(0 ${f1(bob)}) translate(0 -44) scale(${(1+sq).toFixed(3)} ${(1-sq).toFixed(3)}) translate(0 44)`);
  /* mata: kedip deterministik, pupil, mata tertutup (tertawa/kedip) */
  const blink=((t*1000+400)%3100)<110,cl=ex.closed||[0,0];
  [0,1].forEach(j=>{const closed=cl[j];setA(MZ.eo[j],'opacity',closed?0:1);setA(MZ.ec[j],'opacity',closed?1:0);
    setA(MZ.eo[j],'transform',blink&&!closed?'scale(1 .1)':'scale(1 1)');const pu=(typeof mascotLook==='function'&&mascotLook(t))||ex.pu||[0,0];
    setA(MZ.pu[j],'transform',`translate(${f1(pu[0]+Math.sin(t*.8)*1.5)} ${f1(pu[1]+Math.sin(t*.6)*1.5)})`);});
  const bb=ex.b;setA(MZ.mzBrowL,'transform',`translate(0 ${bb[1]}) rotate(${bb[0]} -40 -248)`);setA(MZ.mzBrowR,'transform',`translate(0 ${bb[3]}) rotate(${bb[2]} 40 -248)`);
  const m=(TL.mouth&&TL.mouth[Math.floor(t*30)])||0,[md,mf]=mouthPath(ex.m,m);setA(MZ.mzMouth,'d',md);setA(MZ.mzMouth,'fill',mf?'#6E1F2A':'none');
  setA(MZ.mzGlasses,'opacity',ex.glasses?1:0);setA(MZ.mzSweat,'opacity',ex.sweat?1:0);setA(MZ.mzStars,'opacity',ex.stars?(.7+.3*Math.sin(t*12)).toFixed(2):0);
  if(ex.sweat)setA(MZ.mzSweat,'transform',`translate(0 ${f1((t*60)%24)})`);
  /* lengan: IK dua ruas dari bahu ke target tangan (pose + goyangan) */
  const P=POSE[X.p]||POSE.idle;let Lh=[...P.L],Rh=[...P.R];
  if(X.p==='wave'){Rh[0]+=Math.sin(t*14)*26;Rh[1]+=Math.cos(t*14)*8;}
  if(X.p==='wag'){Rh[0]+=Math.sin(t*16)*16;}
  if(X.p==='excited'||X.p==='flex'){Lh[1]+=Math.sin(t*9)*10;Rh[1]+=Math.sin(t*9+1)*10;}
  if(X.p==='laugh'){Lh[1]+=Math.abs(Math.sin(t*9))*-12;Rh[1]+=Math.abs(Math.sin(t*9))*-12;}
  if(X.p==='idle'){Lh[1]+=Math.sin(t*2.2)*4;Rh[1]+=Math.sin(t*2.2+1.3)*4;}
  const by=bob;[[MZ.mzArmL,MZ.mzHandL,[-96,-150+by],[Lh[0],Lh[1]+by],1],[MZ.mzArmR,MZ.mzHandR,[96,-150+by],[Rh[0],Rh[1]+by],-1]].forEach(([arm,hand,S,H,side])=>{
    const [E2,Hh]=ik(S,H,side);setA(arm,'d',`M${f1(S[0])} ${f1(S[1])}L${f1(E2[0])} ${f1(E2[1])}L${f1(Hh[0])} ${f1(Hh[1])}`);setA(hand,'cx',f1(Hh[0]));setA(hand,'cy',f1(Hh[1]));});
}

/* rolet kuis: 0 = A, 1 = B, -1 = tidak ada sorotan */
