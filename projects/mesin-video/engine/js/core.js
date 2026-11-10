/* ============================== data & util ============================== */
const TL=JSON.parse(document.getElementById('tldata').textContent);
const W=1080,H=1920,FPS=30,DUR=TL.duration;
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const PAL={paper:'#F2E8D3',paper2:'#E7DBC0',ink:'#1E2A22',leaf:'#2F5D3A',leaf2:'#3E7647',lit:'#7DAF4B',under:'#93B47E',under2:'#B2CA9C',
  stem:'#5E8C3E',orange:'#EE7A2B',maroon:'#8E2B36',marker:'#F3C64E',cream:'#FFF8EA',blush:'#E39A7E',dark:'#1F3D2B',warn:'#E5533D',blue:'#23407A',ok:'#3E8E4E'};
const f1=n=>Math.round(n*10)/10;
const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v)), lerp=(a,b,t)=>a+(b-a)*t;
const E={lin:t=>t,inQ:t=>t*t,outQ:t=>t*(2-t),inC:t=>t*t*t,outC:t=>1-Math.pow(1-t,3),ioC:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
  ioQ:t=>t<.5?2*t*t:-1+(4-2*t)*t,outB:(t,s=1.70158)=>1+(s+1)*Math.pow(t-1,3)+s*Math.pow(t-1,2)};
const seg=(t,a,b,e=E.lin)=>e(clamp((t-a)/(b-a)));
function bez(x1,y1,x2,y2){const cx=3*x1,bx=3*(x2-x1)-cx,ax=1-cx-bx,cy=3*y1,by=3*(y2-y1)-cy,ay=1-cy-by;
  const sx=t=>((ax*t+bx)*t+cx)*t,sy=t=>((ay*t+by)*t+cy)*t,dx=t=>(3*ax*t+2*bx)*t+cx;
  return x=>{if(x<=0)return 0;if(x>=1)return 1;let t=x;for(let i=0;i<8;i++){const e=sx(t)-x,d=dx(t);if(Math.abs(e)<1e-6||!d)break;t-=e/d;}return sy(clamp(t));};}
const mulberry32=a=>()=>{let t=(a+=0x6d2b79f5);t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
const T=TL.T, beat=n=>n*T;
const LANG=new URLSearchParams(location.search).get('lang')==='en'?'en':'id';
const world=$('#world');

/* adegan dari timeline.json: {key,jenis,param,cut,speechStart,speechEnd,words:[{w,t,e,p,tag}],cues:{nama:t}} */
const SCN=TL.scenes;
SCN.forEach((s,i)=>{s.i=i;s.end=i+1<SCN.length?SCN[i+1].cut:DUR;s.prev=SCN[i-1]||null;s.next=SCN[i+1]||null;});
const cue=(s,n,d)=>(s.cues&&s.cues[n]!=null)?s.cues[n]:d;
const pageStart=(s,p)=>{const w=s.words.find(w=>w.p===p);return w?w.t:null;};
const nPages=s=>s.words.length?s.words[s.words.length-1].p+1:0;
const sid=(s,n)=>`${s.key}-${n}`;
const S$=(s,n)=>document.getElementById(sid(s,n));

/* ikon: SVG Fluent Emoji Flat (MIT) / SVG kustom, disisipkan oleh build_page.py */
const ICON=TL.icons||{};
const icon=(name,size,cls='')=>`<div class="ic ${cls}" style="width:${size}px;height:${size}px">${ICON[name]||''}</div>`;

/* ============================== dunia: area per adegan ==============================
   kuis + jawaban berbagi satu area; twist menimpa area sebelumnya (tinta merembes); adegan lain pindah area
   searah gerak kamera (turun / kanan / turun / kiri ...). Koordinat lokal area: 0..1080 x 0..1920. */
(function layoutAreas(){
  const dirs=[[0,2700],[1900,0],[0,2700],[-1900,0]];let cx=540,cy=960,k=0;
  SCN.forEach((s,i)=>{
    if(i===0){s.cx=cx;s.cy=cy;s.dir=null;return;}
    if(s.jenis==='jawaban'||s.jenis==='twist'){s.cx=s.prev.cx;s.cy=s.prev.cy;s.dir=null;return;}
    const d=dirs[k++%dirs.length];cx+=d[0];cy+=d[1];s.cx=cx;s.cy=cy;s.dir=d;});
})();
const wp=(s,x,y)=>[s.cx-540+x,s.cy-960+y];
const WP=(k,x,y)=>wp(k,x,y);
const focus=(at,s,x,y,z,dur=.8,ease='power2.inOut')=>{const [a,b]=wp(s,x,y);return look(at,a,b,z,dur,ease);};
function areaEl(s,z=1){const d=document.createElement('div');d.className='area';d.id=sid(s,'area');d.style.left=(s.cx-540)+'px';d.style.top=(s.cy-960)+'px';d.style.zIndex=z;world.appendChild(d);return d;}

/* teks judul yang boleh membungkus (kata = span .w untuk animasi say/press) */
function lineW(parent,text,{x,y,w=940,size=92,id,cls='',align='center',z}={}){
  const d=put(parent,'',{x,y,id,cls:'ab line ttl '+cls,z});d.style.fontSize=size+'px';d.style.width=w+'px';d.style.textAlign=align;
  String(text).split(/\s+/).filter(Boolean).forEach((t,i)=>{if(i)d.appendChild(document.createTextNode(' '));const s=document.createElement('span');s.className='w';s.style.marginRight='0';s.textContent=t;d.appendChild(s);});
  return d;}
/* perkecil huruf sampai muat N baris */
function fitLines(el,maxLines,minSize){let fs=parseFloat(el.style.fontSize);const lh=()=>parseFloat(getComputedStyle(el).lineHeight)||fs*1.05;
  while(fs>minSize&&el.offsetHeight>lh()*maxLines+4){fs-=4;el.style.fontSize=fs+'px';}return fs;}
function fitWidth(el,maxW,minSize){let fs=parseFloat(getComputedStyle(el).fontSize);while(fs>minSize&&el.scrollWidth>maxW){fs-=4;el.style.fontSize=fs+'px';}return fs;}

/* ============================== maskot: ekspresi dari tag intonasi naskah ============================== */
const TAGMAP={curious:['think','think'],excited:['excited','excited'],whispers:['whisper','whisper'],surprised:['surprised','surprised'],
  laughs:['laugh','laugh'],serious:['serious','idle'],dramatically:['shock','shock'],mischievously:['mischief','idle'],playful:['wink','point'],
  warm:['happy','wave'],sad:['sad','sad'],happy:['happy','idle'],sighs:['sad','idle']};
function mascotFromTags(){SCN.forEach(s=>{let last=null;s.words.forEach(w=>{if(w.tag&&w.tag!==last){const m=TAGMAP[w.tag];if(m)mexp(w.t-.08,m[0],m[1]);}last=w.tag;});});}

/* denyut mengikuti ketukan musik (render): elemen yang sedang dibicarakan "bernapas" di tiap ketukan */
const PULSES=[];const pulse=(el,t0,t1,amp=.05)=>{if(el&&t1>t0+.2)PULSES.push({el,t0,t1,amp});};
/* spasi tak-putus antara angka dan satuan ("±30 menit" tidak terpotong) */
const nb=s=>String(s).replace(/±\s+/g,'±').replace(/(\d[\d.,]*)\s+(menit|detik|jam|g|kg|mg|µg|ml|liter|kkal|kalori|°C|sdm|sdt|cm|potong|butir)(?![a-z])/gi,'$1\u00a0$2');

/* ============================== SFX: tabel pin (detik video) ============================== */
const SFX=[];
const PK=new Set(['counter/clock-tick-single','impact/hit-blow','impact/impact-zoom-quick','impact/impact-cine-big','paper/paper-staple',
  'paper/paper-slice-quick','fluid/water-drop-cave','fluid/water-splash','camera/click-camera','text/pen-click-twice']);
const sfx=(t,src,vol,o={})=>SFX.push({t:+t.toFixed(3),src,vol,max:o.max||null,al:o.al||(PK.has(src)?'pk':'on'),rv:o.rv||0,note:o.note||''});
