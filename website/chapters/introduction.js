import {base, esc, pct, prose} from '../shared.js';
import {mapMarkup, drawMap} from '../charts/maps.js';

export function render({population,intro}) {
  const paragraphs=(start,end)=>intro.paragraphs.slice(start,end).map(p=>`<p>${prose(p)}</p>`).join('');
  return `<section class="section"><h2>Changing Populations</h2>${mapMarkup('population-map')}
  <p class="caption">Figure 1. Percent change in county population, 2024–2025. <a href="${population.source}">U.S. Census Bureau, Vintage 2025 Population Estimates</a>. <a href="${base}scripts/build_population_map.py">Computation code ↗</a></p>
  ${paragraphs(0,2)}</section>
  <section class="section"><h2>Why Migration Matters</h2>${paragraphs(2,3)}</section>
  <section class="section"><h2>Uneven Outcomes</h2>${paragraphs(3,4)}${growthComparison(population)}</section>
  <section class="section"><h2>Responses to Migration</h2>${paragraphs(4,6)}</section>
  <section class="section"><h2>Research Framework</h2><div class="research-root">How are counties’ economic, demographic, and environmental characteristics associated with net migration, inflows, and outflows?</div><div class="questions">${intro.questions.map((q,i)=>`<div class="question"><b>${String(i+1).padStart(2,'0')}</b><span>${esc(q)}</span></div>`).join('')}</div><div class="prose"><p>The analysis measures county-level domestic migration<a href="#introduction/geography-note" class="footnote">¹</a> through three coequal outcomes: net migration, inflows, and outflows. Economic, housing, demographic, and environmental characteristics provide complementary views of each community. Current features include income, unemployment, housing values and rent, age, education, temperature, precipitation, and disaster history. Employment growth, affordability measures, population density, drought, and wider hazard exposure are planned extensions.</p><p>Together, these questions move from describing where migration is occurring, to examining associated factors, discovering county profiles, and testing prediction. Exploratory analysis, unsupervised learning, and supervised learning form the research agenda; clustering and PCA results are presented in the next two chapters.</p><p id="geography-note" class="caption">¹ Alaska and Connecticut use official state-level ACS and NOAA characteristics and IRS interstate flows because county-equivalent boundaries changed during the study period. They are labeled as states and excluded from county-only EDA charts. Other county boundaries retain their source-year geography.</p></div></section>`;
}
export function init(data) {
  document.querySelectorAll('[data-growth]').forEach(el=>el.textContent=pct(data.population.groups[+el.dataset.growth].change));
  drawMap('population-map',false,data);
  const map=document.getElementById('population-map');
  map.querySelector('.map-footnotes').append(map.parentElement.nextElementSibling);
}
function growthComparison(population){const names=['Metropolitan areas','Micropolitan areas','Outside metropolitan and micropolitan areas'],max=Math.max(...population.groups.map(g=>Math.abs(g.change)));return `<figure class="growth-comparison"><figcaption>Population growth, 2024–2025</figcaption>${population.groups.map((g,i)=>`<div class="growth-row"><span>${names[i]}</span><div class="growth-track"><div class="growth-bar" style="width:${Math.abs(g.change)/max*100}%"></div></div><strong>${pct(g.change)}</strong></div>`).join('')}<p class="caption">Growth of summed populations, not the average county percentage. Classification: <a href="${population.classificationSource}">Vintage 2025 CBSA components</a>.</p></figure>`;}
