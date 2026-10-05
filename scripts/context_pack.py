#!/usr/bin/env python3
import argparse,json,sys
from operator_core import context_pack

def main():
    p=argparse.ArgumentParser(description='One bounded Git/project/search context pack')
    p.add_argument('--root',required=True);p.add_argument('--query');a=p.parse_args()
    try:print(json.dumps(context_pack(a.root,a.query),ensure_ascii=True));return 0
    except Exception:print('Context unavailable: verify Git root, readable configuration and tools.',file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
