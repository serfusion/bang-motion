/* ============================== templat adegan ==============================
   Tiap jenis adegan: build(s) membuat elemen dari s.param, choreo(s) menjadwalkan gerak dari waktu kata/isyarat
   ({nama} di naskah), sfx(s) memasang pin suara, render(s,t) menggambar efek prosedural (fungsi murni dari t). */
const SCENES={};
const SPOTS={BC:[540,1395,.52],BR:[930,1382,.5],TR:[944,470,.44],BL:[170,1385,.52],SIDE:[960,1425,.46]};
const mspot=(t,k,dur=.5,arc=110)=>mpos(t,...SPOTS[k],dur,arc);
/* waktu default untuk item ke-k bila isyarat {l0},{b0}.. tidak ditulis: sebar merata di dalam ucapan */
const itemT=(s,pre,k,n)=>cue(s,pre+k,lerp(s.speechStart+.4,s.speechEnd-.6,n>1?k/(n-1):0));

/* ---------- transisi masuk ke area baru ---------- */
function enter(s){
  const c=s.cut,p=s.prev;
  if(p&&p.jenis==='jawaban'){                     // menembus kartu jawaban
    const q=p.q,G=q.G,k=q.param.jawaban,[bx,by]=wp(q,G.xs[k]+G.w/2,G.y+G.h/2);
    look(c-.62,bx,by,1.4,.3,'power2.inOut');look(c-.32,bx,by,7,.32,'power2.in');
    camSet(c,s.cx,s.cy-300,1.45);tl.to(C,{y:s.cy,z:1,duration:1.1,ease:'power3.out'},c);
    sfx(c,'transition/air-zoom-vacuum',.4,{al:'pk',note:'menembus kartu jawaban'});return;}
  if(s.jenis==='cta'){                             // daun raksasa melintas lensa
    tl.fromTo(FX,{lensP:0},{lensP:1,duration:.9,ease:'power1.inOut',immediateRender:false},c-.45);
    camSet(c,s.cx,s.cy,1.06);tl.to(C,{z:1,duration:1.3,ease:'power3.out'},c);
    sfx(c,'transition/air-whoosh-powerful',.4,{al:'pk',note:'daun melintas lensa'});sfx(c,'impact/impact-cine-big',.36,{al:'pk',note:'CTA'});return;}
  const horiz=s.dir&&s.dir[0]!==0,k=horiz?'whipX':'whipY';
  look(c-.36,s.cx,s.cy,1,.62,'power2.inOut');
  tl.fromTo(FX,{[k]:0},{[k]:26,duration:.3,ease:'power2.in',immediateRender:false},c-.36);tl.to(FX,{[k]:0,duration:.32,ease:'power2.out'},c-.06);
  sfx(c-.06,'transition/whoosh-fast',.3,{al:'pk',note:'whip ke adegan '+s.key});}
/* elemen yang keluar sebelum kamera pindah */
const leave=(s,sels,at=s.end-.75)=>{const ok=sels.filter(n=>S$(s,n));if(s.next&&ok.length)out(ok.map(n=>'#'+sid(s,n)),at,{to:{y:-220,rotate:-5},dur:.3,st:.03});};

/* ============================== KUIS (hook) ============================== */
SCENES.kuis={
  build(s){
    const P=s.param,A=s.el=areaEl(s),n=P.pilihan.length,hero=!!P.ikon&&n===2;
    put(A,`<div class="sticker" style="background:${PAL.marker};font:800 64px/1 'Plus Jakarta Sans';letter-spacing:.06em;padding:12px 30px 16px">${esc(P.stiker||'KUIS!')}</div>`,{x:70,y:132,id:sid(s,'stk'),rot:-6,z:3});
    const ttl=lineW(A,P.judul,{x:70,y:250,w:940,size:92,id:sid(s,'ttl')});fitLines(ttl,2,60);
    const tb=250+ttl.offsetHeight;let G;
    if(n===3){const w=300,h=420,y=Math.max(tb+70,500);G={w,h,y,xs:[45,390,735],rot:[-4,0,4],ic:180,name:46,ring:[540,y+h+120]};}
    else if(hero){const w=420,h=330,y=Math.max(tb+360,780);G={w,h,y,xs:[70,590],rot:[-4,4],ic:130,name:76,ring:[540,y+h/2],hero:[540,(tb+y)/2]};}
    else{const w=440,h=540,y=Math.max(tb+70,460);G={w,h,y,xs:[60,580],rot:[-4,4],ic:280,name:56,ring:[540,y+h/2]};}
    s.G=G;
    if(hero)put(A,icon(P.ikon,250),{x:415,y:G.hero[1]-125,id:sid(s,'hero'),z:2,cls:'ab'});
    P.pilihan.forEach((o,k)=>{
      const art=o.ikon?icon(o.ikon,G.ic):'';
      const inner=hero?`<div class="qart" style="top:30px;height:${G.ic}px">${art}</div><div class="qname" style="bottom:36px;font-size:${G.name}px">${esc(o.label)}</div>`
                      :`<div class="qart" style="top:44px;bottom:${G.name+60}px">${art}</div><div class="qname" style="bottom:32px;font-size:${G.name}px">${esc(o.label)}</div>`;
      put(A,`<div class="qcard" style="width:${G.w}px;height:${G.h}px"><div class="qhi"></div><div class="qtag">${'ABC'[k]}</div>${inner}</div>`,{x:G.xs[k],y:G.y,id:sid(s,'c'+k),cls:'ab',rot:G.rot[k],z:2});});
    put(A,`<svg width="200" height="200" viewBox="-100 -100 200 200"><circle r="86" fill="${PAL.ink}"/><circle class="rp" r="86" fill="none" stroke="${PAL.marker}" stroke-width="14" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" transform="rotate(-90)"/><text class="rt" y="30" text-anchor="middle" font-family="Plus Jakarta Sans" font-weight="800" font-size="84" fill="${PAL.cream}">${n===2?'VS':'?'}</text></svg>`,
      {x:G.ring[0]-100,y:G.ring[1]-100,id:sid(s,'ring'),cls:'ab',z:6});
    const cf=put(A,'',{x:0,y:0,id:sid(s,'cf'),cls:'ab',z:8});
    for(let i=0;i<26;i++){const d=document.createElement('div');d.className='ab';d.style.opacity=0;d.innerHTML=leafMini(40+(i%3)*10,i%4===0);cf.appendChild(d);}
    s.cfl=[...cf.children];
  },
  choreo(s){
    const P=s.param,c=s.cut,n=P.pilihan.length,j=s.next;
    camSet(c,s.cx,s.cy-60,1);tl.to(C,{z:1.03,duration:Math.max(1,s.speechEnd-c),ease:'sine.inOut'},c);
    P.pilihan.forEach((o,k)=>tl.fromTo('#'+sid(s,'c'+k),{scale:.88,rotate:k===0?-6:k===n-1?6:0},{scale:1,rotate:0,duration:.42,ease:'back.out(2.2)',immediateRender:true},c+k*.05));
    pop('#'+sid(s,'stk'),c+.12,{dur:.45,from:.3,rot:-20});
    say('#'+sid(s,'ttl'),c+.05,{mode:'scale',dur:.42,st:.06});
    if(S$(s,'hero'))tl.fromTo('#'+sid(s,'hero'),{scale:.7,rotate:-12},{scale:1,rotate:0,duration:.6,ease:'back.out(2.4)',immediateRender:true},c+.08);
    P.pilihan.forEach((o,k)=>{const t=cue(s,'p'+k,null);if(t!=null)wiggle('#'+sid(s,'c'+k),t,5,.5);});
    mspot(c+.35,'BC');mexp(c+.35,'think','think');
    /* hitung mundur di jeda sebelum jawaban */
    if(j&&j.jenis==='jawaban'&&j.speechStart-s.speechEnd>.8){
      s.cd={t0:s.speechEnd+.02,t1:j.speechStart-.02};mexp(s.cd.t0,'nervous','nervous');
      tl.to(P.pilihan.map((o,k)=>'#'+sid(s,'c'+k)),{y:-14,duration:.08,yoyo:true,repeat:Math.max(1,Math.round((s.cd.t1-s.cd.t0)/.16)),ease:'sine.inOut'},s.cd.t0);
      tl.to('#'+sid(s,'ring'),{scale:0,opacity:0,duration:.3,ease:'back.in(2)'},s.cd.t1+.02);}
    else tl.to('#'+sid(s,'ring'),{scale:0,opacity:0,duration:.3,ease:'back.in(2)'},s.speechEnd+.3);
  },
  sfx(s){const c=s.cut,P=s.param;
    sfx(c,'paper/paper-move-quick',.3,{max:.5,note:'kartu menepuk'});sfx(c+.05,'paper/paper-slice-quick',.26,{note:'kartu menepuk'});
    sfx(c+.12,'paper/paper-slide',.3,{max:.5,note:'stiker KUIS'});sfx(c+.35,'transition/wind-swoosh-short',.18,{note:'maskot muncul'});
    if(S$(s,'hero'))sfx(c+.1,'light/sparkle-touch',.22,{max:.8,note:'ikon utama'});
    P.pilihan.forEach((o,k)=>{const t=cue(s,'p'+k,null);if(t!=null)sfx(t,k%2?'transition/swoosh-quick':'paper/paper-move-quick',.2-k*.02,{max:.5,note:'pilihan '+'ABC'[k]});});
    if(s.cd)[0,1,2].forEach(i=>sfx(s.cd.t0+i*(s.cd.t1-s.cd.t0)/3,'counter/clock-tick-single',.6+i*.06,{al:'pkwin',max:.07,note:'hitung mundur '+(3-i)}));
  },
  render(s,t){
    const R=s.roul,n=s.param.pilihan.length;
    /* cincin hitung mundur */
    if(s.cd){const {t0,t1}=s.cd,rt=$('#'+sid(s,'ring')+' .rt'),rp=$('#'+sid(s,'ring')+' .rp');
      if(t<t0){rt.textContent=n===2?'VS':'?';rp.setAttribute('stroke-dashoffset',1);}
      else if(t<t1){const u=(t-t0)/(t1-t0),k=3-Math.min(2,Math.floor(u*3)),f=u*3-(3-k);rt.textContent=String(k);rp.setAttribute('stroke-dashoffset',(1-f).toFixed(3));
        S$(s,'ring').style.scale=(1+.08*Math.max(0,1-f*4)).toFixed(3);}
      else{rt.textContent='1';rp.setAttribute('stroke-dashoffset',0);}}
    /* rolet sorotan: cepat lalu melambat, berhenti di jawaban */
    const sel=roulAt(s,t);
    for(let k=0;k<n;k++){const el=$('#'+sid(s,'c'+k)+' .qhi');const on=sel===k;el.style.opacity=on?1:0;
      if(on){let i=0;if(R)while(i+1<R.t.length&&R.t[i+1]<=t)i++;const kick=R&&t<R.end?1+.05*clamp(1-(t-R.t[i])/.1):1+.02*Math.sin(t*9);el.style.transform=`scale(${kick.toFixed(3)})`;}}
    /* ikon utama mengapung */
    const h=S$(s,'hero');if(h)h.style.translate=`0 ${f1(Math.sin(t*2.2)*8)}px`;
    /* konfeti daun dari kartu jawaban */
    if(s.conf!=null){const G=s.G,k=s.param.jawaban,ox=G.xs[k]+G.w/2,oy=G.y+G.h*.4,tau=t-s.conf;
      s.cfl.forEach((el,i)=>{if(tau<0||tau>2.2){el.style.opacity=0;return;}
        const Rn=mulberry32(900+i),ang=(-160+Rn()*140)*Math.PI/180,v=700+Rn()*900,spin=(Rn()-.5)*1400;
        el.style.left=f1(ox+Math.cos(ang)*v*tau)+'px';el.style.top=f1(oy+Math.sin(ang)*v*tau+900*tau*tau)+'px';
        el.style.opacity=clamp((2.2-tau)/.6).toFixed(3);el.style.transform=`rotate(${f1(Rn()*360+spin*tau)}deg) scale(${(.8+Rn()*.6).toFixed(2)})`;});}
  }};
/* kartu yang sedang disorot (-1 = tidak ada) */
function roulAt(s,t){const R=s.roul;if(!R||t<R.t[0])return -1;if(t>=R.end)return t<R.off?s.param.jawaban:-1;let i=0;while(i+1<R.t.length&&R.t[i+1]<=t)i++;return R.seq[i];}

/* ============================== JAWABAN (reveal + open loop) ============================== */
SCENES.jawaban={
  build(s){
    const q=s.q=s.prev,P=s.param,G=q.G,A=s.el=q.el,k=q.param.jawaban,cx=G.xs[k]+G.w/2;
    const bad=/MITOS|SALAH|BOHONG/i.test(P.stempel||'')||P.warna==='merah';
    const st=put(A,`<div class="stamp${bad?' bad':''}" style="font-size:${G.w<350?42:54}px">${esc(P.stempel||'BENAR!')}</div>`,{x:0,y:G.y+G.h*.6,id:sid(s,'stamp'),cls:'ab',rot:-10,z:10});
    st.style.left=f1(cx-st.offsetWidth/2)+'px';
    let yb=G.y+G.h+44;
    if(P.label){P.label.forEach((t,i)=>put(A,`<div class="num" style="font-size:${G.w<350?52:64}px;color:${i===k?PAL.leaf:PAL.orange};text-align:center;width:${G.w}px">${esc(t)}</div>`,{x:G.xs[i],y:yb,id:sid(s,'tag'+i),z:11}));yb+=86;}
    if(P.catatan)put(A,`<div class="lbl" style="font-size:36px;width:1080px;text-align:center;opacity:.8">${esc(P.catatan)}</div>`,{x:0,y:yb,id:sid(s,'note'),z:11});
    if(P.besar){
      const txt=String(P.besar),big=txt.length<=3,fs=Math.round(big?Math.min(300,880/(.56*Math.max(2,txt.length))):Math.min(190,860/(.56*txt.length))),cy=G.hero?G.hero[1]:G.y+G.h*.5;
      if(big){const burst=(R1,R2,m)=>{let d='';for(let i=0;i<m*2;i++){const r=i%2?R2:R1,a=i/(m*2)*Math.PI*2-Math.PI/2;d+=(i?'L':'M')+f1(Math.cos(a)*r)+' '+f1(Math.sin(a)*r);}return d+'Z';};
        put(A,`<svg width="560" height="560" viewBox="-280 -280 560 560" style="overflow:visible"><path d="${burst(250,204,20)}" fill="${PAL.ink}" transform="translate(9 9)" opacity=".85"/><path d="${burst(250,204,20)}" fill="${PAL.marker}" stroke="${PAL.ink}" stroke-width="5"/></svg>`,{x:260,y:cy-280,id:sid(s,'burst'),z:8});}
      else put(A,`<div style="width:940px;height:${Math.round(fs*1.45)}px;background:${PAL.marker};border:6px solid ${PAL.ink};border-radius:24px;box-shadow:12px 12px 0 ${PAL.ink}"></div>`,{x:70,y:cy-fs*.72,id:sid(s,'burst'),rot:-4,z:8});
      const riso=put(A,'',{x:0,y:cy-fs*.6,w:1080,h:fs*1.2,id:sid(s,'riso'),cls:'ab',z:9});
      const plate=(col,id)=>`<div id="${id}" style="position:absolute;inset:0;display:flex;justify-content:center;align-items:center;mix-blend-mode:multiply;visibility:hidden"><div class="ttl" style="font-size:${fs}px;font-weight:800;color:${col};font-variation-settings:'SOFT' 30;white-space:nowrap">${esc(txt)}</div></div>`;
      riso.innerHTML=plate(PAL.leaf,sid(s,'rS'))+plate(PAL.orange,sid(s,'rA'))+plate(PAL.leaf,sid(s,'rB'));}
    if(P.teaser)$('#teaser').innerHTML=`<div class="card" style="width:380px;height:300px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#FBF4E4;rotate:-5deg"><div style="display:flex;align-items:center;gap:20px;height:180px"><div class="ttl" style="font-size:150px;font-weight:800;color:${PAL.maroon}">?</div>${sealSVG()}</div><div class="hand" style="font-size:50px;color:${PAL.maroon};margin-top:2px;white-space:nowrap">${esc(P.teaser)}</div></div>`;
  },
  choreo(s){
    const q=s.q,P=s.param,G=q.G,n=q.param.pilihan.length,a=q.param.jawaban,R=cue(s,'jawab',s.speechStart+.8);s.rv=R;
    /* rolet: urutan 0,1,..,n-1 berulang, jumlah langkah dipilih agar berhenti di jawaban */
    {const s0=s.speechStart+.06,span=R-.02-s0;if(span>.5){const iv=[];let d=.075;while(iv.reduce((x,y)=>x+y,0)<span||(iv.length-1)%n!==a){iv.push(d);d*=1.17;}
      const kf=span/iv.reduce((x,y)=>x+y,0);let tt=s0;q.roul={t:[],seq:[],end:R-.02,off:s.end-.75};iv.forEach((x,i)=>{q.roul.t.push(+tt.toFixed(3));q.roul.seq.push(i%n);tt+=x*kf;});}}
    const others=q.param.pilihan.map((o,k)=>k).filter(k=>k!==a);
    tl.to('#'+sid(q,'c'+a),{scale:1.08,y:-6,duration:.35,ease:'back.out(2.5)',transformOrigin:'50% 30%'},R-.05);
    tl.to(others.map(k=>'#'+sid(q,'c'+k)),{scale:.9,y:40,opacity:.5,filter:'saturate(.3)',duration:.5,ease:'power2.out',transformOrigin:'50% 90%'},R+.1);
    tl.fromTo('#'+sid(s,'stamp')+' .stamp',{opacity:0,scale:2.2,rotate:12},{opacity:1,scale:1,rotate:0,duration:.18,ease:'power3.in',immediateRender:false},R+.22);
    q.conf=R;mexp(R-.05,'excited','excited');
    {const [ax,ay]=wp(q,G.xs[a]+G.w/2,G.y+G.h/2);look(R-.02,lerp(q.cx,ax,.4),lerp(q.cy-60,ay,.4),1.12,.12,'power3.out');look(R+.12,q.cx,q.cy-60,1.04,.6,'power2.out');}
    const tL=cue(s,'label',R+.9);
    if(P.label){mspot(tL-.25,'SIDE',.45,24);P.label.forEach((t,i)=>pop('#'+sid(s,'tag'+i),tL+i*.13,{dur:.45,from:.4,rot:0}));}
    if(P.catatan)label('#'+sid(s,'note'),tL+.35);
    if(P.besar){const hb=cue(s,'besar',R+1.0);s.riso=hb;if(!P.label)mspot(hb-.3,'SIDE',.45,24);
      tl.to('#'+sid(s,'stamp'),{opacity:0,scale:.85,duration:.14,ease:'power2.in'},hb-.1);
      tl.fromTo('#'+sid(s,'burst'),{opacity:0,scale:.2,rotate:-40},{opacity:1,scale:1,rotate:0,duration:.32,ease:'back.out(2.2)',immediateRender:false},hb-.03);
      if(S$(q,'hero'))tl.to('#'+sid(q,'hero'),{opacity:0,scale:.6,duration:.2,ease:'power2.in'},hb-.12);
      mexp(hb,'proud','flex');}
    if(P.teaser){const tz=cue(s,'teaser',s.speechEnd-1);s.dim={t0:tz-.35,t1:s.end-.25};
      tl.fromTo('#teaser',{opacity:0,y:420,rotate:-20,scale:.7},{opacity:1,y:0,rotate:0,scale:1,duration:.6,ease:'back.out(1.5)',immediateRender:false},tz-.2);
      tl.to('#teaser',{opacity:0,y:300,rotate:10,duration:.3,ease:'power2.in'},s.end-.6);
      if(P.besar)tl.to(['#'+sid(s,'burst'),'#'+sid(s,'riso')],{opacity:0,scale:.85,duration:.25,ease:'power2.in'},tz-.4);}
    leave(q,['ttl','stk'],s.end-.75);leave(s,['tag0','tag1','tag2','note','burst','riso']);
  },
  sfx(s){const R=s.rv,q=s.q,P=s.param;
    if(q.roul)q.roul.t.forEach((x,i)=>sfx(x,i%2?'ui/switch-tap':'ui/switch-click-quick',.32+.22*i/q.roul.t.length,{max:.25,note:'rolet'}));
    sfx(R-1.1,'light/light-sweep-magic',.3,{max:1.1,al:'tail',note:'naik menuju jawaban'});
    sfx(R,'impact/hit-fast-exciting',.5,{note:'JAWABAN'});sfx(R+.05,'crowd/applause-rhythmic-loop',.22,{max:1.6,note:'tepuk tangan'});
    sfx(R+.02,'light/sparkle-poof-hit',.28,{max:1.4,note:'konfeti'});sfx(R+.4,'impact/hit-weak',.45,{note:'stempel'});
    if(P.label)P.label.forEach((t,i)=>sfx(cue(s,'label',R+.9)+i*.13,'text/typewriter-hit-soft',.32-i*.04,{note:'angka '+t}));
    if(s.riso!=null){sfx(s.riso,'transition/whoosh-fast',.32,{al:'pk',note:'riso meluncur'});sfx(s.riso,'impact/hit-blow',.55,{note:'riso menghantam'});sfx(s.riso+22/FPS,'paper/paper-staple',.36,{note:'pelat terkunci'});}
    if(s.dim){sfx(s.dim.t0+.3,'transition/air-woosh-deep',.24,{max:1.2,note:'layar meredup'});sfx(s.dim.t0+.4,'paper/paper-slide',.3,{max:.6,note:'kartu misteri'});}
  },
  render(s,t){
    if(s.riso!=null){const HIT=s.riso,f=fr(t-HIT),S=S$(s,'rS'),Ap=S$(s,'rA'),Bp=S$(s,'rB'),SNAPF=22;
      if(f<-8){S.style.visibility=Ap.style.visibility=Bp.style.visibility='hidden';}
      else if(f<0){S.style.visibility='visible';Ap.style.visibility=Bp.style.visibility='hidden';S.style.transform=`translateX(${f1(lerp(1400,0,E.inC(clamp((f+8)/8))))}px)`;}
      else if(f<SNAPF){const m=Math.cos(2*Math.PI/18*f)*Math.exp(-f/60),dx=16*m,dy=7*m;S.style.visibility='hidden';Ap.style.visibility=Bp.style.visibility='visible';
        Ap.style.transform=`translate(${f1(-dx)}px,${f1(dy)}px)`;Bp.style.transform=`translate(${f1(dx)}px,${f1(-dy)}px)`;}
      else{S.style.visibility='visible';Ap.style.visibility=Bp.style.visibility='hidden';S.style.transform=`scale(${(f<SNAPF+4?1+.03*(1-(f-SNAPF)/4):1).toFixed(4)})`;}}
  }};

/* ============================== LANGKAH (rantai sebab-akibat / daftar tips) ============================== */
SCENES.langkah={
  build(s){
    const P=s.param,A=s.el=areaEl(s),n=P.item.length,list=P.gaya==='daftar';
    const ty=list?190:200,ttl=lineW(A,P.judul||'',{x:70,y:ty,w:940,size:list?100:90,id:sid(s,'ttl')});fitLines(ttl,2,60);
    const tb=ty+ttl.offsetHeight;s.items=[];
    if(list){const y0=tb+90,gap=Math.min(270,(1260-y0)/n);
      P.item.forEach((it,k)=>{const y=y0+k*gap;put(A,`<div class="step card" style="width:940px;box-sizing:border-box;padding:22px 30px;gap:26px"><div class="badge">${k+1}</div>${icon(it.ikon,170)}<div class="tx"><div class="t1" style="font-size:62px">${esc(it.teks)}</div>${it.sub?`<div class="t2">${esc(it.sub)}</div>`:''}</div></div>`,{x:70,y,id:sid(s,'i'+k),z:3});
        s.items.push({x:540,y:y+75});});}
    else{const ys=[[620,1060],[540,860,1180],[490,740,990,1240]][n-2];
      let arr='';P.item.forEach((it,k)=>{const left=k%2===0,y=ys[k];
        put(A,`<div class="step" style="flex-direction:${left?'row':'row-reverse'};width:900px"><div style="flex:none">${icon(it.ikon,200)}</div><div class="tx" style="align-items:${left?'flex-start':'flex-end'};text-align:${left?'left':'right'}"><div class="t1">${esc(it.teks)}</div>${it.sub?`<div class="t2">${esc(it.sub)}</div>`:''}</div></div>`,{x:90,y:y-100,id:sid(s,'i'+k),z:3});
        s.items.push({x:left?190:890,y,left});});
      for(let k=0;k+1<n;k++){const a=s.items[k],b=s.items[k+1],x0=a.x,y0=a.y+116,x1=b.x,y1=b.y-120;
        const hd=`M${x1-26} ${y1-30}L${x1} ${y1}L${x1+26} ${y1-30}`;
        arr+=`<path id="${sid(s,'ar'+k)}" d="M${x0} ${y0}C${x0} ${y0+130} ${x1} ${y1-150} ${x1} ${y1}" stroke="${PAL.ink}" stroke-width="7" fill="none" stroke-linecap="round" stroke-dasharray="1" stroke-dashoffset="1" pathLength="1" opacity="0"/>`+
             `<path id="${sid(s,'ah'+k)}" d="${hd}" stroke="${PAL.ink}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>`;}
      put(A,`<svg width="1080" height="1920" viewBox="0 0 1080 1920" style="overflow:visible">${arr}</svg>`,{x:0,y:0,cls:'ab',z:2});}
  },
  choreo(s){
    const P=s.param,c=s.cut,n=P.item.length,list=P.gaya==='daftar';enter(s);
    mspot(c+.1,list?'BR':'TR');
    say('#'+sid(s,'ttl'),c+.25,{mode:'up',dur:.55,st:.1});
    const ts=P.item.map((it,k)=>itemT(s,'l',k,n));s.ts=ts;
    ts.forEach((t,k)=>{const el='#'+sid(s,'i'+k);
      if(list)fly(el,t-.08,{from:{x:700,rotate:6,scale:.9},dur:.55,ease:'back.out(1.4)'});
      else{fly(el,t-.08,{from:{y:140,rotate:s.items[k].left?-8:8,scale:.6},dur:.55,ease:'back.out(1.6)'});
        if(k>0){tl.set('#'+sid(s,'ar'+(k-1)),{attr:{opacity:1}},t-.45);tl.to('#'+sid(s,'ar'+(k-1)),{attr:{'stroke-dashoffset':0},duration:.4,ease:'power2.inOut'},t-.45);tl.to('#'+sid(s,'ah'+(k-1)),{opacity:1,duration:.1},t-.08);}
        focus(t-.3,s,540,lerp(960,s.items[k].y,.25),1.05,.6);}});
    const last=ts[n-1];
    if(!list&&last+1.6<s.end-.5)focus(last+1.0,s,540,960,1,.9);
    if(list)tl.to(C,{z:1.04,duration:Math.max(1,s.end-c-.6),ease:'sine.inOut'},c+.7);
    if(s.next)leave(s,['ttl']);
  },
  sfx(s){const n=s.param.item.length;
    sfx(s.cut+.25,'transition/swoosh-quick',.22,{note:'judul'});
    s.ts.forEach((t,k)=>{sfx(t-.08,k%2?'transition/swoosh-quick':'paper/paper-slide',.28-k*.03,{max:.6,note:'item '+(k+1)});
      if(k>0&&s.param.gaya!=='daftar')sfx(t-.45,'text/marker-pen-line',.24,{max:.45,note:'panah'});});}
};

/* ============================== BANDING (batang arsir -> padat) ============================== */
SCENES.banding={
  build(s){
    const P=s.param,A=s.el=areaEl(s),n=P.item.length,BMAX=560,vmax=Math.max(...P.item.map(i=>i.nilai))||1;
    if(P.tema==='kejutan'){put(A,'<div class="yellowpage"></div>',{x:0,y:0,cls:'ab',z:0});put(A,'<div class="rays" style="left:-460px;top:-1040px;width:2000px;height:2000px"></div>',{x:0,y:0,id:sid(s,'rays'),cls:'ab',z:0});}
    const ttl=lineW(A,P.judul||'',{x:70,y:150,w:820,size:100,id:sid(s,'ttl'),align:'left'});fitLines(ttl,2,64);
    let tb=150+ttl.offsetHeight;
    if(P.sub){put(A,`<div class="hand" style="font-size:52px;color:${PAL.maroon}">${esc(P.sub)}</div>`,{x:76,y:tb+8,id:sid(s,'sub')});tb+=80;}
    const y0=tb+90,gap=Math.min(290,(1330-y0)/n);s.bars=[];
    P.item.forEach((it,k)=>{const y=y0+k*gap,w=Math.max(18,it.nilai/vmax*BMAX);
      put(A,`<div style="position:relative;width:940px;height:${gap-24}px">${it.juara?'<div class="juara"></div>':''}<div style="display:flex;align-items:center;gap:18px">${icon(it.ikon,96,'flat')}<div class="lbl" style="font-size:44px;font-weight:700">${esc(it.label)}</div></div>
        <div class="ab" style="left:0;top:116px;width:${BMAX}px;height:86px"><div class="hatchbar hb" style="background:repeating-linear-gradient(45deg,rgba(30,42,34,.55) 0 7px,transparent 7px 17px);box-shadow:inset 0 0 0 3px rgba(30,42,34,.55);width:0"></div>
        <div class="hatchbar sb" style="background:linear-gradient(90deg,${it.juara?PAL.leaf:k%2?'#C9852E':'#7C98AA'},${it.juara?'#5E9B47':k%2?'#E2A955':PAL.under2});width:0;opacity:0"></div>
        <div class="num ab vb" style="top:6px;font-size:66px;color:${it.juara?PAL.leaf:PAL.ink};opacity:0">${esc(it.teks)}</div></div></div>`,{x:70,y,id:sid(s,'b'+k),z:3});
      s.bars.push({w,k});});
  },
  choreo(s){
    const P=s.param,c=s.cut,n=P.item.length;enter(s);mspot(c+.1,'TR');
    say('#'+sid(s,'ttl'),c+.25,{mode:'scale',dur:.5,st:.1});if(S$(s,'sub'))label('#'+sid(s,'sub'),c+.6);
    s.ts=P.item.map((it,k)=>itemT(s,'b',k,n));
    s.ts.forEach((t,k)=>{label('#'+sid(s,'b'+k),t-.2,{dur:.35});
      if(P.item[k].juara){tl.to(C,{z:1.12,duration:.12,ease:'power3.out'},t+.5);tl.to(C,{z:1.03,duration:.6,ease:'power2.out'},t+.64);
        tl.fromTo('#'+sid(s,'b'+k)+' .juara',{opacity:0,scale:1.15},{opacity:1,scale:1,duration:.3,ease:'back.out(2)',immediateRender:false},t+.5);mexp(t+.4,'excited','excited');}});
    tl.to(C,{z:1.03,duration:Math.max(1,s.end-c-1),ease:'sine.inOut'},c+.7);
    if(s.next)leave(s,['ttl','sub']);
  },
  sfx(s){s.ts.forEach((t,k)=>{sfx(t-.2,k%2?'fluid/sand-swish':'text/chalk-line',.26-k*.03,{max:.9,note:'batang '+(k+1)});sfx(t+.5,'text/typewriter-hit-soft',.3,{note:'nilai '+(k+1)});
      if(s.param.item[k].juara){sfx(t+.5,'impact/impact-zoom-quick',.4,{note:'juara'});sfx(t+.6,'crowd/clap-single',.42,{note:'juara'});}});},
  render(s,t){
    s.bars.forEach((b,i)=>{const t0=s.ts[i],g=seg(t,t0,t0+.9,E.outC),m=seg(t,t0+.5,t0+1.0),root=S$(s,'b'+i),w=g*b.w;
      root.querySelector('.hb').style.width=f1(w)+'px';root.querySelector('.sb').style.width=f1(w)+'px';
      root.querySelector('.hb').style.opacity=(1-m).toFixed(3);root.querySelector('.sb').style.opacity=m.toFixed(3);
      const v=root.querySelector('.vb');v.style.left=f1(w+22)+'px';v.style.opacity=m.toFixed(3);});
    const r=S$(s,'rays');if(r)r.style.rotate=f1(t*6)+'deg';
  }};

/* ============================== TWIST (tinta merembes ke halaman baru) ============================== */
SCENES.twist={
  build(s){
    const P=s.param,kej=P.nada==='kejutan',A=s.el=areaEl(s,5);A.style.clipPath='path("M0 0Z")';
    put(A,`<div class="darkpage${kej?' kejutan':''}"></div>`,{x:0,y:0,cls:'ab',z:0});
    if(kej)put(A,'<div class="rays" style="left:-460px;top:-860px;width:2000px;height:2000px"></div>',{x:0,y:0,id:sid(s,'rays'),cls:'ab',z:0});
    const ttl=lineW(A,`${P.judul||(kej?'Kejutan!':'Wajib tahu!')}`,{x:84,y:170,w:900,size:116,id:sid(s,'ttl'),align:'left'});ttl.style.color=PAL.cream;ttl.style.fontStyle='italic';
    const news=put(A,`<div class="news"><svg class="ab" width="600" height="110" viewBox="0 0 600 110" style="left:8px;top:2px;overflow:visible;z-index:2"><path id="${sid(s,'circ')}" d="M560 44C560 10 40 4 30 48C22 92 540 98 568 58C576 46 564 26 526 16" fill="none" stroke="#E5533D" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg><div class="mast"><span class="kk">${esc(P.kicker||'FAKTA')}</span></div><div class="head">${hlText(P.headline,sid(s,'hl'))}</div><div class="bar" style="width:92%"></div><div class="bar" style="width:70%"></div></div>`,{x:90,y:350,id:sid(s,'news'),rot:-2,z:3});
    {const kk=news.querySelector('.kk'),w=kk.offsetWidth,cx=36+w/2,cy=46,rx=w/2+38,ry=38;
      $('#'+sid(s,'circ')).setAttribute('d',`M${f1(cx+rx-8)} ${cy-ry+6}C${f1(cx+rx+6)} ${cy-6} ${f1(cx+rx-30)} ${cy+ry+2} ${f1(cx)} ${cy+ry}C${f1(cx-rx-6)} ${cy+ry-4} ${f1(cx-rx-10)} ${cy-ry+8} ${f1(cx-rx/3)} ${cy-ry-2}C${f1(cx+rx/3)} ${cy-ry-8} ${f1(cx+rx+14)} ${cy-ry+10} ${f1(cx+rx+6)} ${cy+6}`);}
    let y=350+news.offsetHeight+60;s.rows=[];
    (P.baris||[]).forEach((r,i)=>{const long=String(r.nilai||'').length>8,txt=long?`<div class="rt">${esc(r.teks)}<div class="rv" style="font-size:52px;margin-top:6px">${esc(r.nilai)}</div></div>`:`<div class="rt">${esc(r.teks)}</div><div class="rv">${esc(r.nilai||'')}</div>`;
      const el=put(A,`<div class="row">${icon(r.ikon,104,'flat')}${txt}<div class="mark ${r.ok?'ok':'no'}">${r.ok?'✓':'✕'}</div></div>`,{x:90,y,id:sid(s,'r'+i),z:3});y+=el.offsetHeight+30;s.rows.push(r);});
    if(P.angka)put(A,`<div class="bignum" style="width:1080px"><div class="n">${esc(P.angka.teks)}</div><div class="s">${esc(P.angka.sub||'')}</div></div>`,{x:0,y:Math.min(y+10,1060),id:sid(s,'num'),z:3});
    const drop=document.createElement('div');drop.id=sid(s,'drop');drop.className='ab';
    drop.style.cssText=`width:46px;height:60px;left:0;top:0;opacity:0;border-radius:50% 50% 50% 50% / 60% 60% 40% 40%;background:${kej?PAL.blue:PAL.dark};z-index:20`;s.prev.el.appendChild(drop);
  },
  choreo(s){
    const P=s.param,kej=P.nada==='kejutan',c=s.cut,p=s.prev;
    if(!kej){tl.to(p.el,{filter:'grayscale(1) contrast(1.1)',duration:.08},c-.02);
      tl.fromTo('#flash',{opacity:0},{opacity:.55,duration:.05,immediateRender:false},c-.02);tl.to('#flash',{opacity:0,duration:.45,ease:'power2.out'},c+.05);
      tl.to(C,{z:1.12,duration:.08,ease:'power4.out'},c-.02);mexp(c-.02,'shock','shock');}
    else{tl.to(C,{z:1.08,duration:.12,ease:'power3.out'},c-.02);mexp(c-.02,'surprised','surprised');}
    s.ink={drop:c+.12,f0:c+.28};look(c+.2,s.cx,s.cy-40,1,1.6,'power2.inOut');
    say('#'+sid(s,'ttl'),s.ink.f0+.45,{mode:'up',dur:.55,st:.14});mspot(c+.3,'BR');
    const tk=cue(s,'k',s.speechStart+.6);
    fly('#'+sid(s,'news'),tk-.15,{from:{y:640,rotate:12,scale:.9},dur:.75,ease:'back.out(1.2)'});
    tl.to('#'+sid(s,'circ'),{attr:{'stroke-dashoffset':0},duration:.45,ease:'power2.inOut'},tk+.55);
    tl.to('#'+sid(s,'hl'),{scaleX:1,duration:.55,ease:'power2.inOut'},cue(s,'stabilo',tk+.95));
    tl.to(C,{z:1.05,duration:2.4,ease:'sine.inOut'},tk+.8);
    s.tr=s.rows.map((r,i)=>cue(s,'i'+i,tk+1.6+i*1.4));
    s.tr.forEach((t,i)=>{fly('#'+sid(s,'r'+i),t-.12,{from:{y:300,rotate:-4,scale:.9},dur:.5,ease:'back.out(1.4)'});
      tl.fromTo('#'+sid(s,'r'+i)+' .mark',{opacity:0,scale:2.2,rotate:-20},{opacity:1,scale:1,rotate:0,duration:.18,ease:'power3.in',immediateRender:false},t+.45);});
    if(P.angka){s.ta=cue(s,'angka',s.speechEnd-1.2);tl.fromTo('#'+sid(s,'num'),{opacity:0,scale:.4},{opacity:1,scale:1,duration:.5,ease:'back.out(2.2)',immediateRender:false},s.ta-.05);}
    if(s.next)leave(s,['ttl']);
  },
  sfx(s){const P=s.param,kej=P.nada==='kejutan',c=s.cut;
    if(!kej)sfx(c-.04,'film/vinyl-scratch-small',.62,{note:'piringan berhenti: TWIST'});
    else{sfx(c-.04,'light/sparkle-wand',.3,{max:1.4,note:'kejutan'});sfx(c-.06,'transition/whoosh-fast',.28,{al:'pk',note:'kejutan'});}
    sfx(s.ink.drop+.16,'fluid/water-drop-cave',.5,{note:'tetes tinta'});sfx(s.ink.f0+.1,'transition/air-woosh-deep',.26,{max:2,note:'tinta merembes'});
    const tk=cue(s,'k',s.speechStart+.6);sfx(tk-.15,'paper/paper-page-turn-big',.4,{note:'kartu berita'});sfx(tk+.55,'text/marker-pen-line',.34,{max:.45,note:'lingkaran merah'});
    sfx(cue(s,'stabilo',tk+.95),'text/marker-pen-line',.28,{max:.55,note:'stabilo'});
    s.tr.forEach((t,i)=>{sfx(t-.12,'paper/paper-slide',.26,{max:.6,note:'baris '+(i+1)});sfx(t+.6,s.rows[i].ok?'crowd/clap-single':'impact/hit-blow',s.rows[i].ok?.36:.45,{note:s.rows[i].ok?'centang':'silang'});});
    if(s.ta!=null){sfx(s.ta,'impact/hit-weak',.45,{note:'angka'});sfx(s.ta+.05,'light/sparkle-touch',.22,{max:1,note:'angka'});}
  },
  render(s,t){
    const f=fr(t-s.ink.f0),A=s.el,drop=S$(s,'drop');
    if(t<s.ink.drop)A.style.clipPath='path("M0 0Z")';else if(f<80)A.style.clipPath=inkPath(Math.max(0,f),540,760);else A.style.clipPath='none';
    const dp=clamp((t-s.ink.drop)/.16);drop.style.opacity=t>=s.ink.drop&&t<s.ink.f0+.05?1:0;drop.style.transform=`translate(517px,${f1(lerp(320,730,E.inQ(dp)))}px)`;
    const r=S$(s,'rays');if(r)r.style.rotate=f1(t*6)+'deg';
  }};

/* judul kliping: kata di antara *bintang* diberi stabilo (tanpa bintang: kata terakhir) */
function hlText(t,id){const m=String(t).match(/^(.*?)\*(.+?)\*(.*)$/);const [a,b,c]=m?[m[1],m[2],m[3]]:(()=>{const w=String(t).trim().split(/\s+/);return [w.slice(0,-1).join(' ')+' ',w[w.length-1],''];})();
  return `${esc(a)}<span style="position:relative;z-index:0;display:inline-block">${esc(b)}<i id="${id}" style="position:absolute;left:-8px;right:-8px;bottom:4px;height:46%;background:${PAL.marker};z-index:-1;border-radius:6px;transform-origin:0 50%;transform:scaleX(0)"></i></span>${esc(c)}`;}
/* ============================== CTA (penutup) ============================== */
SCENES.cta={
  build(s){
    const P=s.param,A=s.el=areaEl(s);
    put(A,'<div class="rays" style="left:-460px;top:-570px;width:2000px;height:2000px;opacity:.8"></div>',{x:0,y:0,id:sid(s,'rays'),z:0});
    put(A,icon(P.ikon,330),{x:375,y:260,id:sid(s,'hero'),z:2});
    const ttl=lineW(A,P.judul,{x:60,y:650,w:960,size:112,id:sid(s,'ttl')});fitLines(ttl,2,70);
    const words=$$('.w',ttl);if(words.length){const last=words[words.length-1];last.innerHTML=`<span class="hlw" id="${sid(s,'hlw')}">${esc(last.textContent)}</span>`;}
    let y=650+ttl.offsetHeight+44;
    put(A,`<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:16px;width:1000px">${(P.tagline||[]).map((x,i)=>`<span class="chip" id="${sid(s,'chip'+i)}" style="opacity:0;display:inline-block">${esc(x)}</span>`).join('')}</div>`,{x:40,y,id:sid(s,'tags'),cls:'ab',z:3});
    y+=$('#'+sid(s,'tags')).offsetHeight+40;
    put(A,`<div style="display:flex;align-items:center;justify-content:center;gap:18px;width:1080px">${icon('love-letter',84,'flat')}<span class="hand" style="font-size:58px;white-space:nowrap">${esc(P.ajakan||'kirim ke temanmu')}</span><span id="${sid(s,'cb')}" style="display:inline-block">${icon(P.ikon_ajakan||P.ikon,76,'flat')}</span></div>`,{x:0,y,id:sid(s,'share'),z:3});
    y+=120;
    const cr=TL.meta||{},src=(cr.sumber||[]).join('; ');
    put(A,`<div class="lbl" style="font-size:29px;font-weight:600;width:680px;line-height:1.25;opacity:.8">Sumber: ${esc(src)}. Edukasi umum, bukan pengganti saran tenaga kesehatan. ${esc(cr.suara||'')}</div>`,{x:350,y,id:sid(s,'foot'),z:3});
  },
  choreo(s){
    const P=s.param,c=s.cut;enter(s);mspot(c+.15,'BL');
    tl.fromTo('#'+sid(s,'hero'),{opacity:0,scale:.3,rotate:-25},{opacity:1,scale:1,rotate:0,duration:.7,ease:'back.out(2.2)',immediateRender:false},c+.1);
    tl.fromTo('#'+sid(s,'rays'),{opacity:0},{opacity:.8,duration:.6},c+.1);
    press('#'+sid(s,'ttl'),c+.45);
    const hl=$('#'+sid(s,'hlw'));if(hl){s.mk={...addMarker(hl,31,1.2),t0:c+1.35};}
    const tg=P.tagline||[],w0=s.words.filter(w=>w.p<=1);
    s.tc=tg.map((x,i)=>w0.length?w0[Math.min(w0.length-1,Math.floor(i*w0.length/Math.max(1,tg.length)))].t:c+.8+i*.4);
    s.tc.forEach((t,i)=>tl.fromTo('#'+sid(s,'chip'+i),{opacity:0,scale:.3,rotate:[-14,10,-8][i%3]},{opacity:1,scale:1,rotate:0,duration:.45,ease:'back.out(2)',immediateRender:false},t));
    const ps=pageStart(s,Math.max(0,nPages(s)-2));s.ts=ps!=null?ps:c+(s.end-c)*.55;
    pop('#'+sid(s,'share'),s.ts-.05,{dur:.55,from:.4,rot:6});label('#'+sid(s,'foot'),s.ts+.5);
    const lw=s.words[s.words.length-1];s.tcb=lw?lw.t-.05:s.end-1;
    tl.to('#'+sid(s,'cb'),{scale:1.45,rotate:-14,duration:.32,ease:'back.out(3)',transformOrigin:'0% 50%'},s.tcb);
    wiggle('#'+sid(s,'cb'),s.tcb+.35,10,.6);
    mexp(s.tcb,'laugh','laugh');mexp((lw?lw.e:s.end-.6)+.3,'happy','wave');
    tl.to(C,{z:1.025,duration:Math.max(1,DUR-(c+1.3)),ease:'sine.inOut'},c+1.3);
  },
  sfx(s){const c=s.cut;
    sfx(c+.1,'light/sparkle-touch',.24,{max:1,note:'ikon penutup'});sfx(c+.45,'transition/swoosh-quick',.26,{note:'judul'});
    if(s.mk)sfx(s.mk.t0,'text/marker-pen-line',.34,{max:.45,note:'spidol judul'});
    s.tc.forEach((t,i)=>sfx(t,i%2?'fluid/water-bubble':'fluid/liquid-bubble',.3-i*.04,{max:.4,note:'chip '+(i+1)}));
    sfx(s.ts-.05,'transition/swoosh-quick',.28,{note:'ajakan kirim'});
    sfx(s.tcb,'impact/metal-spring-hit',.24,{max:1,note:'ikon callback membesar'});
    const lw=s.words[s.words.length-1];sfx((lw?lw.e:DUR-1)+.1,'light/sparkle-wand',.28,{max:2,note:'sparkle penutup'});},
  render(s,t){
    const r=S$(s,'rays');if(r)r.style.rotate=f1(t*5)+'deg';
    const h=S$(s,'hero');if(h&&t>s.cut+.8)h.style.translate=`0 ${f1(Math.sin(t*2)*10)}px`;
    if(s.mk)marker(s.mk,t,s.mk.t0);}
};
