"""Execute the authoritative cleaning notebook and retain its readable outputs."""
import argparse
from pathlib import Path
from run_notebooks import execute_notebook


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=int,default=2009)
    parser.add_argument('--end',type=int,default=2026)
    args=parser.parse_args()
    if not 2009<=args.start<=2018<=args.end:
        parser.error('This documented imputation workflow requires a range including training year 2018; start must be >=2009.')
    root=Path(__file__).resolve().parents[1]
    execute_notebook(root/'notebooks/01_data_cleaning.ipynb',{'START_YEAR':args.start,'END_YEAR':args.end})

if __name__ == '__main__':
    main()
