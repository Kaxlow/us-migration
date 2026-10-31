import {pcaDetails,inspect,heatmap} from './analysis-details.js';
import {d3} from '../vendor.js';
import {fmt} from '../shared.js';
import {chartSvg,chartAxes,pointLabel} from './chart-utils.js';
export async function drawCharts({pcaResults}) {
    const detailWork=pcaDetails({pcaResults});
    const d=pcaResults, svg=chartSvg('pca-variance','Individual and cumulative PCA variance');
    const x=d3.scaleBand().domain(d.variance.map(r=>r.component)).range([65,820]).padding(.25), y=d3.scaleLinear().domain([0,1]).range([330,35]);
    chartAxes(svg,x,y,'Principal component','Proportion of feature variance');
    inspect(svg.selectAll('.bar').data(d.variance).join('rect').attr('x',r=>x(r.component)).attr('y',r=>y(r.variance_ratio)).attr('width',x.bandwidth()).attr('height',r=>330-y(r.variance_ratio)).attr('fill',(r,i)=>i<d.retained?'#a55335':'#bab4a1'),r=>`${r.component}: ${(100*r.variance_ratio).toFixed(1)}% variance; ${(100*r.cumulative).toFixed(1)}% cumulative`);
    svg.append('path').datum(d.variance).attr('d',d3.line().x(r=>x(r.component)+x.bandwidth()/2).y(r=>y(r.cumulative))).attr('fill','none').attr('stroke','#315f58').attr('stroke-width',3);
    svg.append('line').attr('x1',65).attr('x2',820).attr('y1',y(.8)).attr('y2',y(.8)).attr('stroke','#315f58').attr('stroke-dasharray','6 4');
    d3.select('#pca-variance .interactive-body').append('div').attr('class','legend-card').html('<span><i class="box-key" style="background:#a55335"></i>Retained components</span><span><i class="box-key" style="background:#bab4a1"></i>Other components</span><span><i class="line-key" style="border-color:#315f58"></i>Cumulative variance</span><span><i class="line-key dashed" style="border-color:#315f58"></i>80% threshold</span>');
    heatmap('pca-associations',d.variance.slice(0,d.retained).map(r=>r.component),d.outcomes.map(o=>o.label),d.variance.slice(0,d.retained).map(r=>d.outcomes.map(o=>d.associations.find(a=>a.component===r.component&&a.outcome===o.id).spearman_rho)),1);
    await detailWork;
}
