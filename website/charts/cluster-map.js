import {attachCountySearch,countySearchEntries} from '../county-search.js';
import {d3} from '../vendor.js';
import {fmt,esc} from '../shared.js';
import {mapMarkup,arrangeMap} from './maps.js';
import {clusterColors} from './analysis-details.js';

export async function drawClusterMap({clusteringResults,geo,states}){
  const host=document.querySelector('#cluster-geography .interactive-body');
  host.innerHTML=mapMarkup('cluster-map');
  const root=host.firstElementChild;
  root.insertAdjacentHTML('afterbegin','<h3 class="visualization-title">Where the county profiles occur</h3>');
  root.querySelector('.map-context p').textContent=`County profiles · ${clusteringResults.year} · K-means`;
  root.querySelector('.map-controls').insertAdjacentHTML('afterbegin','<label>Cluster view <select class="cluster-view"><option value="migration">Migration</option><option value="characteristics">County characteristics</option></select></label>');
  const context=root.querySelector('.map-context');root.querySelector('.map-bottom').innerHTML='<span class="small">Hover to inspect</span><div class="cluster-legend"></div>';
  root.querySelector('.map-bottom').prepend(context);
  root.insertAdjacentHTML('beforeend','<details class="map-notes"><summary>Coverage and boundary notes · gray counties</summary><p>Gray = outside the eligible cohort or unmatched boundary. Alaska and Connecticut state substitutes are excluded. Census 2025 display boundaries retain source-year geography limitations. Cluster numbers identify groups within each view.</p></details>');
  arrangeMap(root);
  const rows=await d3.csv('data/clustering/cluster-assignments.csv');if(!root.isConnected)return;
  const records=new Map(rows.map(r=>[r.county_fips,r])),features=new Map(geo.features.map(f=>[f.id,f]));
  const svg=d3.select(root.querySelector('svg')).attr('aria-label','US county cluster membership'),layer=svg.append('g'),path=d3.geoPath(d3.geoAlbersUsa().fitExtent([[15,15],[985,595]],geo));
  const tip=root.querySelector('.tooltip'),detail=root.querySelector('.map-detail'),input=root.querySelector('input'),suggestions=root.querySelector('.county-suggestions');
  let view='migration',selected;
  const zoom=d3.zoom().scaleExtent([1,12]).on('zoom',e=>layer.attr('transform',e.transform));svg.call(zoom);
  function info(id){const r=records.get(id);if(!r)return 'Outside the eligible cohort or unmatched boundary.';const profile=clusteringResults.interpretations[view].find(p=>p.cluster===+r[view+'_kmeans']);return `<strong>${esc(r.county_name)}</strong><span>C${r[view+'_kmeans']} · ${esc(profile.title)}</span><span>Net ${fmt(r.net_individuals_per_1000)} · Inflow ${fmt(r.inflow_individuals_per_1000)} · Outflow ${fmt(r.outflow_individuals_per_1000)} / 1,000</span>`;}
  function inspect(id){selected=id;paths.classed('selected',f=>f.id===id);}
  const paths=layer.selectAll('.county').data(geo.features).join('path').attr('class','county').attr('d',path).on('pointermove',(e,f)=>{tip.hidden=false;tip.innerHTML=info(f.id);const box=root.querySelector('.map-wrap').getBoundingClientRect();tip.style.left=Math.max(5,Math.min(e.clientX-box.left+12,box.width-tip.offsetWidth-8))+'px';tip.style.top=Math.max(5,Math.min(e.clientY-box.top-75,box.height-tip.offsetHeight-5))+'px';}).on('pointerleave',()=>tip.hidden=true);
  layer.append('g').selectAll('path').data(states.features).join('path').attr('d',path).attr('class','state-border');
  const entries=countySearchEntries(geo,states);
  function choose(id){input.value=entries.find(c=>c.id===id).name;hide();inspect(id);const f=features.get(id);if(f){const [[x0,y0],[x1,y1]]=path.bounds(f),scale=Math.min(9,.75/Math.max((x1-x0)/1000,(y1-y0)/610));svg.call(zoom.transform,d3.zoomIdentity.translate(500-scale*(x0+x1)/2,305-scale*(y0+y1)/2).scale(scale));}}
  const {hide}=attachCountySearch(input,suggestions,entries,choose);
  function update(){paths.attr('fill',f=>records.has(f.id)?clusterColors[+records.get(f.id)[view+'_kmeans']-1]:'#dedbd3');root.querySelector('.cluster-legend').innerHTML=clusteringResults.views[view].profiles.map(p=>`<span><i style="background:${clusterColors[p.cluster-1]}"></i>C${p.cluster}: ${p.cluster===1?'Higher':'Lower'} ${view==='migration'?'turnover':'housing costs'} · ${fmt(p.counties)}</span>`).join('');if(selected)inspect(selected);}
  root.querySelector('.cluster-view').onchange=e=>{view=e.target.value;update();};
  root.querySelector('.zoom-in').onclick=()=>svg.call(zoom.scaleBy,1.7);root.querySelector('.zoom-out').onclick=()=>svg.call(zoom.scaleBy,1/1.7);root.querySelector('.reset').onclick=()=>{svg.call(zoom.transform,d3.zoomIdentity);input.value='';selected=null;paths.classed('selected',false);detail.hidden=true;hide();};update();
}
