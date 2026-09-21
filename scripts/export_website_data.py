"""Export existing analysis results for the static website (no recleaning)."""
from pathlib import Path
import json
import shutil
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'website/data'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'data/processed/analysis_county_year.parquet'
    data = pd.read_parquet(source)
    county = data.loc[data.geography_level.eq('county')]
    latest = int(county.year.max())
    cross = county.loc[county.year.eq(latest)]
    fields = ['county_fips','county_name','population','median_age','median_household_income','median_home_value','median_gross_rent','poverty_pct','unemployment_pct','vacancy_pct','homeownership_pct','bachelors_plus_pct','declarations','precipitation_inches','temperature_f','inflow_individuals_per_1000','outflow_individuals_per_1000','net_individuals_per_1000','education_band']
    migration_fields = ['county_fips','county_name','inflow_individuals','outflow_individuals','net_individuals','net_individuals_per_1000','geography_level']
    migration = {str(year): json.loads(g[migration_fields].round(4).to_json(orient='values')) for year,g in data.groupby('year')}
    captions = pd.read_csv(ROOT/'reports/tables/eda_chart_catalog.csv').caption.tolist()
    matrix = pd.read_csv(ROOT/'reports/tables/validated_latest_year_spearman.csv',index_col=0)
    result = {'latest':latest,'rows':len(data),'counties':len(cross),'years':sorted(int(y) for y in data.year.unique()),'fields':fields,'cross':json.loads(cross[fields].round(5).to_json(orient='values')),'migrationFields':migration_fields,'migration':migration,'captions':captions,'trend':json.loads(pd.read_csv(ROOT/'reports/tables/chart03_balanced_trend.csv').to_json(orient='records')),'correlation':{'fields':matrix.columns.tolist(),'values':matrix.round(4).values.tolist()},'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    (OUT/'analysis.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    cross[fields].to_csv(OUT/'latest-counties.csv',index=False)
    images=ROOT/'website/assets/cleaning'
    images.mkdir(parents=True,exist_ok=True)
    for file in (ROOT/'reports/figures/cleaning').glob('0*.png'):
        shutil.copy2(file,images/file.name)
    print(f'Exported {len(data):,} rows and {len(cross):,} latest-year counties.')

if __name__=='__main__':
    main()
