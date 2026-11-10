/* ============================== FORMAT FAKTA: penjelasan santai ala catatan dokumenter ==============================
   Kertas tua, ilustrasi di tengah, kartu catatan (kicker + angka) bertumpuk di kiri atas tepat saat disebut,
   caption karaoke besar di tengah bawah, tempo santai (jeda wajar, tanpa percepatan), perpindahan adegan dengan
   geser kamera pelan, dan penutup berupa pertanyaan untuk penonton. Isyarat: {b0}.. baris pembuka, {sorot},
   {k0}.. kartu, {kutip} kutipan analogi, {tanya} pertanyaan, {pilih} pilihan jawaban. */

/* noda cat air + coretan tangan tipis di belakang ilustrasi (gaya ilustrasi editorial) */
const WASH=['#E6CC97','#CFDDB8','#EFC3A8','#C9D8E2','#E9D4B0'];
function blobD(cx,cy,r,R,n=14,j=.1){const pts=[];for(let i=0;i<n;i++){const a=i/n*6.2832,w=r*(1+(R()-.5)*2*j);pts.push([cx+Math.cos(a)*w,cy+Math.sin(a)*w*.92]);}
  let d=`M${f1((pts[0][0]+pts[1][0])/2)} ${f1((pts[0][1]+pts[1][1])/2)}`;
  for(let i=1;i<=n;i++){const p=pts[i%n],q=pts[(i+1)%n];d+=`Q${f1(p[0])} ${f1(p[1])} ${f1((p[0]+q[0])/2)} ${f1((p[1]+q[1])/2)}`;}return d+'Z';}
function doodleSVG(size,seed){const R=mulberry32(seed),c=size/2,r=size*.43;let d='',p='';
  d+=`<path d="${blobD(c,c,r*.98,R,13,.09)}" fill="${WASH[seed%WASH.length]}" opacity=".75"/>`;
  d+=`<path d="${blobD(c+r*.08,c-r*.05,r*.78,R,11,.12)}" fill="${WASH[(seed+2)%WASH.length]}" opacity=".35"/>`;
  for(let a=0;a<=380;a+=10){const t=a*Math.PI/180,w=r*(1.04+(R()-.5)*.05);p+=(a?'L':'M')+f1(c+Math.cos(t)*w)+' '+f1(c+Math.sin(t)*w*.9);}
  d+=`<path d="${p}" stroke="${PAL.ink}" stroke-width="3" fill="none" opacity=".2" stroke-linejoin="round"/>`;
  for(let i=0;i<10;i++){const a=R()*6.283,rr=r*(1.1+R()*.18),x=c+Math.cos(a)*rr,y=c+Math.sin(a)*rr*.9;
    d+=R()<.5?`<path d="M${f1(x-9)} ${f1(y)}L${f1(x+9)} ${f1(y)}M${f1(x)} ${f1(y-9)}L${f1(x)} ${f1(y+9)}" stroke="${PAL.ink}" stroke-width="3" opacity=".24" stroke-linecap="round"/>`
             :`<circle cx="${f1(x)}" cy="${f1(y)}" r="${f1(3+R()*4)}" fill="${PAL.ink}" opacity=".18"/>`;}
  return `<svg class="ab" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="left:0;top:0;overflow:visible">${d}</svg>`;}
/* ilustrasi: gambar unggahan ({"gambar": "<aset>"}) atau komposisi ikon ({"ikon": [utama, satelit..]}) */
function ilustrasiHTML(il,size,seed=5){il=il||{};
  if(il.gambar&&(TL.images||{})[il.gambar])return `<div class="ilus img" style="width:${size}px;height:${size}px">${doodleSVG(size,seed)}<img src="${TL.images[il.gambar]}" alt=""></div>`;
  const ik=(il.ikon||[]).slice(0,4);if(!ik.length)return '';
  const sat=[[-.35,.31,.30,-10],[.36,-.30,.27,9],[.34,.34,.22,14]];
  let h=`<div class="ilus" style="width:${size}px;height:${size}px">${doodleSVG(size,seed)}<div class="ilm">${icon(ik[0],Math.round(size*.6),'flat')}</div>`;
  ik.slice(1).forEach((n,i)=>{const [dx,dy,sc,r]=sat[i],w=Math.round(size*sc);
    h+=`<div class="ils" style="left:${f1(size/2+dx*size-w/2)}px;top:${f1(size/2+dy*size-w/2)}px;rotate:${r}deg">${icon(n,w,'flat')}</div>`;});
  return h+'</div>';}
/* kartu catatan: {kicker, nilai, warna:'merah'} atau catatan pendek {teks} */
function dcardHTML(k,i){const red=k.warna==='merah';
  if(k.teks)return `<div class="dcard note${red?' red':''}" style="rotate:${i%2?1.2:-1.2}deg"><div class="dv sm">${esc(nb(k.teks))}</div></div>`;
  return `<div class="dcard${red?' red':''}" style="rotate:${i%2?.8:-.8}deg">${k.kicker?`<div class="dk">${esc(k.kicker)}</div>`:''}<div class="dv">${esc(nb(k.nilai||''))}</div></div>`;}
function cardColumn(s,A,cards,y0=150){const col=put(A,'',{x:60,y:y0,cls:'ab',id:sid(s,'col'),z:4});
  col.style.cssText+=';display:flex;flex-direction:column;align-items:flex-start;gap:20px;width:940px';
  cards.forEach((k,i)=>{const d=document.createElement('div');d.id=sid(s,'kc'+i);d.innerHTML=dcardHTML(k,i);d.style.opacity=0;col.appendChild(d);});return col;}
function cardsIn(s,cards){const n=cards.length;const ts=cards.map((k,i)=>itemT(s,'k',i,n));
  ts.forEach((t,i)=>{tl.fromTo('#'+sid(s,'kc'+i),{opacity:0,x:-90,rotate:i%2?4:-4,scale:.94},{opacity:1,x:0,rotate:0,scale:1,duration:.5,ease:'back.out(1.4)',immediateRender:false},t-.12);
    pulse($('#'+sid(s,'kc'+i)+' .dv'),t+.6,(i+1<n?ts[i+1]:s.end)-.3,.035);});return ts;}
/* ilustrasi besar di bawah tumpukan kartu, alasnya tepat di atas caption; boleh sedikit tertutup kartu terbawah
   (kolase editorial). Ukuran: sisa ruang + 60 px, dibatasi [420, max]. */
const CAP_TOP=1330,IL_FOOT=1350;
function ilusFit(s,A,il,top,max,seed){const size=Math.round(clamp(IL_FOOT-top+60,420,max));
  return put(A,ilustrasiHTML(il,size,seed),{x:Math.round(540-size/2),y:IL_FOOT-size,id:sid(s,'il'),cls:'ab o0',z:1});}
const kenBurns=s=>tl.to(C,{z:1.035,duration:Math.max(1,s.end-s.cut-1),ease:'sine.inOut'},s.cut+.45);
const ilusIn=(s,t)=>tl.fromTo('#'+sid(s,'il'),{opacity:0,scale:.82,rotate:-4},{opacity:1,scale:1,rotate:0,duration:.8,ease:'back.out(1.5)',immediateRender:false},t);

/* ---------- PEMBUKA: kalimat pembuka besar di atas ilustrasi yang digelapkan + angka sorotan ---------- */
SCENES.pembuka={
  build(s){const P=s.param,A=s.el=areaEl(s);
    put(A,ilustrasiHTML(P.ilustrasi,780,3),{x:150,y:700,id:sid(s,'il'),cls:'ab',z:1});
    put(A,'<div class="veil"></div>',{x:0,y:0,cls:'ab',id:sid(s,'veil'),z:2});
    if(P.kicker)put(A,`<div class="kick">${esc(P.kicker)}</div>`,{x:0,y:300,w:1080,id:sid(s,'kick'),z:3});
    const lines=Array.isArray(P.judul)?P.judul:[P.judul];
    const box=put(A,'',{x:60,y:380,w:960,cls:'ab',id:sid(s,'lines'),z:3});box.style.cssText+=';display:flex;flex-direction:column;align-items:center;gap:4px';
    lines.forEach((l,i)=>{const d=document.createElement('div');d.className='hl1';d.id=sid(s,'l'+i);d.textContent=nb(l);d.style.opacity=0;box.appendChild(d);});
    if(P.sorot){const so=put(A,`<div class="sorot">${esc(nb(P.sorot))}</div>`,{x:0,y:0,id:sid(s,'sorot'),z:3});
      so.style.left=f1(540-so.offsetWidth/2)+'px';so.style.top=f1(380+box.offsetHeight+40)+'px';}},
  choreo(s){const P=s.param,c=s.cut,lines=Array.isArray(P.judul)?P.judul:[P.judul];
    if(s.i===0){camSet(c,s.cx,s.cy,1.05);tl.to(C,{z:1,duration:Math.max(1,s.end-c),ease:'sine.inOut'},c);}else enter(s);
    tl.fromTo('#'+sid(s,'il'),{opacity:.55,scale:.94},{opacity:1,scale:1,duration:1.4,ease:'power2.out',immediateRender:true},c);
    if(S$(s,'kick'))label('#'+sid(s,'kick'),c+.1);
    s.tb=lines.map((l,i)=>cue(s,'b'+i,lerp(s.speechStart,s.speechEnd-.8,i/lines.length)));
    s.tb.forEach((t,i)=>tl.fromTo('#'+sid(s,'l'+i),{opacity:0,y:30,scale:1.08},{opacity:1,y:0,scale:1,duration:.45,ease:'back.out(1.8)',immediateRender:false},t-.06));
    if(S$(s,'sorot')){s.ts=cue(s,'sorot',s.tb[s.tb.length-1]+.8);
      tl.fromTo('#'+sid(s,'sorot'),{opacity:0,scale:2,rotate:-8},{opacity:1,scale:1,rotate:-2,duration:.22,ease:'power3.in',immediateRender:false},s.ts-.12);
      pulse(S$(s,'sorot'),s.ts+.4,s.end-.4,.04);}
    leave(s,['lines','sorot','kick']);if(s.next)tl.to('#'+sid(s,'veil'),{opacity:0,duration:.6,ease:'sine.inOut'},s.end-.7);},
  sfx(s){if(S$(s,'kick'))sfx(s.cut+.1,'paper/paper-slide',.16,{max:.5,note:'kicker'});
    s.tb.forEach((t,i)=>sfx(t-.06,i%2?'transition/swoosh-quick':'impact/hit-weak',.22,{note:'baris pembuka '+(i+1)}));
    if(s.ts!=null)sfx(s.ts+.1,'impact/hit-blow',.3,{note:'angka sorotan'});}
};

/* ---------- CATATAN: kartu kicker + angka muncul bertumpuk saat disebut, ilustrasi di tengah ---------- */
SCENES.catatan={
  build(s){const P=s.param,A=s.el=areaEl(s);
    cardColumn(s,A,P.kartu||[]);
    ilusFit(s,A,P.ilustrasi,150+S$(s,'col').offsetHeight+40,740,7+s.i);},
  choreo(s){enter(s);ilusIn(s,s.cut+.1);s.tc=cardsIn(s,s.param.kartu||[]);kenBurns(s);
    pulse($('#'+sid(s,'il')+' .ilm'),s.cut+1,s.end-.4,.025);},
  sfx(s){sfx(s.cut+.1,'light/sparkle-touch',.1,{max:.7,note:'ilustrasi'});
    s.tc.forEach((t,i)=>sfx(t-.12,i%2?'paper/paper-move-quick':'paper/paper-slide',.22,{max:.6,note:'kartu '+(i+1)}));}
};

/* ---------- IBARAT: analogi sehari-hari dalam kartu kutipan + catatan pendek ---------- */
SCENES.ibarat={
  build(s){const P=s.param,A=s.el=areaEl(s);
    put(A,`<div class="quote">“${esc(nb(P.kutipan))}”</div>`,{x:60,y:150,w:960,id:sid(s,'q'),z:4});
    const qh=S$(s,'q').offsetHeight;
    cardColumn(s,A,P.kartu||[],150+qh+34);
    ilusFit(s,A,P.ilustrasi,150+qh+34+S$(s,'col').offsetHeight+40,700,11);},
  choreo(s){enter(s);const c=s.cut;s.tq=cue(s,'kutip',s.speechStart+.1);
    tl.fromTo('#'+sid(s,'q'),{opacity:0,y:-40,rotate:-6,scale:.92},{opacity:1,y:0,rotate:0,scale:1,duration:.6,ease:'back.out(1.5)',immediateRender:false},s.tq-.15);
    ilusIn(s,s.tq+.35);s.tc=cardsIn(s,s.param.kartu||[]);kenBurns(s);
    pulse($('#'+sid(s,'il')+' .ilm'),s.tq+1.2,s.end-.4,.03);},
  sfx(s){sfx(s.tq-.15,'paper/paper-page-turn',.26,{note:'kutipan analogi'});
    s.tc.forEach((t,i)=>sfx(t-.12,'paper/paper-slice-quick',.2,{note:'catatan '+(i+1)}));}
};

/* ---------- TANYA: pertanyaan untuk penonton + dua pilihan + ajakan berkomentar + sumber ---------- */
SCENES.tanya={
  build(s){const P=s.param,A=s.el=areaEl(s),cr=TL.meta||{},nk=(P.kartu||[]).length;
    const col=cardColumn(s,A,P.kartu||[],150);
    const q=put(A,`<div class="qcard2">${esc(nb(P.pertanyaan))}</div>`,{x:60,y:0,w:960,id:sid(s,'q'),z:4});
    const picks=(P.pilihan||[]).slice(0,2).map((p,i)=>put(A,`<div class="pick ${i?'no':'ok'}">${icon(i?'cross-mark':'check-mark-button',104,'flat')}<div>${esc(nb(p))}</div></div>`,
      {x:i?566:114,y:0,id:sid(s,'p'+i),rot:i?3:-3,z:4}));
    const aj=put(A,`<div style="display:flex;align-items:center;justify-content:center;gap:16px;width:1080px">${icon('speech-balloon',84,'flat')}<span class="hand" style="font-size:64px;white-space:nowrap">${esc(P.ajakan||TX.komentar)}</span></div>`,{x:0,y:0,id:sid(s,'aj'),z:4});
    const ft=put(A,`<div class="lbl foot">${TX.sumber}: ${esc((cr.sumber||[]).join('; '))}. ${TX.disclaimer} ${cr.elevenlabs?TX.suara:''}</div>`,{x:90,y:0,w:900,id:sid(s,'foot'),z:4});
    const top=150+(nk?col.offsetHeight:0),hs=[q.offsetHeight,picks.length?300:0,aj.offsetHeight,ft.offsetHeight];
    const gap=Math.min(110,Math.max(30,(CAP_TOP-20-top-hs.reduce((a,b)=>a+b,0))/3.4));
    let y=top+(nk?gap:0);q.style.top=y+'px';y+=hs[0]+gap;
    picks.forEach(el=>el.style.top=y+'px');if(picks.length)y+=hs[1]+gap;
    aj.style.top=y+'px';y+=hs[2]+gap*.4;ft.style.top=y+'px';},
  choreo(s){enter(s);const P=s.param,c=s.cut;s.tc=cardsIn(s,P.kartu||[]);
    s.tq=cue(s,'tanya',s.speechStart+(s.speechEnd-s.speechStart)*.4);s.tp=cue(s,'pilih',s.tq+1.2);
    tl.fromTo('#'+sid(s,'q'),{opacity:0,scale:.6,rotate:-4},{opacity:1,scale:1,rotate:0,duration:.5,ease:'back.out(2)',immediateRender:false},s.tq-.1);
    (P.pilihan||[]).slice(0,2).forEach((p,i)=>{pop('#'+sid(s,'p'+i),s.tp+i*.22,{dur:.5,from:.3,rot:i?12:-12});pulse(S$(s,'p'+i).firstElementChild,s.tp+.8+i*T,DUR-.3,.05);});
    s.ta=Math.max(s.tp+.9,s.speechEnd-.9);label('#'+sid(s,'aj'),s.ta);label('#'+sid(s,'foot'),s.ta+.35);
    kenBurns(s);},
  sfx(s){sfx(s.tq-.1,'transition/swoosh-quick',.24,{note:'pertanyaan'});
    (s.param.pilihan||[]).slice(0,2).forEach((p,i)=>sfx(s.tp+i*.22,i?'ui/switch-tap':'ui/switch-click-quick',.32,{max:.25,note:'pilihan '+(i+1)}));
    s.tc.forEach((t,i)=>sfx(t-.12,'paper/paper-slide',.2,{max:.6,note:'kartu '+(i+1)}));
    sfx(s.ta,'light/sparkle-touch',.18,{max:1,note:'ajakan komentar'});sfx(s.speechEnd+.2,'light/sparkle-wand',.24,{max:2,note:'penutup'});}
};
