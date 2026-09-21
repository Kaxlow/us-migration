"""Compatibility exports; implementations live in notebooks/01_data_cleaning.ipynb."""
from .notebook_api import definitions

TRAIN_END = definitions()['TRAIN_END']
VALIDATION_END = definitions()['VALIDATION_END']
SMALL_MISSING_FRACTION = definitions()['SMALL_MISSING_FRACTION']
STATE_UNITS = definitions()['STATE_UNITS']
recalculate = definitions()['recalculate']
finish_fema_dates = definitions()['finish_fema_dates']
area_key = definitions()['area_key']
map_fema_areas = definitions()['map_fema_areas']
annual_climate = definitions()['annual_climate']
clean_state_climate = definitions()['clean_state_climate']
repair_identifiers = definitions()['repair_identifiers']
SocioeconomicImputer = definitions()['SocioeconomicImputer']

deduplicate_fema_events = definitions()['deduplicate_fema_events']
