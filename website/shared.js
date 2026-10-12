export const base = 'https://github.com/Kaxlow/us-migration/blob/main/';
export const esc = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt = n => Number(n).toLocaleString('en-US',{maximumFractionDigits:1});
export const pct = n => `${n>=0?'+':''}${n.toFixed(2)}%`;
export const prose = p => p.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/\*(.*?)\*/g,'<em>$1</em>');
