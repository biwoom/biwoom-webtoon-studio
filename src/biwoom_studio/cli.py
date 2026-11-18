import argparse
import json
from .core import create_fixture, approve_fixture_only, preview, layout

def main():
    parser = argparse.ArgumentParser(description='Synthetic local fixture only; no live mode or real approval')
    parser.add_argument('command', choices=['demo'])
    parser.parse_args()
    run = create_fixture()
    preview(run)  # Deliberately demonstrates a clearly labelled unapproved preview.
    approve_fixture_only(run)
    errors = layout(run)
    print(json.dumps({'mock_only':True, 'run':str(run), 'errors':errors}, indent=2))
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
