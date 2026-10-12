"""Shared definitions for the three descriptive IRS migration outcomes."""
import numpy as np

OUTCOME_DEFINITIONS = [
    dict(id=key, label=label, count=f'{key}_individuals',
         rate=f'{key}_individuals_per_1000', units='IRS individuals per 1,000 ACS residents')
    for key, label in [('net', 'Net migration'), ('inflow', 'Inflow'), ('outflow', 'Outflow')]]
RATE_FIELDS = [o['rate'] for o in OUTCOME_DEFINITIONS]
COUNT_FIELDS = [o['count'] for o in OUTCOME_DEFINITIONS]


def color_limits(frame):
    """Fixed descriptive saturation limits; exact observations remain in exports."""
    return {o['id']: max(float(np.quantile(np.abs(frame[o['rate']]) if o['id'] == 'net'
                                          else frame[o['rate']], .95)), 1e-9)
            for o in OUTCOME_DEFINITIONS}
