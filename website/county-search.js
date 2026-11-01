// Use display geography so state searches include counties with unavailable data.
export function countySearchEntries(geo, states) {
  const stateNames = new Map(states.features.map(f => [f.id, f.properties.name]));
  return geo.features.map(f => ({id: f.id, name: `${f.properties.name}, ${stateNames.get(f.id.slice(0, 2))}`}));
}

export function attachCountySearch(input, suggestions, entries, choose) {
  const counties = [...entries].sort((a, b) => a.name.localeCompare(b.name));
  input.placeholder = 'Search by county or state';
  input.setAttribute('aria-controls', suggestions.id);
  input.setAttribute('aria-expanded', 'false');
  function hide() {
    suggestions.hidden = true;
    suggestions.replaceChildren();
    input.setAttribute('aria-expanded', 'false');
  }
  function suggest() {
    hide();
    input.setCustomValidity('');
    const query = input.value.trim().toLowerCase();
    if (!query) return;
    const state = c => c.name.includes(',') ? c.name.split(',').at(-1).trim().toLowerCase() : '';
    const isState = counties.some(c => state(c) === query);
    const matches = counties.filter(c => isState ? state(c) === query || c.name.toLowerCase() === query+' (state)' : c.name.toLowerCase().includes(query) || c.id.startsWith(query));
    suggestions.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    if (!matches.length) suggestions.textContent = 'No matching county or state.';
    for (const county of matches) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = county.name;
      button.onclick = () => { hide(); choose(county.id); input.focus(); };
      suggestions.append(button);
    }
  }
  input.addEventListener('input', suggest);
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowDown' && !suggestions.hidden) {
      e.preventDefault(); suggestions.querySelector('button')?.focus();
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const exact = counties.find(c => c.id === input.value.trim() || c.name.toLowerCase() === input.value.trim().toLowerCase());
      if (exact) { hide(); choose(exact.id); }
      else suggestions.querySelector('button')?.click();
    }
  });
  suggestions.addEventListener('keydown', e => {
    if (e.key === 'Escape') { hide(); input.focus(); }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const buttons = [...suggestions.querySelectorAll('button')], index = buttons.indexOf(document.activeElement);
      buttons[(index + (e.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length]?.focus();
    }
  });
  input.parentElement.addEventListener('focusout', e => {
    if (!input.parentElement.contains(e.relatedTarget)) hide();
  });
  return {hide, suggest};
}
