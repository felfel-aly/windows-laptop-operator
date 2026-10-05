#!/usr/bin/env python3
import argparse,json,sys
from operator_core import repo_snapshot

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args()
    try:print(json.dumps(repo_snapshot(a.path),ensure_ascii=True))
    except Exception:print('Git snapshot unavailable; verify repository and Git installation.',file=sys.stderr);sys.exit(2)
