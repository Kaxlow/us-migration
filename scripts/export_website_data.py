"""Package canonical result bundles; analyses remain independent Jupyter workflows."""
from pathlib import Path
import argparse
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from us_migration.exports import export_topics

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topics', nargs='+', choices=['cleaning','exploration','clustering','pca','classification'])
    args = parser.parse_args()
    print('Exported: ' + ', '.join(export_topics(ROOT,args.topics)))

if __name__ == '__main__':
    main()
