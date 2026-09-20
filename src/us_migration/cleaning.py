"""Compatibility exports; implementations live in notebooks/01_data_cleaning.ipynb."""
from .notebook_api import definitions

US_STATES = definitions()['US_STATES']
NOAA_STATE_FIPS = definitions()['NOAA_STATE_FIPS']
code = definitions()['code']
numeric = definitions()['numeric']
acs_numeric = definitions()['acs_numeric']
api_frame = definitions()['api_frame']
clean_acs = definitions()['clean_acs']
normalize_irs = definitions()['normalize_irs']
read_irs = definitions()['read_irs']
canonical_irs_pairs = definitions()['canonical_irs_pairs']
normalize_state_irs = definitions()['normalize_state_irs']
clean_acs_flows = definitions()['clean_acs_flows']
clean_fema = definitions()['clean_fema']
clean_noaa = definitions()['clean_noaa']
build_panel = definitions()['build_panel']


def main(argv=None):
    """Execute the authoritative notebook, preserving the former CLI entry point."""
    import subprocess
    import sys
    from .acquisition import ROOT
    result=subprocess.run([sys.executable,str(ROOT/'scripts/clean_data.py'),*(argv or [])],cwd=ROOT)
    result.check_returncode()
