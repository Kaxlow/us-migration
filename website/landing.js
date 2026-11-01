import {countyFlows} from './flow-data.js';
import {attachCountySearch,countySearchEntries} from './county-search.js?v=atlas-3';

const d3=globalThis.d3;
const canvas=document.getElementById('flow-canvas'),ctx=canvas.getContext('2d');
const countyInput=document.getElementById('flow-county'),yearInput=document.getElementById('flow-year'),modeInput=document.getElementById('flow-mode');
const status=document.getElementById('flow-status'),tip=document.getElementById('flow-tooltip');
const number=new Intl.NumberFormat('en-US');
const names=new Map(),places=new Map(),cache=new Map();
let meta,selected='08031',selection,visibleFlows=[],countyShapes=[],stateShapes=[],hitShapes=[],hitFlows=[];
let yaw=0,pitch=.72,zoom=1,panX=0,panY=0,frame=0,version=0,playing=null,loading=false,width=0,height=0;
const background=document.createElement('canvas'),base=background.getContext('2d');
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
const motionButton=document.getElementById('flow-motion');
let animateFlows=!reducedMotion.matches,motionChosen=false;
let sceneDirty=true,projectedFlows=[];
const formatCounty=id=>names.get(id)||id;
const fetchJSON=async url=>{const r=await fetch(url);if(!r.ok)throw Error(`Could not load ${url} (${r.status})`);return r.json();};

// An actual three-dimensional scene: counties lie on z=0, migration arcs rise
// above that plane, and a fixed perspective camera projects every vertex.
function project([x,y,z=0]){
  x-=500;y-=310;
  const a=x*Math.cos(yaw)-y*Math.sin(yaw),b=x*Math.sin(yaw)+y*Math.cos(yaw);
  const screenY=b*Math.cos(pitch)-z*Math.sin(pitch),depth=b*Math.sin(pitch)+z*Math.cos(pitch);
  const perspective=1600/(1600-depth),scale=Math.min(width/1080,height/600)*zoom;
  return [width/2+panX+a*scale*perspective,height*.5+panY+screenY*scale*perspective];
}
function polygonPath(rings){
  const path=new Path2D();
  for(const ring of rings){
    ring.forEach((v,i)=>{const [x,y]=project(v);i?path.lineTo(x,y):path.moveTo(x,y);});path.closePath();
  }
  return path;
}
function arc(flow){
  const a=places.get(flow.origin),b=places.get(flow.destination),lift=Math.min(190,30+Math.hypot(b[0]-a[0],b[1]-a[1])*.32);
  return Array.from({length:33},(_,i)=>{const t=i/32;return project([a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,4*lift*t*(1-t)]);});
}
function draw(time=0){
  frame=0;
  const rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);
  width=rect.width;height=rect.height;
  if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);sceneDirty=true;}
  if(sceneDirty){
    background.width=canvas.width;background.height=canvas.height;
    base.setTransform(dpr,0,0,dpr,0,0);hitShapes=[];
    for(const shape of countyShapes){
      const path=polygonPath(shape.rings);hitShapes.push({id:shape.id,path});
      base.fillStyle=shape.id===selected?'#bf7955':'#e0e6d9';base.fill(path);
      base.strokeStyle='#fffdf799';base.lineWidth=.35;base.stroke(path);
    }
    base.strokeStyle='#8d9f8b';base.lineWidth=.7;
    for(const shape of stateShapes)base.stroke(polygonPath(shape.rings));
    projectedFlows=[...visibleFlows].reverse().map(flow=>({flow,points:arc(flow)}));
    hitFlows=projectedFlows;sceneDirty=false;
  }
  ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(background,0,0);
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const max=Math.max(1,...visibleFlows.map(f=>f.quantity));
  // Paint smaller connections first so the major flows remain legible.
  for(const {flow,points} of projectedFlows){
    const lineWidth=10*flow.quantity/max;
    ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));
    ctx.strokeStyle=flow.inward?'#965030':'#3d7067';ctx.globalAlpha=.73;ctx.lineWidth=lineWidth;ctx.stroke();
    // The arrow sits near the destination, along the arc's projected tangent.
    const end=points[29],previous=points[27],angle=Math.atan2(end[1]-previous[1],end[0]-previous[0]),size=3+lineWidth*1.7;
    ctx.beginPath();ctx.moveTo(end[0],end[1]);
    ctx.lineTo(end[0]-Math.cos(angle-.45)*size,end[1]-Math.sin(angle-.45)*size);
    ctx.lineTo(end[0]-Math.cos(angle+.45)*size,end[1]-Math.sin(angle+.45)*size);
    ctx.closePath();ctx.fillStyle=ctx.strokeStyle;ctx.fill();
    // Two moving arrowheads travel from origin to destination on every arc.
    if(animateFlows)for(const offset of [0,.5]){
      const position=((time/2400+offset)%1)*32,index=Math.min(31,Math.floor(position)),t=position-index;
      const a=points[index],b=points[index+1],x=a[0]+(b[0]-a[0])*t,y=a[1]+(b[1]-a[1])*t;
      const angle=Math.atan2(b[1]-a[1],b[0]-a[0]),size=Math.max(4,Math.min(9,3+lineWidth));
      ctx.globalAlpha=.95;ctx.beginPath();ctx.moveTo(x,y);
      ctx.lineTo(x-Math.cos(angle-.5)*size,y-Math.sin(angle-.5)*size);
      ctx.lineTo(x-Math.cos(angle+.5)*size,y-Math.sin(angle+.5)*size);
      ctx.closePath();ctx.fillStyle=flow.inward?'#c67a4e':'#65a99a';ctx.fill();
    }
  }
  ctx.globalAlpha=1;
  if(places.has(selected)){
    const [x,y]=project(places.get(selected));
    ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fillStyle='#293d36';ctx.fill();ctx.strokeStyle='#fffdf7';ctx.lineWidth=2;ctx.stroke();
    ctx.font='600 12px "Noto Sans", sans-serif';ctx.textAlign='center';
    const label=formatCounty(selected).split(',')[0],w=ctx.measureText(label).width+14;
    const lx=Math.max(w/2+2,Math.min(width-w/2-2,x)),ly=Math.max(24,y-13);
    ctx.fillStyle='#fffdf7ee';ctx.fillRect(lx-w/2,ly-15,w,21);ctx.fillStyle='#293d36';ctx.fillText(label,lx,ly);
  }
  canvas.dataset.rendered='true';canvas.dataset.flowCount=String(visibleFlows.length);
  if(visibleFlows.length&&animateFlows&&!document.hidden)frame=requestAnimationFrame(draw);
}
function requestDraw(){sceneDirty=true;if(!frame&&!document.hidden)frame=requestAnimationFrame(draw);}
function geometry(feature,projection){
  const rings=[];let ring;
  d3.geoStream(feature,projection.stream({polygonStart(){},polygonEnd(){},lineStart(){ring=[];rings.push(ring);},lineEnd(){},point(x,y){ring?.push([x,y,0]);},sphere(){}}));
  return {id:feature.id,rings:rings.filter(r=>r.length>2)};
}
function stop(){clearTimeout(playing);playing=null;document.getElementById('flow-play').textContent='Play years';document.getElementById('flow-play').setAttribute('aria-pressed','false');}
function clearSelection(){selection=null;visibleFlows=[];requestDraw();}
async function update(){
  const ticket=++version,year=yearInput.value,county=selected,mode=modeInput.value;
  loading=true;clearSelection();tip.hidden=true;status.textContent=`Loading ${year} flows for ${formatCounty(county)}…`;
  try{
    if(!cache.has(year))cache.set(year,fetchJSON(`data/flows/${year}.json`).catch(e=>{cache.delete(year);throw e;}));
    const data=await cache.get(year);if(ticket!==version)return;
    selection=countyFlows(data.flows,county,mode);
    visibleFlows=selection.flows.filter(f=>places.has(f.origin)&&places.has(f.destination));
    status.textContent=selection.flows.length?'':mode==='net'?'No nonzero bilateral net flows can be calculated for this selection.':'No published flows are available for this selection.';
    canvas.setAttribute('aria-label',`3D ${mode} map for ${formatCounty(county)}, ${data.period_start}–${year}. ${visibleFlows.length} arrows. Drag or use arrow keys to pan; plus and minus zoom. Hover a flow for its value.`);
    requestDraw();
  }catch(error){if(ticket!==version)return;stop();clearSelection();status.replaceChildren(document.createTextNode(error.message+' '));const retry=document.createElement('button');retry.textContent='Retry loading flows';retry.onclick=update;status.append(retry);}
  finally{if(ticket===version)loading=false;}
}
function setCounty(id){selected=id;countyInput.value=`${formatCounty(id)} · ${id}`;countyInput.setCustomValidity('');stop();update();}
for(const control of [yearInput,modeInput])control.addEventListener('change',()=>{stop();update();});
document.getElementById('flow-play').onclick=()=>{
  if(playing){stop();return;}
  const button=document.getElementById('flow-play');button.textContent='Pause years';button.setAttribute('aria-pressed','true');
  const tick=async()=>{
    if(!playing)return;
    if(!loading){const index=meta.years.indexOf(+yearInput.value);yearInput.value=meta.years[(index+1)%meta.years.length];await update();}
    if(playing)playing=setTimeout(tick,1600);
  };
  playing=setTimeout(tick,100);
};
function reset(){yaw=0;pitch=.72;zoom=1;panX=0;panY=0;requestDraw();}
const zoomBy=factor=>{zoom=Math.max(.55,Math.min(5,zoom*factor));requestDraw();};
document.getElementById('flow-reset').onclick=reset;
document.getElementById('flow-zoom-in').onclick=()=>zoomBy(1.2);
document.getElementById('flow-zoom-out').onclick=()=>zoomBy(1/1.2);
canvas.addEventListener('wheel',e=>{e.preventDefault();zoomBy(Math.exp(-e.deltaY*.001));},{passive:false});
canvas.addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(e.key))return;
  e.preventDefault();
  if(e.key==='ArrowLeft')panX-=30;if(e.key==='ArrowRight')panX+=30;
  if(e.key==='ArrowUp')panY-=30;if(e.key==='ArrowDown')panY+=30;
  if(e.key==='+'||e.key==='=')zoomBy(1.15);if(e.key==='-')zoomBy(1/1.15);if(e.key==='0')reset();requestDraw();
});
let drag;
canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};canvas.setPointerCapture(e.pointerId);tip.hidden=true;});
canvas.addEventListener('pointermove',e=>{
  if(drag){panX+=e.clientX-drag.x;panY+=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;requestDraw();return;}
  const rect=canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
  let nearest=null,best=36;
  for(const candidate of hitFlows)for(let i=1;i<candidate.points.length;i++){
    const [a,b]=[candidate.points[i-1],candidate.points[i]],dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy||1)));
    const distance=(x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2;
    if(distance<best){best=distance;nearest=candidate.flow;}
  }
  if(nearest){tip.textContent=`${formatCounty(nearest.origin)} → ${formatCounty(nearest.destination)}: ${number.format(nearest.quantity)} ${modeInput.value==='net'?'net ':''}IRS individuals`;tip.hidden=false;tip.style.left=Math.max(0,Math.min(width-tip.offsetWidth,x+12))+'px';tip.style.top=Math.max(0,Math.min(height-tip.offsetHeight,y+12))+'px';}
  else tip.hidden=true;
});
canvas.addEventListener('pointerup',e=>{
  if(drag&&Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)<5){
    const rect=canvas.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
    // Path coordinates are in CSS pixels; isPointInPath follows the current transform.
    ctx.save();ctx.setTransform(1,0,0,1,0,0);
    const shape=hitShapes.find(s=>ctx.isPointInPath(s.path,x,y));ctx.restore();
    if(shape&&names.has(shape.id))setCounty(shape.id);
  }
  drag=null;
});
canvas.addEventListener('pointercancel',()=>drag=null);canvas.addEventListener('pointerleave',()=>tip.hidden=true);
new ResizeObserver(requestDraw).observe(canvas);
function pauseAnimation(){cancelAnimationFrame(frame);frame=0;}
function updateMotion(){
  motionButton.textContent=animateFlows?'Pause flows':'Animate flows';
  motionButton.setAttribute('aria-pressed',String(animateFlows));
  pauseAnimation();requestDraw();
}
motionButton.onclick=()=>{motionChosen=true;animateFlows=!animateFlows;updateMotion();};
reducedMotion.addEventListener('change',()=>{if(!motionChosen){animateFlows=!reducedMotion.matches;updateMotion();}});
updateMotion();
document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();pauseAnimation();}else requestDraw();});
window.addEventListener('pagehide',()=>{stop();pauseAnimation();});
window.addEventListener('pageshow',requestDraw);

async function init(){
  try{
    const [metadata,geo,states]=await Promise.all([fetchJSON('data/flows/metadata.json'),fetchJSON('data/county.geojson'),fetchJSON('data/state.geojson')]);
    meta=metadata;
    const counties=[...new Map([...countySearchEntries(geo,states),...meta.counties].map(c=>[c.id,c])).values()];
    counties.forEach(c=>names.set(c.id,c.name));
    const projection=d3.geoAlbersUsa().translate([500,310]).scale(1250);
    countyShapes=geo.features.map(f=>geometry(f,projection));stateShapes=states.features.map(f=>geometry(f,projection));
    for(const f of geo.features){const point=projection(d3.geoCentroid(f));if(point)places.set(f.id,[...point,0]);}
    attachCountySearch(countyInput,document.getElementById('flow-counties'),counties,setCounty);
    yearInput.innerHTML=meta.years.map(y=>`<option value="${y}">${y-1}–${y}</option>`).join('');yearInput.value=meta.years.at(-1);
    for(const el of [countyInput,yearInput,modeInput,document.getElementById('flow-play'),motionButton])el.disabled=false;
    setCounty(selected);
  }catch(error){status.replaceChildren(document.createTextNode(error.message+' '));const retry=document.createElement('button');retry.textContent='Retry atlas';retry.onclick=init;status.append(retry);}
}
init();
