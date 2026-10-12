import {Plotly} from './vendor.js';
import {chapters} from './chapters/index.js';
import {esc} from './shared.js';

const main=document.getElementById('main');
const nav=document.getElementById('navigation');
let data, activeChapter, cleanup;
const chapterViews=new Map();
history.scrollRestoration='manual';
let restoring=false;
function savePosition(){if(!restoring)history.replaceState({...history.state,scrollY:window.scrollY},'');}
let sectionFrame;
window.addEventListener('scroll',()=>{savePosition();if(!sectionFrame)sectionFrame=requestAnimationFrame(()=>{sectionFrame=null;highlightSection();});},{passive:true});
function highlightSection(){
  const headings=[...main.querySelectorAll('.section-title')];
  if(!headings.length)return;
  const threshold=document.querySelector('.chapter-title').getBoundingClientRect().bottom+24;
  let current=headings[0];
  for(const heading of headings)if(heading.getBoundingClientRect().top<=threshold)current=heading;
  if(window.scrollY>0&&window.scrollY+window.innerHeight>=document.documentElement.scrollHeight-2)current=headings.at(-1);
  main.querySelectorAll('.section-nav a').forEach(link=>{
    if(link.hash.split('/')[1]===current.id)link.setAttribute('aria-current','location');
    else link.removeAttribute('aria-current');
  });
}
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#"]');
  if(!link||link.hash==='#main'||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();savePosition();history.pushState({},'',link.hash);route();
});
window.addEventListener('popstate',()=>{
  const position=history.state?.scrollY;
  restoring=true;route(position);
  requestAnimationFrame(()=>requestAnimationFrame(()=>{restoring=false;}));
});
nav.innerHTML=chapters.map(chapter=>`<a href="#${chapter.slug}">${chapter.title}</a>`).join('');

function render(chapter) {
  // Keep mounted chapter nodes and control state for history traversal. Rebuilding
  // async charts here changes page height underneath a restored scroll position.
  if(activeChapter)chapterViews.set(activeChapter,{nodes:[...main.childNodes],cleanup});
  activeChapter=chapter;
  nav.querySelectorAll('a').forEach(a=>{
    if(a.hash===`#${chapter.slug}`)a.setAttribute('aria-current','page');
    else a.removeAttribute('aria-current');
  });
  document.title=`Do County Characteristics Explain Migration Flows? | ${chapter.title}`;
  const previous=chapterViews.get(chapter);
  const pending=previous?.nodes.some(node=>node.querySelector?.('[data-phase-chart] .interactive-body:empty')||node.querySelector?.('#cluster-map')&&!node.querySelector('#cluster-map .county'));
  if(previous&&!pending){main.replaceChildren(...previous.nodes);cleanup=previous.cleanup;updateStickyOffsets();return;}
  main.innerHTML=`<h1 class="chapter-title">${chapter.heading}</h1><div class="chapter-layout"><nav class="section-nav" aria-label="${esc(chapter.title)} sections"></nav><div class="chapter-content">${chapter.render(data)}</div></div>`;
  const headings=[...main.querySelectorAll('.chapter-content > .section > h2')];
  headings.forEach(heading=>{
    heading.id='section-'+heading.textContent.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    heading.classList.add('section-title');
  });
  main.querySelector('.section-nav').innerHTML='<span>On this page</span>'+headings.map(h=>`<a href="#${chapter.slug}/${h.id}">${esc(h.textContent)}</a>`).join('');
  linkResearchQuestions();
  main.querySelectorAll('a[href]').forEach(link=>{
    if(!link.getAttribute('href').startsWith('#')){link.target='_blank';link.rel='noopener noreferrer';}
  });
  cleanup=chapter.init(data);
  updateStickyOffsets();
}

// Link narrative references, including text interpolated from exported findings.
function linkResearchQuestions(){
  const walker=document.createTreeWalker(main.querySelector('.chapter-content'),NodeFilter.SHOW_TEXT);
  const nodes=[];
  while(walker.nextNode())if(!walker.currentNode.parentElement.closest('a,script,style'))nodes.push(walker.currentNode);
  for(const node of nodes){
    const pattern=/\bQuestion(?:s)?\s+(?:10|[1-9])(?:\s*(?:,|and|&|–|-)\s*(?:10|[1-9]))*\b|\b(?:10|ten) research questions\b/gi;
    if(!pattern.test(node.textContent))continue;
    pattern.lastIndex=0;
    const fragment=document.createDocumentFragment();let offset=0;
    for(const match of node.textContent.matchAll(pattern)){
      fragment.append(node.textContent.slice(offset,match.index));
      const a=document.createElement('a');a.href='#introduction/section-research-framework';a.textContent=match[0];fragment.append(a);
      offset=match.index+match[0].length;
    }
    fragment.append(node.textContent.slice(offset));node.replaceWith(fragment);
  }
}
function scrollToSection(){
  const links=[...main.querySelectorAll('.section-nav a')];
  const id=location.hash.slice(1).split('/')[1]||links[0]?.hash.split('/')[1];
  links.forEach((a,i)=>{
    if(a.hash.split('/')[1]===id)a.setAttribute('aria-current','location');
    else a.removeAttribute('aria-current');
  });
  requestAnimationFrame(()=>{
    updateStickyOffsets();
    const target=document.getElementById(id);
    if(target){target.scrollIntoView({block:'start'});if(location.hash.includes('/')){target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}}
  });
}
function route(position){
  if(!data)return;
  if(location.hash==='#main')return;
  const slug=location.hash.slice(1).split('/')[0];
  const chapter=chapters.find(c=>c.slug===slug)||chapters[0];
  if(chapter!==activeChapter)render(chapter);
  const section=location.hash.split('/')[1]||main.querySelector('.section-nav a')?.hash.split('/')[1];
  main.querySelectorAll('.section-nav a').forEach(link=>{if(link.hash.split('/')[1]===section)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
  if(typeof position==='number')requestAnimationFrame(()=>{updateStickyOffsets();window.scrollTo(0,position);});
  else scrollToSection();
}
window.addEventListener('pagehide',()=>{cleanup?.();for(const [chapter,view] of chapterViews)if(chapter!==activeChapter)view.cleanup?.();});
function updateStickyOffsets(){
  document.documentElement.style.setProperty('--masthead-height',document.querySelector('.site-masthead').getBoundingClientRect().height+'px');
  document.documentElement.style.setProperty('--chapter-height',(main.querySelector('.chapter-title')?.getBoundingClientRect().height||0)+'px');
  fitFigures();
}
function fitFigures(){
  const chrome=document.querySelector('.site-masthead').getBoundingClientRect().height+(main.querySelector('.chapter-title')?.getBoundingClientRect().height||0);
  const available=window.innerHeight-chrome-36;
  main.querySelectorAll('.chart-card,.map-card').forEach(card=>{
    if(card.closest('.chart-card')!==card&&card.closest('.chart-card'))return;
    const plot=card.querySelector('.chart,svg,img');if(!plot)return;
    const overhead=card.getBoundingClientRect().height-plot.getBoundingClientRect().height;
    const limit=Math.max(80,Math.floor(available-overhead));
    if(plot.style.maxHeight!==limit+'px')plot.style.maxHeight=limit+'px';
  });
}
new ResizeObserver(fitFigures).observe(main);
new ResizeObserver(updateStickyOffsets).observe(document.querySelector('.site-masthead'));
window.addEventListener('resize',updateStickyOffsets);
document.fonts.ready.then(updateStickyOffsets);
const files={population:'population.json',analysis:'analysis.json',geo:'county.geojson',states:'state.geojson',intro:'introduction.json',cleaningEvidence:'cleaning-evidence.json',clusteringResults:'clustering.json',pcaResults:'pca.json'};
Promise.all(Object.entries(files).map(async([key,file])=>{
  const response=await fetch('data/'+file,{cache:'no-cache'});
  if(!response.ok)throw Error(file+' could not be loaded');
  return [key,await response.json()];
})).then(entries=>{data=Object.fromEntries(entries);route();window.addEventListener('hashchange',()=>{if(!restoring)route();});}).catch(error=>{
  window.portfolioTelemetry?.reportError(error,{component:'atlas-bootstrap'});
  main.innerHTML=`<div class="loading"><h2>The atlas could not load.</h2><p>${esc(error.message)}. Serve the website through a local HTTP server, then reload.</p><button onclick="location.reload()">Try again</button></div>`;
});
