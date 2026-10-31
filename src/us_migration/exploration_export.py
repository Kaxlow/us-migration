"""Package measured EDA tables for the static presentation."""
from pathlib import Path
import json, hashlib
import pandas as pd
from .outcomes import OUTCOME_DEFINITIONS, COUNT_FIELDS, RATE_FIELDS, color_limits

def export_exploration(root, directory):
    ROOT, OUT = Path(root), Path(directory)
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'data/processed/analysis_county_year.parquet'
    data = pd.read_parquet(source)
    county = data.loc[data.geography_level.eq('county')]
    latest = int(county.year.max())
    cross = county.loc[county.year.eq(latest)]
    fields = ['county_fips','county_name','population','median_age','median_household_income','median_home_value','median_gross_rent','poverty_pct','unemployment_pct','vacancy_pct','homeownership_pct','bachelors_plus_pct','declarations','precipitation_inches','temperature_f','inflow_individuals_per_1000','outflow_individuals_per_1000','net_individuals_per_1000','education_band']
    fields = list(dict.fromkeys(fields + COUNT_FIELDS))
    migration_fields = ['county_fips','county_name','population','geography_level'] + COUNT_FIELDS + RATE_FIELDS
    migration = {str(year): json.loads(g[migration_fields].round(4).to_json(orient='values')) for year,g in data.groupby('year')}
    captions = pd.read_csv(OUT/'eda_chart_catalog.csv').caption.tolist()
    matrix = pd.read_csv(OUT/'validated_latest_year_spearman.csv',index_col=0)
    pearson = pd.read_csv(OUT/'validated_latest_year_pearson.csv',index_col=0)
    pairs = pd.read_csv(OUT/'validated_latest_year_pair_counts.csv',index_col=0)
    from .eda import FEATURES
    ranks = []
    for outcome in OUTCOME_DEFINITIONS:
        field = outcome['rate']
        frame = pd.DataFrame({'spearman':matrix[field], 'pearson':pearson[field], 'pair_count':pairs[field]}).loc[FEATURES]
        frame = frame.loc[frame.spearman.abs().sort_values(ascending=False).index]
        frame.index.name = 'feature'
        frame['outcome'] = outcome['id']
        ranks.append(frame)
    pd.concat(ranks).to_csv(OUT/'migration_correlations.csv')
    result = {'latest':latest,'rows':len(data),'counties':len(cross),'years':sorted(int(y) for y in data.year.unique()),'fields':fields,'cross':json.loads(cross[fields].round(5).to_json(orient='values')),'migrationFields':migration_fields,'migration':migration,'captions':captions,'trend':json.loads(pd.read_csv(OUT/'chart03_balanced_trend.csv').to_json(orient='records')),'correlation':{'fields':matrix.columns.tolist(),'values':matrix.round(4).values.tolist()},'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    result.update(outcomes=OUTCOME_DEFINITIONS, colorLimits=color_limits(data))
    result['outcomeCaptions'] = {o['id']: [f"{o['label']} · {o['units']}. " + caption for caption in captions] for o in OUTCOME_DEFINITIONS}
    for key, filename in [('rateRankings','chart05_county_rankings.csv'),('countRankings','migration_count_rankings.csv'),('associations','migration_correlations.csv')]:
        table = pd.read_csv(OUT/filename, dtype={'county_fips':str})
        result[key] = json.loads(table.to_json(orient='records'))
        table.to_csv(OUT/filename,index=False)
    (OUT/'analysis.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    (OUT/'outcomes.json').write_text(json.dumps(OUTCOME_DEFINITIONS,indent=2)+'\n',encoding='utf-8')
    cross[fields].to_csv(OUT/'latest-counties.csv',index=False)
