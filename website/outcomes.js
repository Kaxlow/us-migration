// Definitions are exported from the shared Python outcome contract.
export const outcomes = await fetch('data/outcomes.json').then(r=>{if(!r.ok)throw Error('Outcome definitions unavailable');return r.json();});
export function outcomeSelect(label='Migration outcome') {
  return `<label class="outcome-control">${label} <select class="outcome-select" aria-label="${label}">${outcomes.map(o=>`<option value="${o.id}">${o.label}</option>`).join('')}</select></label>`;
}
export const outcomeById=id=>outcomes.find(o=>o.id===id);
export function cardControls(card, label) {
  let header=card.querySelector('.card-header');
  if(!header){header=document.createElement('div');header.className='card-header';card.prepend(header);header.append(card.querySelector('h3'));}
  let controls=header.querySelector('.card-controls');
  if(!controls){controls=document.createElement('div');controls.className='card-controls';header.append(controls);}
  controls.append(label);
}
