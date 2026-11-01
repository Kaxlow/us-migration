import {Plotly,d3} from '../vendor.js';
const layout={paper_bgcolor:'#ffffff',plot_bgcolor:'#ffffff',font:{family:'Noto Sans, sans-serif',color:'#293d36',size:11},margin:{l:90,r:15,t:20,b:75},height:360};
const config={responsive:true,displayModeBar:false};
export function initSupervised(data){
 const plots=[];
 const observer=new ResizeObserver(entries=>{for(const {target} of entries){if(target.data&&target.clientWidth>0)Plotly.relayout(target,{width:target.clientWidth});}});
 for(const article of document.querySelectorAll('.supervised-task')){
  const outcome=article.dataset.outcome;
  const t=outcome==='inflow'?data.naiveBayesResults.tasks[outcome]:data.decisionTreeResults.tasks[outcome];
  const mode=article.querySelector('.confusion-mode');
  const confusion=document.getElementById(outcome+'-confusion');
  const draw=()=>{const normalized=mode.value==='normalized',z=normalized?t.model.confusion_normalized:t.model.confusion;
   Plotly.react(confusion,[{type:'heatmap',z,x:t.model.classes,y:t.model.classes,colorscale:[[0,'#f8f3e8'],[0.5,'#8eafa0'],[1,'#293d36']],zmin:0,zmax:normalized?1:Math.max(...z.flat()),showscale:false,
    text:z.map(row=>row.map(v=>normalized?(v*100).toFixed(1)+'%':String(v))),texttemplate:'%{text}',
    hovertemplate:'Actual %{y}<br>Predicted %{x}<br>%{text}<extra></extra>'}],
    {...layout,width:confusion.clientWidth,margin:{l:confusion.clientWidth<400?65:90,r:10,t:20,b:75},xaxis:{title:{text:'Predicted class'},automargin:true},yaxis:{title:{text:'Actual class'},autorange:'reversed',automargin:true}},config);};
  draw();mode.addEventListener('change',draw);plots.push(confusion);
  const comparison=document.getElementById(outcome+'-comparison');
  const candidates=t.tuning.map((r,i)=>'Candidate '+(i+1));
  const settings=t.tuning.map(r=>Object.entries(r).filter(([k])=>!k.endsWith('score')).map(([k,v])=>k+': '+v).join('<br>'));
  Plotly.newPlot(comparison,[{type:'scatter',mode:'lines+markers',name:'Training',x:candidates,y:t.tuning.map(r=>r.mean_train_score),marker:{color:'#965030'},text:settings,hovertemplate:'%{x}<br>%{text}<br>Training F1 %{y:.3f}<extra></extra>'},
   {type:'scatter',mode:'lines+markers',name:'Validation',x:candidates,y:t.tuning.map(r=>r.mean_test_score),marker:{color:'#3d7067'},error_y:{type:'data',array:t.tuning.map(r=>r.std_test_score),visible:true},text:settings,hovertemplate:'%{x}<br>%{text}<br>Validation F1 %{y:.3f}<extra></extra>'}],
   {...layout,width:comparison.clientWidth,margin:{l:55,r:15,t:15,b:95},yaxis:{title:{text:'Macro-F1'},range:[0,1]},xaxis:{tickangle:-45,nticks:6},legend:{orientation:'h',y:1.15}},config);plots.push(comparison);
 }
 const target=document.getElementById('tree-target'),depth=document.getElementById('tree-depth');
 if(target){
  function drawTree(){
   const outcome=target.value,tree=data.decisionTreeResults.tasks[outcome].trees.find(t=>t.depth===Number(depth.value));
   const root=d3.hierarchy(tree.root);
   d3.tree().nodeSize([68,270])(root);
   const [low,high]=d3.extent(root.descendants(),d=>d.x);
   const height=Math.max(260,high-low+80),width=(root.height+1)*270;
   root.each(d=>d.x+=40-low);
   const host=document.querySelector('.tree-scroll');host.replaceChildren();
   const svg=d3.select(host).append('svg').attr('width',width).attr('height',height).attr('role','group').attr('aria-label',`${outcome} tree, maximum depth ${tree.depth}`);
   const group=svg.append('g').attr('transform','translate(15,0)');
   group.selectAll('path').data(root.links()).join('path').attr('d',d3.linkHorizontal().x(d=>d.y+110).y(d=>d.x)).attr('fill','none').attr('stroke','#bbae90');
   const detail=document.querySelector('.tree-node-detail');
   function inspect(d){detail.textContent=`Node ${d.data.id}: ${d.data.samples} training counties; predicts ${d.data.prediction}; impurity ${d.data.impurity.toFixed(3)}. `+Object.entries(d.data.proportions).map(([c,p])=>`${c}: ${(p*100).toFixed(1)}%`).join('; ');}
   const nodes=group.selectAll('g').data(root.descendants()).join('g').attr('transform',d=>`translate(${d.y},${d.x})`).attr('tabindex',0).attr('role','button')
    .attr('aria-label',d=>`Node ${d.data.id}: ${d.data.feature?d.data.feature+' at '+d.data.threshold.toFixed(3):'Leaf predicts '+d.data.prediction}; ${d.data.samples} counties`)
    .on('focus',(event,d)=>inspect(d)).on('click',(event,d)=>inspect(d)).on('keydown',(event,d)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();inspect(d);}});
   nodes.append('rect').attr('y',-22).attr('width',240).attr('height',44).attr('rx',5).attr('fill',d=>d.children?'#eee7d7':'#dcece6').attr('stroke','#965030');
   nodes.append('text').attr('x',8).attr('y',-5).attr('font-size',10).text(d=>d.data.feature?d.data.feature+' ≤ '+d.data.threshold.toFixed(2):d.data.prediction);
   nodes.append('text').attr('x',8).attr('y',11).attr('font-size',10).text(d=>`${d.data.samples} counties · ${d.data.prediction}`);
   document.querySelector('.tree-summary').textContent=`${tree.params.criterion}; minimum leaf ${tree.params.min_samples_leaf}; ${tree.node_count} nodes and ${tree.leaf_count} leaves. Validation macro-F1 ${tree.cv_macro_f1.toFixed(3)}.`;
   document.querySelector('.tree-downloads').innerHTML=`<a href="assets/classification/${outcome}-tree-${tree.depth}.svg" target="_blank" rel="noopener">Open full-size tree ↗</a> · <a href="data/classification/${outcome}-tree-${tree.depth}.txt" download>Download decision rules ↓</a>`;
   inspect(root);
  }
  target.addEventListener('change',drawTree);depth.addEventListener('change',drawTree);drawTree();
 }
 plots.forEach(p=>observer.observe(p));
 return ()=>{observer.disconnect();plots.forEach(p=>Plotly.purge(p));};
}
