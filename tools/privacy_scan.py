"""Check the explicit public inventory; report locations/categories, never values."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATED = {'__pycache__', 'dist', '.git'}
PATTERNS = {
    'personal Windows path': re.compile(r'(?i)[a-z]:[\\/]+Users[\\/]+(?!Public\b|Default\b)[^\s"\'<>]+'),
    'private project path': re.compile(r'(?i)[a-z]:[\\/]+Tradebot\b'),
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'GitHub token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'API token': re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'),
    'AWS key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'JWT': re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b'),
    'credential URL': re.compile(r'https?://[^\s/]+:[^\s/]+@'),
    'literal credential assignment': re.compile(r'''(?i)\b(?:password|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret)\s*["']?\s*[:=]\s*["'][A-Za-z0-9/+_=.-]{12,}["']'''),
    'machine identifier': re.compile(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b'),
    'private email': re.compile(r'\b[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo)\.com\b'),
}
FORBIDDEN = {'workspace_registry.json', 'runtime-info.json', '.env'}

def inventory(root=ROOT):
    names=json.loads((root/'PUBLIC_FILES.json').read_text(encoding='utf-8'))
    if not isinstance(names,list) or len(names)!=len(set(names)):
        raise ValueError('Invalid or duplicate public inventory')
    for name in names:
        p=Path(name)
        if p.is_absolute() or p.drive or '..' in p.parts or '\\' in name:
            raise ValueError('Unsafe inventory path')
    return sorted(names)

def scan(root=ROOT):
    names=inventory(root); allowed=set(names); findings=[]
    for p in root.rglob('*'):
        rel=p.relative_to(root); parts=set(rel.parts)
        if parts & GENERATED: continue
        if p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()):
            findings.append((rel.as_posix(),0,'link refused'));continue
        if p.is_file() and rel.as_posix() not in allowed:
            findings.append((rel.as_posix(),0,'unlisted file'))
    for name in names:
        p=root/name
        if not p.is_file(): findings.append((name,0,'missing file'));continue
        if p.is_symlink() or any(x.is_symlink() or (hasattr(x,'is_junction') and x.is_junction()) for x in [p,*p.parents] if x!=root.parent):
            findings.append((name,0,'linked public file'));continue
        if p.name in FORBIDDEN or p.name.startswith('.env.') or p.suffix.lower() in {'.png','.jpg','.log','.db','.sqlite','.zip','.pem','.key','.pfx','.pyc'}:
            findings.append((name,0,'private/generated file type'));continue
        try: content=p.read_text(encoding='utf-8-sig')
        except (UnicodeError,OSError): findings.append((name,0,'unreadable/non-text file'));continue
        for number,line in enumerate(content.splitlines(),1):
            for category,pattern in PATTERNS.items():
                if pattern.search(line): findings.append((name,number,category))
    if (root/'.git').exists():
        cp=subprocess.run(['git','ls-files','-z'],cwd=root,capture_output=True,check=True)
        for name in cp.stdout.decode().split('\0'):
            if name and name not in allowed: findings.append((name,0,'tracked outside inventory'))
    return names,findings

def main():
    try: names,findings=scan()
    except Exception:
        print('FAIL: inventory or scan could not be completed.');return 2
    for name,line,category in findings: print(f'{name}:{line}: {category}')
    print(f'{"FAIL" if findings else "PASS"}: {len(names)} public files; {len(findings)} findings. Manual review is also required.')
    return 1 if findings else 0

if __name__=='__main__': sys.exit(main())
