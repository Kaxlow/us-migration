import {outcomes,outcomeSelect,outcomeById,cardControls} from '../outcomes.js';
import {d3} from '../vendor.js';
import {chartSvg,chartAxes} from './chart-utils.js';

export const clusterColors=['#965030','#3d7067','#8a9272','#b77f5a'];
const number=d3.format('.2f');
// Pointer, touch and keyboard inspection share a visible readout.
export function inspect(selection,label){
 selection.attr('tabindex',0).attr('aria-label',label).on('pointerenter.details pointermove.details focus.details click.details',function(event,row){
   const body=this.closest('.interactive-body');let tip=body.querySelector('.chart-tooltip');
   if(!tip){tip=document.createElement('div');tip.className='chart-tooltip';tip.setAttribute('role','tooltip');body.append(tip);}
   tip.textContent=this.getAttribute('aria-label');tip.hidden=false;const box=body.getBoundingClientRect(),point=this.getBoundingClientRect();
   const px=event.clientX||point.left+point.width/2,py=event.clientY||point.top;
   tip.style.left=Math.max(4,Math.min(px-box.left+10,box.width-tip.offsetWidth-4))+'px';
   tip.style.top=Math.max(4,Math.min(py-box.top+10,box.height-tip.offsetHeight-4))+'px';
 }).on('pointerleave.details blur.details',function(){const tip=this.closest('.interactive-body').querySelector('.chart-tooltip');if(tip)tip.hidden=true;});
}
function selectOutcome(id,draw){const body=document.querySelector(`#${id} .interactive-body`);body.insertAdjacentHTML('afterbegin',outcomeSelect('Migration outcome'));const select=body.querySelector('.outcome-select');cardControls(body.closest('.chart-card'),select.parentElement);const update=()=>{body.querySelectorAll('svg,.legend-card,.chart-tooltip,.score-tooltip').forEach(el=>el.remove());draw(outcomeById(select.value));body.querySelector('svg')?.setAttribute('aria-label',outcomeById(select.value).label+' comparison');};select.onchange=update;update();}
function chart(id){return chartSvg(id,id.replaceAll('-',' '));}
function legend(id,items){d3.select(`#${id} .interactive-body`).append('div').attr('class','legend-card').selectAll('span').data(items).join('span').html(d=>d);}
function colorLegend(id,title,kind,ticks){
 legend(id,[`<div class="scale-legend"><strong>${title}</strong><div class="color-key ${kind}"></div><div class="scale-ticks">${ticks.map(t=>`<span>${t}</span>`).join('')}</div></div>`]);
}
function scatter(id,rows,xkey,ykey,color,xlabel,ylabel,diagonal=false,outcome=outcomeById('net')){
  const svg=chart(id),x=d3.scaleLinear().domain(d3.extent(rows,r=>+r[xkey])).nice().range([65,820]),y=d3.scaleLinear().domain(d3.extent(rows,r=>+r[ykey])).nice().range([330,35]);
  chartAxes(svg,x,y,xlabel,ylabel);
  if(diagonal){const hi=Math.min(x.domain()[1],y.domain()[1]);svg.append('line').attr('x1',x(0)).attr('x2',x(hi)).attr('y1',y(0)).attr('y2',y(hi)).attr('stroke','#555').attr('stroke-dasharray','6 4');}
  const points=svg.append('g').selectAll('circle').data(rows).join('circle').attr('cx',r=>x(+r[xkey])).attr('cy',r=>y(+r[ykey])).attr('r',3.4).attr('opacity',.65).attr('fill',color);
  const label=r=>`${r.county_name||'Illustrative point'} · ${xlabel}: ${number(r[xkey])} · ${ylabel}: ${number(r[ykey])}${r.net_individuals_per_1000!==undefined?' · Net / 1,000: '+number(r.net_individuals_per_1000):''}${r.cluster?' · C'+r.cluster:''}`;
  if(id==='pca-scores'){
    const body=svg.node().parentElement,tip=document.createElement('div');tip.className='score-tooltip';tip.hidden=true;tip.setAttribute('role','tooltip');tip.id='pca-score-tooltip';body.append(tip);
    const countyLabel=r=>`${r.county_name} · PC1: ${number(r.PC1)} · PC2: ${number(r.PC2)} · ${outcome.label}: ${number(r[outcome.rate])} / 1,000`;
    function show(event,r){
      tip.textContent=countyLabel(r);tip.hidden=false;
      const box=body.getBoundingClientRect(),point=this.getBoundingClientRect();
      const px=event.clientX||point.left+point.width/2,py=event.clientY||point.top;
      tip.style.left=Math.max(4,Math.min(px-box.left+12,box.width-tip.offsetWidth-4))+'px';
      tip.style.top=Math.max(4,Math.min(py-box.top+12,box.height-tip.offsetHeight-4))+'px';
    }
    points.attr('tabindex',0).attr('aria-label',countyLabel).attr('aria-describedby',tip.id).on('pointerenter.details pointermove.details focus.details click.details',show).on('pointerleave.details blur.details',()=>tip.hidden=true);
  }else inspect(points,label);
  return {svg,x,y};
}
export function heatmap(id,rows,columns,values,limit=2,percent=false){
  const body=document.querySelector(`#${id} .interactive-body`),width=Math.min(850,Math.max(250,body.clientWidth)),left=id==='pca-associations'?50:width<450?115:210;
  const svg=chartSvg(id,'Interactive matrix',Math.max(260,rows.length*27+90)),height=+svg.attr('viewBox').split(' ')[3];
  svg.attr('viewBox',`0 0 ${width} ${height}`).style('font-size','12px');
  const x=d3.scaleBand().domain(columns).range([left,width-12]).padding(.04),y=d3.scaleBand().domain(rows).range([35,height-55]).padding(.04);
  const color=percent?d3.scaleLinear().domain([0,100]).range(['#f5f0e4','#965030']):d3.scaleLinear().domain([-limit,0,limit]).range(['#3d7067','#f5f0e4','#965030']).clamp(true);
  svg.append('g').attr('transform',`translate(0,${height-55})`).call(d3.axisBottom(x));svg.append('g').attr('transform',`translate(${left-5},0)`).call(d3.axisLeft(y).tickSize(0));
  const cells=rows.flatMap((row,i)=>columns.map((column,j)=>({row,column,value:+values[i][j]})));
  inspect(svg.selectAll('rect').data(cells).join('rect').attr('x',r=>x(r.column)).attr('y',r=>y(r.row)).attr('width',x.bandwidth()).attr('height',y.bandwidth()).attr('fill',r=>color(r.value)),r=>`${r.row} · ${r.column}: ${number(r.value)}${percent?'%':''}`);
  if(columns.length<8)svg.selectAll('.value').data(cells).join('text').attr('class','value').attr('font-size',width<450?9:12).attr('x',r=>x(r.column)+x.bandwidth()/2).attr('y',r=>y(r.row)+y.bandwidth()/2+4).attr('text-anchor','middle').attr('fill',r=>Math.abs(r.value)>(percent?60:limit*.65)?'white':'#293d36').text(r=>number(r.value)+(percent?'%':''));
  colorLegend(id,percent?'Within cluster (%)':limit===2?'Standard deviations':'Correlation',percent?'sequential':'diverging',percent?['0','50','100']:[`−${limit}`,'0',`${limit}`]);
  let lastWidth=width;
  new ResizeObserver(()=>{
    if(!body.isConnected||!body.clientWidth)return;
    const next=Math.min(850,Math.max(250,body.clientWidth));if(next===lastWidth)return;lastWidth=next;
    const margin=id==='pca-associations'?50:next<450?115:210;
    svg.attr('viewBox',`0 0 ${next} ${height}`);x.range([margin,next-12]);
    const axes=svg.selectAll(':scope > g');
    axes.filter((_,i)=>i===0).call(d3.axisBottom(x));
    axes.filter((_,i)=>i===1).attr('transform',`translate(${margin-5},0)`).call(d3.axisLeft(y).tickSize(0));
    svg.selectAll('rect').attr('x',r=>x(r.column)).attr('width',x.bandwidth());
    svg.selectAll('.value').attr('x',r=>x(r.column)+x.bandwidth()/2).attr('font-size',next<450?9:12);
  }).observe(body);
}
function tree(id,data){
  const svg=chart(id),x=d3.scaleLinear().domain([0,data.ivl.length*10]).range([65,820]),y=d3.scaleLinear().domain([0,d3.max(data.dcoord.flat())]).nice().range([330,35]);
  svg.append('g').attr('transform','translate(65,0)').call(d3.axisLeft(y).ticks(5));
  svg.append('text').attr('x',65).attr('y',18).text('Average cosine distance');
  const segments=data.icoord.map((xs,i)=>xs.map((v,j)=>[x(v),y(data.dcoord[i][j]) ]));
  inspect(svg.selectAll('.branch').data(segments).join('path').attr('class','branch').attr('d',d3.line()).attr('fill','none').attr('stroke','#3d7067').attr('stroke-width',2),(_,i)=>'Hierarchy merge');
  svg.selectAll('.leaf').data(data.ivl).join('text').attr('class','leaf').attr('transform',(r,i)=>`translate(${x(i*10+5)},342) rotate(65)`).attr('font-size',10).text(r=>r);
  d3.select(`#${id} .interactive-body`).append('p').attr('class','chart-footnote').text('Hover or focus branches to inspect. Parentheses show county counts in collapsed nodes.');
  inspect(svg.selectAll('.branch'),(_,i)=>`Merge distance ${number(Math.max(...data.dcoord[i]))}`);
}
function boxplot(id,rows,view,o){
  const svg=chart(id),groups=d3.groups(rows,r=>+r[view+'_kmeans']),x=d3.scaleBand().domain(groups.map(([k])=>'C'+k)).range([65,820]).padding(.5),y=d3.scaleLinear().domain(d3.extent(rows,r=>r[o.rate])).nice().range([330,35]);
  chartAxes(svg,x,y,view+' cluster',o.label+' / 1,000');
  for(const [k,items] of groups){const a=items.map(r=>r[o.rate]).sort(d3.ascending),q1=d3.quantile(a,.25),q2=d3.quantile(a,.5),q3=d3.quantile(a,.75),iqr=q3-q1,lo=a.find(v=>v>=q1-1.5*iqr),hi=a.findLast(v=>v<=q3+1.5*iqr),cx=x('C'+k)+x.bandwidth()/2;
    svg.append('line').attr('x1',cx).attr('x2',cx).attr('y1',y(lo)).attr('y2',y(hi)).attr('stroke','#293d36');
    inspect(svg.append('rect').datum(k).attr('x',x('C'+k)).attr('y',y(q3)).attr('width',x.bandwidth()).attr('height',y(q1)-y(q3)).attr('fill',clusterColors[k-1]).attr('opacity',.7),()=>`C${k} · ${items.length} counties · Q1 ${number(q1)} · Median ${number(q2)} · Q3 ${number(q3)} · Whiskers ${number(lo)} to ${number(hi)}`);
    for(const v of [lo,q2,hi])svg.append('line').attr('x1',x('C'+k)).attr('x2',x('C'+k)+x.bandwidth()).attr('y1',y(v)).attr('y2',y(v)).attr('stroke','#293d36');
    inspect(svg.append('g').selectAll('circle').data(items.filter(r=>r[o.rate]<lo||r[o.rate]>hi)).join('circle').attr('cx',cx).attr('cy',r=>y(r[o.rate])).attr('r',3).attr('fill',clusterColors[k-1]),r=>`${r.county_name} · ${o.label} ${number(r[o.rate])} / 1,000`);
  }
  legend(id,['<i class="box-key"></i>Middle 50%','<i class="line-key"></i>Median','<i class="whisker-key"></i>Within 1.5 IQR','<i class="dot-key"></i>Outliers']);
}
export async function clusteringDetails(){
  const host=document.getElementById('clustering-migration-scatter');
  const data=await d3.json('data/clustering/clustering-charts.json');
  if(document.getElementById('clustering-migration-scatter')!==host)return;
  for(const view of ['migration','characteristics']){
    const rows=data.counties.map(r=>({...r,cluster:r[view+'_kmeans']}));
    scatter('clustering-'+view+'-scatter',rows,view==='migration'?'inflow':'PC1',view==='migration'?'outflow':'PC2',r=>clusterColors[r.cluster-1],view==='migration'?'Inflow per 1,000':'PC1',view==='migration'?'Outflow per 1,000':'PC2',view==='migration');
    legend('clustering-'+view+'-scatter',['<i class="dot-key gold"></i>C1','<i class="dot-key slate"></i>C2',...(view==='migration'?['<i class="line-key dashed"></i>Inflow = outflow']:[])]);
    const p=data.profiles[view];
    // Features on rows retain readable labels on narrow displays.
    heatmap('clustering-'+view+'-profiles',p.labels,p.values.map((_,i)=>'C'+(i+1)),p.labels.map((_,j)=>p.values.map(row=>row[j])));
    tree('clustering-'+view+'-dendrogram',data.trees[view]);
  }
  for(const view of ['characteristics','migration'])selectOutcome('clustering-'+view+'-outcomes',o=>boxplot('clustering-'+view+'-outcomes',data.counties,view,o));
  const cs=d3.sort(new Set(data.counties.map(r=>r.characteristics_kmeans))),ms=d3.sort(new Set(data.counties.map(r=>r.migration_kmeans)));
  heatmap('clustering-cross-view',cs.map(c=>'Characteristics C'+c),ms.map(c=>'Migration C'+c),cs.map(c=>ms.map(m=>100*data.counties.filter(r=>r.characteristics_kmeans===c&&r.migration_kmeans===m).length/data.counties.filter(r=>r.characteristics_kmeans===c).length)),100,true);
  const toy=data.toy,points=toy.points.map((p,i)=>({x:p[0],y:p[1],cluster:toy.labels[i]+1}));
  const {svg,x,y}=scatter('clustering-overview-partitional',points,'x','y',r=>clusterColors[r.cluster-1],'Feature 1','Feature 2');
  inspect(svg.selectAll('.center').data(toy.centers).join('path').attr('class','center').attr('d',d3.symbol().type(d3.symbolCross).size(140)).attr('transform',p=>`translate(${x(p[0])},${y(p[1])})`).attr('fill','#293d36'),p=>`Centroid: ${number(p[0])}, ${number(p[1])}`);
  legend('clustering-overview-partitional',['<i class="dot-key gold"></i><i class="dot-key slate"></i><i class="dot-key teal"></i>Illustrative groups','<b aria-hidden="true">✚</b> Centroids']);tree('clustering-overview-hierarchy',data.trees.toy);
}
export async function pcaDetails({pcaResults:d}){
  const host=document.getElementById('pca-scores');
  const [loadings,scores,quintiles,toy]=await Promise.all([d3.csv('data/pca/pca-variable-correlations.csv'),d3.csv('data/pca/pca-county-scores.csv'),d3.csv('data/pca/pca-score-quintiles.csv'),d3.json('data/pca/pca-toy.json')]);
  if(document.getElementById('pca-scores')!==host)return;
  const pcs=d.variance.slice(0,d.retained).map(r=>r.component);
  heatmap('pca-loadings',d.feature_labels,pcs,loadings.map(row=>pcs.map(pc=>+row[pc])),1);
  selectOutcome('pca-scores',o=>{const limit=d.color_limits[o.id],color=d3.scaleLinear().domain(o.id==='net'?[-limit,0,limit]:[0,limit]).range(o.id==='net'?['#3d7067','#f5f0e4','#965030']:(o.id==='inflow'?['#f5f0e4','#965030']:['#f5f0e4','#3d7067'])).clamp(true);
    scatter('pca-scores',scores,'PC1','PC2',r=>color(+r[o.rate]),'PC1','PC2',false,o);colorLegend('pca-scores',o.label+' / 1,000 residents',o.id==='net'?'diverging':o.id==='inflow'?'sequential':'outflow',[o.id==='net'?number(-limit):'0',o.id==='net'?'0':number(limit/2),number(limit)]);});
  const root=d3.select('#pca-quintiles .interactive-body');root.append('label').text('Component ').append('select').attr('class','component-select').attr('aria-label','Quintile component').selectAll('option').data(pcs).join('option').text(r=>r);
  root.node().insertAdjacentHTML('afterbegin',outcomeSelect('Quintile outcome'));
  const card=root.node().closest('.chart-card');root.selectAll('label').each(function(){cardControls(card,this);});
  function draw(){root.selectAll('svg,.chart-tooltip').remove();const pc=card.querySelector('.component-select').value,o=outcomeById(card.querySelector('.outcome-select').value),all=quintiles.filter(r=>r.outcome===o.id),rows=all.filter(r=>r.component===pc),svg=chart('pca-quintiles'),x=d3.scaleLinear().domain([1,5]).range([65,820]),y=d3.scaleLinear().domain(d3.extent(all.flatMap(r=>[+r.q25,+r.q75]))).nice().range([330,35]);svg.attr('aria-label',o.label+' by '+pc+' score quintile');chartAxes(svg,x,y,'Score quintile (low → high)',o.label+': median and middle 50%');svg.select('.x-axis').call(d3.axisBottom(x).tickValues([1,2,3,4,5]).tickFormat(d3.format('d')));
    svg.selectAll('.interval').data(rows).join('line').attr('class','interval').attr('x1',r=>x(+r.quintile)).attr('x2',r=>x(+r.quintile)).attr('y1',r=>y(+r.q25)).attr('y2',r=>y(+r.q75)).attr('stroke','#3d7067').attr('stroke-width',4);
    svg.append('path').datum(rows).attr('d',d3.line().x(r=>x(+r.quintile)).y(r=>y(+r.median))).attr('fill','none').attr('stroke','#965030');
    inspect(svg.selectAll('circle').data(rows).join('circle').attr('cx',r=>x(+r.quintile)).attr('cy',r=>y(+r.median)).attr('r',6).attr('fill','#965030'),r=>`${pc} · ${o.label} · Q${r.quintile} · n=${r.counties} · Median ${number(r.median)} · IQR ${number(r.q25)}–${number(r.q75)}`);
  }d3.select(card).selectAll('select').on('change',draw);draw();
  legend('pca-quintiles',['<i class="dot-key gold"></i>Median','<i class="whisker-key"></i>Middle 50%']);
  const {svg,x,y}=scatter('pca-overview-directions',toy.points.map(p=>({x:p[0],y:p[1]})),'x','y',()=>clusterColors[1],'Centered feature A','Centered feature B');
  svg.append('defs').append('marker').attr('id','pc-arrow').attr('viewBox','0 0 10 10').attr('refX',9).attr('refY',5).attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto').append('path').attr('d','M0,0 L10,5 L0,10 Z').attr('fill','#293d36');
  toy.vectors.forEach((v,i)=>{svg.append('line').attr('x1',x(0)).attr('y1',y(0)).attr('x2',x(v[0])).attr('y2',y(v[1])).attr('stroke','#293d36').attr('stroke-width',3).attr('marker-end','url(#pc-arrow)');svg.append('text').attr('x',x(v[0])+8).attr('y',y(v[1])-8).text('PC'+(i+1));});
  const steps=['13 county characteristics','Log transforms and standardization','PCA scores and variable correlations','Compare scores with migration'];
  d3.select('#pca-overview-workflow .interactive-body').append('ol').attr('class','workflow').attr('aria-label','Analysis workflow, from left to right').selectAll('li').data(steps).join('li').text(r=>r);
}
