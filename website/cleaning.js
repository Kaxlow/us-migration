/* Descriptions follow notebook 01; evidence is exported from its saved outputs. */
const cleaningStages = [
  {
    title: 'ACS characteristics', reference: 'Notebook section 2',
    text: 'Preserve zero-padded FIPS, the five-year reference window, estimates, and margins of error. Convert negative special codes to flagged missing values and calculate percentages only with valid positive denominators. Reconstruct unavailable historical employment and education measures from same-window B23001 and B15002 cells; retain reconstruction flags and component-based margins of error. Process official Alaska and Connecticut state supplements separately.',
    image: '01_acs_raw_vs_clean',
    imageCaption: 'Raw ACS estimates beside cleaned values. Special codes become missing values with provenance flags; unchanged valid estimates are retained.',
    evidence: [['2.7.', 'Compare raw income, cleaned income, and the recorded reason']]
  },
  {
    title: 'IRS migration records', reference: 'Notebook section 3',
    text: 'Normalize historical workbook and CSV layouts, remove embedded headers, construct geographic identifiers, and mask suppression markers. Keep legitimate negative adjusted gross income. Classify pairs, nonmigrants, domestic totals, and foreign or special rows; orient origin and destination consistently. Collapse exact repeated county pairs, reject conflicting measurements, and use published domestic totals. Select interstate totals for Alaska and Connecticut.',
    image: '02_irs_raw_vs_clean',
    imageCaption: 'Original repeated county-pair records versus the canonical deduplicated flow table. The saved output below separately shows suppression handling.',
    evidence: [['3.8.', 'Suppression audit and matching raw-versus-cleaned individuals']]
  },
  {
    title: 'ACS migration flows', reference: 'Notebook section 4',
    text: 'Read historical fixed-width tables or Census JSON responses, preserve geographic codes and five-year windows, and retain mover estimates with their margins of error. Distinguish domestic origins from named foreign regions that reuse a code. Validate destination-origin-year uniqueness and nonnegative available estimates. Save county-origin and state-origin flows separately so their geography levels are never conflated.',
    image: '03_acs_flows_raw_vs_clean',
    imageCaption: 'Raw origin codes and names versus cleaned, distinct origin identifiers for the same example records.',
    evidence: [['4.4.', 'Validate transformed origin identities']]
  },
  {
    title: 'FEMA disaster records', reference: 'Notebook section 5',
    text: 'Parse dates and geographic codes, calculate inclusive durations, and inspect missing or invalid dates. For missing end dates, exclude affected declarations when at most 5% are missing; otherwise estimate eligible durations using incidents whose start and end dates are on or before December 31, 2018, and flag the estimates. Never substitute declaration dates for missing incident starts. Map explicit statewide records and unambiguous tribal areas using Census land overlaps, retaining unresolved areas in an audit. Deduplicate official incident IDs across declaration numbers and count each incident once per analysis geography at its earliest local start year. Where an incident ID is unavailable, use the declaration number and record the fallback method.',
    image: '04_fema_raw_vs_clean',
    imageCaption: 'Raw FEMA date records versus completed and flagged records. Incident deduplication follows date cleaning and geographic mapping.',
    evidence: [['5.5.', 'Matching records before and after date completion']]
  },
  {
    title: 'NOAA climate measurements', reference: 'Notebook section 6',
    text: 'Parse fixed-width monthly data, map NOAA climate-state codes to Census FIPS (including the DC exception), and reshape the twelve monthly columns into observations. Replace temperature and precipitation sentinels with flagged missing values. Require twelve valid months for annual mean temperature and annual precipitation totals. Save incomplete-year audits and use official statewide climate series for Alaska and Connecticut.',
    image: '05_noaa_raw_vs_clean',
    imageCaption: 'Raw DC temperature values versus cleaned monthly observations. Future months with sentinel values remain missing.',
    evidence: [['6.4.', 'All twelve months: raw value, clean value, and sentinel flag']]
  },
  {
    title: 'Join the datasets', reference: 'Notebook section 7',
    text: 'Join ACS characteristics, published IRS domestic totals, FEMA incident counts, and annual climate by analysis geography and year. Enforce one record per join key. Use state observations for Alaska and Connecticut; the other analysis units remain counties. Fill absent FEMA counts with zero only for completed, covered years. Calculate net inflow minus outflow and descriptive rates per 1,000 ACS residents. ACS migration-flow tables remain separate supporting products.',
    evidence: [['7.3.', 'Before joining: snapshots of the cleaned source tables'], ['7.2.', 'After assembly: saved table inventory, including the county-year panel']],
    note: 'The source-table previews show the inputs to the join. The table inventory and combined records show the resulting dataset.'
  },
  {
    title: 'Data quality checks', reference: 'Notebook section 8',
    text: 'Recover identifiers only from unique same-year reference matches. Inspect missing and nonfinite values, duplicate keys, impossible percentages, invalid counts, age and climate ranges, and migration arithmetic. Record exclusion reasons rather than silently removing rows. Hold out denominator-review rates above 1,000 per 1,000; preserve ordinary IQR extremes with flags. Run the same quality rules again after imputation to validate the final dataset.',
    evidence: [['8.5.', 'Before imputation: rule violations and the denominator-review example'], ['9.5.', 'After imputation and selection: final completeness audit']],
    note: 'The before/after views are quality-audit snapshots. Flagged rules can overlap, so their counts are not additive.'
  },
  {
    title: 'Impute missing data and publish', reference: 'Notebook section 9',
    text: 'Fit socioeconomic donor medians on 2009-2018 training observations only, with state medians and a training-wide fallback. Fit monetary donors in common 2024 CPI-U dollars, then convert fills back to the receiving year; preserve observed values. Scale eligible counts by population, bound imputed counts by their universes, and recalculate derived percentages. Never median-fill migration outcomes, population, climate, or education and employment counts. Apply the quality rules again and publish the validated dataset with imputation flags, exclusions, and retention summaries.',
    evidence: [['9.3.', 'Imputed values by variable, split coverage, and post-imputation exclusions'], ['9.4.', 'After preparation: transformed records and year-by-year retention']],
    note: 'Validation uses 2019-2020 and testing uses 2021-2023. Saved outputs report 49,717 input rows, 46,026 accepted rows, and 3,691 exclusions. No missing values, infinities, or duplicate keys remain in the final cohort.'
  }
];

function cleaningContent() {
  return `<p>Data preparation preserves the original records, standardizes each source, and combines comparable geography-year observations. The process then checks data quality, fills eligible missing socioeconomic values using training data only, and validates the final analysis dataset. The comparisons and audit tables below show what changed at each stage. For the full implementation, saved cell outputs, and additional checks, see the <a href="${base}notebooks/01_data_cleaning.ipynb">Data Cleaning notebook</a>.</p>
    <h3>Prepare and verify the source records</h3><p>Read the download catalog and verify snapshot checksums. Keep raw files separate from cleaned outputs and retain source hashes for traceability. Store geographic codes as strings to preserve leading zeros, normalize formatted numeric values, and record each source's reference period: IRS interval-ending years, ACS five-year windows, FEMA incident-start years, and NOAA calendar years.</p>
    <div class="cleaning-sequence">${cleaningStages.map((stage, index) => `
      <article class="cleaning-stage" id="cleaning-${index + 1}">
        <h3><span>${String(index + 1).padStart(2, '0')}</span> ${stage.title}</h3>
        <p>${stage.text}</p>
        ${stage.image ? `<figure class="cleaning-comparison"><a href="assets/cleaning/${stage.image}.png"><img loading="lazy" src="assets/cleaning/${stage.image}.png" alt="Raw versus cleaned comparison for ${stage.title}"></a><figcaption>${stage.imageCaption} Select the image to inspect it at full size.</figcaption></figure>` : ''}
        ${stage.evidence.map(([key, label]) => `<details class="notebook-evidence" ${index >= 5 ? 'open' : ''}><summary>${label}</summary>
          ${cleaningEvidence.sections[key].outputs.map(output => `<div class="notebook-output"><div class="table-scroll" tabindex="0" aria-label="Data preparation output: ${esc(label)}">${output.html}</div></div>`).join('')}
        </details>`).join('')}
        ${index === 5 || index === 7 ? `<div class="notebook-output"><p class="caption">${index === 5 ? 'After joining: five rows from the saved county-year panel.' : 'Before and after imputation: the same records in the original panel and prepared export, before final row selection.'}</p><div class="table-scroll" tabindex="0" aria-label="${index === 5 ? 'Joined dataset snapshot' : 'Paired imputation snapshot'}">${cleaningEvidence.exportSnapshots[index === 5 ? 'joined' : 'imputed']}</div></div>` : ''}
        ${stage.note ? `<p class="caption">${stage.note}</p>` : ''}
      </article>`).join('')}</div>`;
}
