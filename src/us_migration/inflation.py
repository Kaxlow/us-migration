"""Annual CPI-U factors for fitting monetary donors; exports retain source-year dollars."""
import pandas as pd
from .acquisition import ROOT


def annual_price_index():
    frame=pd.read_csv(ROOT/'docs/cpi-u-annual.csv')
    if frame.year.duplicated().any() or frame.cpi_u.isna().any() or frame.cpi_u.le(0).any():
        raise ValueError('Invalid annual CPI index')
    return frame.set_index('year').cpi_u.to_dict()


def dollar_factors(years, price_index, base_year):
    index=years.map(price_index)
    if base_year not in price_index or index.isna().any() or index.le(0).any():
        raise ValueError('CPI coverage missing for requested dollar years')
    return float(price_index[base_year])/index
