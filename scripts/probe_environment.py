#!/usr/bin/env python3
import argparse, json, os, platform, shutil, sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('path', nargs='?', default='.')
a=p.parse_args()
path=str(Path(a.path).expanduser().resolve())
commands=['python','py','node','npm','pnpm','yarn','git','java','mvn','gradle','dotnet','vercel','supabase']
print(json.dumps({
    'path':path,
    'platform':platform.platform(),
    'python':sys.version.split()[0],
    'commands':{c:shutil.which(c) for c in commands if shutil.which(c)},
    'cwd':os.getcwd(),
}, separators=(',',':')))
