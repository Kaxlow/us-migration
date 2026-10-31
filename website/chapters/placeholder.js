import {esc} from '../shared.js';
export function render(title='Analysis') {
  return `<section class="section"><h2 id="section-overview">Planned analysis</h2><div class="prose"><p>${esc(title)} belongs to the future research agenda. The current evidence covers exploration, clustering, PCA, and retrospective classification.</p><p>Prediction of migration magnitudes will require publication-date-aware predictors and fresh temporal and geographic evaluation.</p><p><a href="#conclusion/section-future-work">Read the remaining research questions →</a></p></div></section>`;
}
export function init(){}
