import {clusteringDetails,clusterColors,inspect} from './analysis-details.js';
import {drawClusterMap} from './cluster-map.js';
import {d3} from '../vendor.js';
import {fmt} from '../shared.js';
import {chartSvg,chartAxes,pointLabel} from './chart-utils.js';
export async function drawCharts({clusteringResults,geo,states}) {
  const svg=chartSvg('cluster-selection','Silhouette by cluster count and method'), x=d3.scaleLinear().domain([2,8]).range([65,820]), y=d3.scaleLinear().domain([-1,1]).range([330,35]);
  chartAxes(svg,x,y,'Number of clusters k','Mean silhouette');
  svg.select('.x-axis').call(d3.axisBottom(x).tickValues(d3.range(2,9)).tickFormat(d3.format('d')));
  const groups=d3.groups(clusteringResults.metrics,r=>`${r.view} / ${r.method}`);
  const colors=groups.map(([name])=>name.startsWith('migration')?'#b27c16':'#697787');
  groups.forEach(([name,rows],i)=>{
    svg.append('path').datum(rows).attr('d',d3.line().x(r=>x(r.k)).y(r=>y(r.silhouette))).attr('fill','none').attr('stroke',colors[i]).attr('stroke-width',2).attr('stroke-dasharray',name.includes('hierarchical')?'6 3':null);
    inspect(svg.append('g').selectAll('circle').data(rows).join('circle').attr('cx',r=>x(r.k)).attr('cy',r=>y(r.silhouette)).attr('r',5).attr('fill',colors[i]),r=>`${name}, k=${r.k}, silhouette=${r.silhouette.toFixed(3)}`);
  });
  const legend=d3.select('#cluster-selection .interactive-body').append('div').attr('class','legend-card').attr('aria-label','Cluster selection legend');
  legend.append('strong').text('Reading this chart');
  groups.forEach(([name],i)=>{const item=legend.append('span');item.append('i').attr('class','line-key').style('border-color',colors[i]).style('border-top-style',name.includes('hierarchical')?'dashed':'solid');item.append('span').text(name.replace('kmeans','k-means · Euclidean').replace('hierarchical','hierarchy · cosine'));});

  await Promise.all([drawClusterMap({clusteringResults,geo,states}), clusteringDetails()]);
}
function showChartError(error){document.querySelectorAll('[data-analysis-chart] .interactive-body:empty').forEach(el=>el.textContent='Chart data could not load. Reload to retry. '+error.message);}
