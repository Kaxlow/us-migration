import {Plotly} from './vendor.js';
import {chapters,datasets} from './chapters/index.js';
import {esc} from './shared.js';

const main=document.getElementById('main');
const nav=document.getElementById('navigation');
const data={};
let activeChapter, cleanup, routeVersion=0;
const requests=new Map();
async function loadDataset(key){
  if(Object.hasOwn(data,key))return data[key];
  if(!requests.has(key))requests.set(key,fetch('data/'+datasets[key]).then(r=>{if(!r.ok)throw Error(datasets[key]+' could not be loaded');return r.json();}).then(value=>data[key]=value).catch(error=>{requests.delete(key);throw error;}));
  return requests.get(key);
}
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
  restoring=true;route(position).finally(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>{restoring=false;})));
});
nav.innerHTML=['Overview','Data & Methods','Analyses','Findings','Future work'].map(group=>{
  const links=chapters.filter(c=>c.group===group).map(c=>`<a href="#${c.slug}" data-status="${c.status}">${c.title}</a>`).join('');
  return group==='Future work'?`<details class="nav-group future-nav"><summary>Future work</summary>${links}</details>`:`<div class="nav-group"><span class="nav-group-label">${group}</span>${links}</div>`;
}).join('');

async function render(chapter) {
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
  const pending=previous?.nodes.some(node=>node.querySelector?.('[data-analysis-chart] .interactive-body:empty')||node.querySelector?.('#cluster-map')&&!node.querySelector('#cluster-map .county'));
  if(previous&&!pending){main.replaceChildren(...previous.nodes);cleanup=previous.cleanup;updateStickyOffsets();return;}
  main.innerHTML=`<h1 class="chapter-title">${chapter.heading}</h1><div class="chapter-layout"><nav class="section-nav" aria-label="${esc(chapter.title)} sections"></nav><div class="chapter-content">${chapter.render(data)}</div></div>`;
  arrangeSections(chapter);
  const headings=[...main.querySelectorAll('.chapter-content > .section > h2')];
  headings.forEach(heading=>{
    if(!heading.id)throw Error('Chapter section needs an explicit stable ID');
    heading.classList.add('section-title');
  });
  main.querySelector('.section-nav').innerHTML='<span>On this page</span>'+headings.map(h=>`<a href="#${chapter.slug}/${h.id}">${esc(h.textContent)}</a>`).join('');
  linkResearchQuestions();
  main.querySelectorAll('a[href]').forEach(link=>{
    if(!link.getAttribute('href').startsWith('#')){link.target='_blank';link.rel='noopener noreferrer';}
  });
  cleanup=await chapter.init(data);
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
    if(target){const detail=target.parentElement.querySelector(':scope > details.supporting-detail');if(detail)detail.open=true;for(let node=target.parentElement;node&&node!==main;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;target.scrollIntoView({block:'start'});if(location.hash.includes('/')){target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}}
  });
}
const aliases={conclusion:{'section-overview':'section-findings','section-data':'section-limitations','section-code':'section-limitations','section-results':'section-findings'},regression:{'section-data':'section-overview','section-code':'section-overview','section-results':'section-overview'}};
async function route(position){
  const version=++routeVersion;
  if(location.hash==='#main')return;
  const slug=location.hash.slice(1).split('/')[0];
  const chapter=chapters.find(c=>c.slug===slug)||chapters[0];
  const requested=location.hash.split('/')[1];
  const alias=(aliases[chapter.slug]||(chapter.status==='planned'?aliases.regression:{}))[requested];
  if(alias)history.replaceState(history.state,'','#'+chapter.slug+'/'+alias);
  main.setAttribute('aria-busy','true');
  try{
    await Promise.all(chapter.datasets.map(loadDataset));
    if(version!==routeVersion)return;
    if(chapter.status==='planned')nav.querySelector('.future-nav').open=true;
    if(chapter!==activeChapter)await render(chapter);
    if(version!==routeVersion)return;
    if(typeof position==='number')requestAnimationFrame(()=>{updateStickyOffsets();window.scrollTo(0,position);});
    else scrollToSection();
  }catch(error){
    if(version!==routeVersion)return;
    if(activeChapter===chapter){cleanup?.();chapterViews.delete(chapter);}
    else if(activeChapter)chapterViews.set(activeChapter,{nodes:[...main.childNodes],cleanup});
    activeChapter=null;cleanup=null;
    main.innerHTML=`<h1 class="chapter-title">${esc(chapter.title)}</h1><section class="loading" role="alert"><h2>This chapter could not load</h2><p>${esc(error.message)}</p><button id="retry-chapter">Try again</button><p><a href="#introduction">Return to Overview</a></p></section>`;
    main.querySelector('#retry-chapter').addEventListener('click',()=>route(position));
  }finally{if(version===routeVersion)main.removeAttribute('aria-busy');}
}

function arrangeSections(chapter){
  const content=main.querySelector('.chapter-content');
  const sections=[...content.children];
  const byId=id=>sections.find(s=>s.querySelector(':scope > h2')?.id===id);
  if(chapter.group==='Analyses'){
    const overview=byId('section-overview');
    const bundle=chapter.slug==='clustering'?data.clusteringResults:chapter.slug==='pca'?data.pcaResults:chapter.slug==='naivebayes'?data.naiveBayesResults:data.decisionTreeResults;
    const sentences=bundle.conclusions||Object.values(bundle.tasks).map(t=>t.conclusions[0]);
    const question={clustering:'Can county profiles reveal different migration patterns?',pca:'Which dimensions summarize county characteristics?',naivebayes:'How accurately do characteristics classify inflow intensity?',dectrees:'How accurately do characteristics classify outflow intensity and net direction?'}[chapter.slug];
    overview.querySelector('.analysis-prose')?.insertAdjacentHTML('beforebegin','<h3>How the method works</h3>');
    overview.querySelector('h2').insertAdjacentHTML('afterend',`<div class="prose chapter-answer"><p class="study-question">${question}</p>${sentences.slice(0,chapter.slug==='clustering'?2:1).map(t=>`<p>${esc(t)}</p>`).join('')}</div>`);
    for(const id of ['section-overview','section-data-prep','section-code','section-results','section-conclusions']){
      const section=byId(id);if(section)content.append(section);
    }
  }else if(chapter.slug==='data-prep-eda'){
    for(const id of ['section-eda-findings','section-data-sources','section-data-cleaning'])content.append(byId(id));

  }
}
main.addEventListener('toggle',()=>{updateStickyOffsets();window.dispatchEvent(new Event('resize'));},true);
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
window.addEventListener('hashchange',()=>{if(!restoring)route();});
route();
