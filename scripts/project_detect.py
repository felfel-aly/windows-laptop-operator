#!/usr/bin/env python3
import argparse,json,sys
from operator_core import project_detect

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');a=p.parse_args()
    try:print(json.dumps(project_detect(a.path),ensure_ascii=True))
    except Exception:print('Project detection failed; verify root and configuration.',file=sys.stderr);sys.exit(2)
