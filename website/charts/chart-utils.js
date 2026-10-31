import {d3} from '../vendor.js';
export function interactiveCard(id, title, caption) {
  return `<figure class="chart-card interactive-result" id="${id}"><h3>${title}</h3><div class="interactive-body"></div><figcaption class="caption">${caption}</figcaption></figure>`;
}
export function chartSvg(id, label, height=390) {
  return d3.select(`#${id} .interactive-body`).append('svg').attr('viewBox',`0 0 850 ${height}`).attr('role','img').attr('aria-label',label);
}
export function chartAxes(svg,x,y,xlabel,ylabel) {
  svg.append('g').attr('class','x-axis').attr('transform','translate(0,330)').call(d3.axisBottom(x));
  svg.append('g').attr('transform','translate(65,0)').call(d3.axisLeft(y).ticks(6));
  svg.append('text').attr('x',440).attr('y',380).attr('text-anchor','middle').text(xlabel);
  svg.append('text').attr('x',65).attr('y',18).text(ylabel);
}
export function pointLabel(selection, label) {
  selection.attr('tabindex',0).attr('aria-label',label).append('title').text(label);
}
