"""Bounded local operations. Standard library; no service, socket or elevation.

Connector authorization is the boundary, not this module. No helper is a sandbox.
"""
import codecs
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

MAX_FILE = 1024 * 1024
MAX_TEXT = 64000
SKIP = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'runtime', 'dist', 'build', '.ssh', '.aws'}
MARKERS = ('package.json', 'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'pyproject.toml',
           'requirements.txt', 'Pipfile', 'poetry.lock', 'uv.lock', 'pom.xml', 'build.gradle',
           'build.gradle.kts', 'Cargo.toml', 'go.mod', 'AGENTS.md')
SECRET = re.compile(r'(?i)(-----BEGIN .*PRIVATE KEY-----|\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)|(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|secret|service[_-]?role[_-]?key|authorization|cookie)\s*["\x27]?\s*[:=]\s*[^\r\n]+)')

def redact(value):
    s = SECRET.sub('[REDACTED]', str(value))
    s = re.sub(r'(https?://)[^/\s@]+@', r'\1[REDACTED]@', s)
    s = re.sub(r'(https?://[^\s?#]+)[?#][^\s]*', r'\1?[REDACTED]', s)
    return s

def digest(data):
    return hashlib.sha256(data).hexdigest()

def restricted(path):
    parts = [p.lower() for p in Path(path).parts]
    n = parts[-1] if parts else ''
    return (any(p in SKIP for p in parts) or n.startswith('.env') or
            any(k in n for k in ('credential', 'secret', 'cookie', 'admin-login', 'id_rsa', 'id_ed25519')) or
            n.endswith(('.pem', '.key', '.pfx', '.p12', '.db', '.sqlite', '.sqlite3')))

def root_path(root):
    p = Path(root).expanduser().resolve(strict=True)
    if not p.is_dir(): raise ValueError('root must be a directory')
    return p

def safe_path(root, relative):
    rel = Path(relative)
    if not str(relative) or rel.is_absolute() or rel.drive or '..' in rel.parts or ':' in str(relative):
        raise ValueError('relative normal project path required')
    if restricted(rel): raise ValueError('protected path refused')
    base = root_path(root)
    p = base
    for part in rel.parts:
        p = p / part
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise ValueError('linked paths refused')
    p.resolve().relative_to(base)
    if p.exists() and not p.is_file(): raise ValueError('normal file required')
    return p

def bounded_read(path):
    with open(path, 'rb') as f:
        data = f.read(MAX_FILE + 1)
    if len(data) > MAX_FILE: raise ValueError('file exceeds 1 MiB limit')
    return data

def decode(data):
    enc = 'utf-8-sig' if data.startswith(codecs.BOM_UTF8) else 'utf-8'
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)): enc = 'utf-16'
    text = data.decode(enc)  # Do not guess a legacy encoding.
    if '\x00' in text: raise ValueError('binary file refused')
    return text, enc

def read_bundle(root, paths):
    if not isinstance(paths, list) or len(paths) > 12: raise ValueError('at most 12 paths')
    result=[]; remaining=MAX_TEXT
    for rel in paths:
        p=safe_path(root,rel); raw=bounded_read(p); content,enc=decode(raw)
        clean=redact(content); take=min(remaining,12000); remaining-=min(take,len(clean))
        result.append({'path':str(rel),'sha256':digest(raw),'encoding':enc,'text':clean[:take],
                       'redacted':clean!=content,'truncated':len(clean)>take,'bytes':len(raw)})
    return result

def git(root, *args, okay=(0,)):
    env=os.environ.copy(); env['GIT_OPTIONAL_LOCKS']='0'; env['GIT_TERMINAL_PROMPT']='0'
    cp=subprocess.run(['git','--no-optional-locks','-C',str(root),*args],capture_output=True,
                      timeout=20, env=env)
    if len(cp.stdout)>4*MAX_FILE: raise ValueError('Git output exceeds context limit; narrow repository')
    if cp.returncode not in okay: raise ValueError('Git operation failed (no raw stderr emitted)')
    return cp.stdout.decode('utf-8','replace')

def repo_snapshot(root):
    root=git(root_path(root),'rev-parse','--show-toplevel').strip()
    records=git(root,'status','--porcelain=v2','--branch','-z','--untracked-files=all').split('\0')
    branch=None; head=None; changes=[]; i=0
    while i<len(records):
        row=records[i]; i+=1
        if row.startswith('# branch.head '): branch=row[14:]
        elif row.startswith('# branch.oid '): head=row[13:]
        elif row.startswith(('1 ','2 ','u ')):
            kind=row[0]; fields=row.split(' ',{'1':8,'2':9,'u':10}[kind]); xy=fields[1]
            item={'path':fields[-1],'index':xy[0],'worktree':xy[1]}
            if kind=='2': item['original_path']=records[i]; i+=1
            changes.append(item)
        elif row.startswith('? '): changes.append({'path':row[2:],'index':'?','worktree':'?'})
    remote=git(root,'remote','-v')
    return {'repo_root':root,'branch':branch,'head':head,'changes':changes[:200],
            'staged':[x['path'] for x in changes if x['index'] not in ('.','?')][:200],
            'modified':[x['path'] for x in changes if x['worktree'] not in ('.','?')][:200],
            'untracked':[x['path'] for x in changes if x['index']=='?'][:200],
            'change_count':len(changes),'truncated':len(changes)>200,'remotes':redact(remote)[:8000].splitlines()}

def fingerprints(root):
    r=root_path(root); out={}
    for name in MARKERS:
        p=r/name
        if p.is_file() and not p.is_symlink(): out[name]=digest(bounded_read(p))
    return out

def project_detect(root):
    r=root_path(root); fp=fingerprints(r); markers=list(fp)
    kinds=[]
    for kind, files in {'node':['package.json'],'python':['pyproject.toml','requirements.txt','Pipfile'],
                        'java':['pom.xml','build.gradle','build.gradle.kts'],'rust':['Cargo.toml'],'go':['go.mod']}.items():
        if any(x in markers for x in files): kinds.append(kind)
    extra=[x.name for x in r.iterdir() if x.suffix in ('.sln','.csproj')][:20]
    if extra: kinds.append('dotnet')
    # Root-level extension hints only: no recursive project crawl or code execution.
    suffixes = {x.suffix.lower() for x in r.iterdir() if x.is_file() and not restricted(x.name)}
    for kind, endings in [('python', {'.py', '.ipynb'}), ('java', {'.java'}),
                          ('matlab', {'.mlx', '.mlapp'}), ('powershell', {'.ps1', '.psm1', '.psd1'}),
                          ('javascript', {'.js', '.jsx'}), ('typescript', {'.ts', '.tsx'})]:
        if suffixes & endings and kind not in kinds: kinds.append(kind)
    if '.m' in suffixes and 'matlab' not in kinds:
        kinds.append('matlab_or_objective_c')
    names=[]
    if 'package.json' in markers:
        obj=json.loads(bounded_read(r/'package.json').decode('utf-8-sig'))
        names=list((obj.get('scripts') or {}).keys())[:40]
    pm=next((pm for marker,pm in [('pnpm-lock.yaml','pnpm'),('yarn.lock','yarn'),('package-lock.json','npm'),('uv.lock','uv'),('poetry.lock','poetry')] if marker in markers),None)
    venv=next((str(r/x) for x in ('.venv/Scripts/python.exe','venv/Scripts/python.exe','.venv/bin/python') if (r/x).is_file()),None)
    return {'root':str(r),'project_types':kinds,'markers':markers+extra,'package_manager':pm,
            'package_script_names':names,'venv':venv,'fingerprints':fp,
            'top_level':sorted(x.name for x in r.iterdir() if not restricted(x.name))[:60]}

def candidate_files(root):
    r=root_path(root)
    if shutil.which('rg'):
        cp=subprocess.run(['rg','--files','--hidden','-g','!.git','-g','!node_modules','-g','!.venv',str(r)],capture_output=True,timeout=15)
        if cp.returncode not in (0,1): raise ValueError('file discovery failed')
        if len(cp.stdout)>4*MAX_FILE: raise ValueError('file inventory too large; narrow root')
        files=[Path(x).relative_to(r).as_posix() for x in cp.stdout.decode('utf-8','replace').splitlines()]
    else:
        files=[]
        for folder, dirs, names in os.walk(r,followlinks=False):
            dirs[:]=[d for d in dirs if not restricted(d) and not (Path(folder)/d).is_symlink() and not (hasattr(Path(folder)/d,'is_junction') and (Path(folder)/d).is_junction())]
            files.extend((Path(folder)/n).relative_to(r).as_posix() for n in names)
            if len(files)>5000: break
    return sorted(x for x in files if not restricted(x))

def search_context(root, query, paths=None):
    if not isinstance(query,str) or not query.strip() or len(query)>300: raise ValueError('query must contain 1..300 characters')
    terms=list(dict.fromkeys(re.findall(r'[\w./-]+',query.lower())))[:8]
    files=paths if paths is not None else candidate_files(root)
    if not isinstance(files,list): raise ValueError('paths must be a list')
    files=sorted(files,key=lambda f:(-sum(t in f.lower() for t in terms),f))
    matches=[]; scanned=0; bytes_read=0
    for rel in files[:500]:
        try:
            p=safe_path(root,rel); raw=bounded_read(p); content,_=decode(raw)
        except (ValueError,UnicodeError,OSError): continue
        scanned+=1; bytes_read+=len(raw)
        lines=content.splitlines(); hits=[i for i,line in enumerate(lines) if any(t in line.lower() for t in terms)]
        score=len(hits)+4*sum(t in rel.lower() for t in terms)
        if score:
            indices=set()
            for n in hits[:4]: indices.update(range(max(0,n-2),min(len(lines),n+3)))
            if not indices: indices=set(range(min(12,len(lines))))
            matches.append({'path':rel,'score':score,'sha256':digest(raw),'context':
                            [{'line':i+1,'text':redact(lines[i])[:300]} for i in sorted(indices)][:20]})
        if bytes_read>=4*MAX_FILE: break
    matches.sort(key=lambda x:(-x['score'],x['path']))
    result = {'matches':matches[:8],'related_tests':[f for f in files if re.search(r'(^|/)(test[^/]*|[^/]*[._]test[._])',f)][:15],
            'scanned_files':scanned,'bytes_read':bytes_read,'bounded_scan':len(files)>scanned,
            'note':'literal token relevance; no semantic completeness guarantee'}
    if paths is not None: result['files']=read_bundle(root,paths)
    return result

def workspace_snapshot(root):
    """Fresh Git state or an explicitly non-Git workspace; never hide Git errors."""
    r = root_path(root)
    if not shutil.which('git'):
        if any((parent / '.git').exists() for parent in [r, *r.parents]):
            raise ValueError('Git is required for this repository')
        is_git = False
    else:
        env = os.environ.copy()
        env['GIT_OPTIONAL_LOCKS'] = '0'
        env['GIT_TERMINAL_PROMPT'] = '0'
        env['LC_ALL'] = 'C'
        result = subprocess.run(['git', '--no-optional-locks', '-C', str(r),
                                 'rev-parse', '--is-inside-work-tree'],
                                capture_output=True, timeout=20, env=env)
        if result.returncode == 0:
            if result.stdout.strip() != b'true':
                raise ValueError('Bare repository is not a project worktree')
            is_git = True
        elif (b'not a git repository' in result.stderr.lower() and
              not any((parent / '.git').exists() for parent in [r, *r.parents])):
            is_git = False
        else:
            raise ValueError('Git discovery failed; refusing to label this non-Git')
    if is_git:
        result = repo_snapshot(r)
        result['is_git'] = True
        return result
    return {'repo_root': str(r), 'is_git': False, 'branch': None, 'head': None,
            'changes': [], 'staged': [], 'modified': [], 'untracked': [],
            'remotes': [], 'change_count': None, 'truncated': False,
            'note': 'Non-Git workspace: version-control change tracking unavailable'}

def context_pack(root,query=None):
    snap=workspace_snapshot(root); root=snap['repo_root']
    info=project_detect(root)
    out={'git':snap,'project':info,'instruction_locations':[str(p/'AGENTS.md') for p in [Path(root),*Path(root).parents] if (p/'AGENTS.md').is_file()]}
    if query: out['search']=search_context(root,query)
    return out

def apply_patchset(root, changes):
    """Preflight all files; per-file atomic replacement; guarded rollback on error.

    No cross-file/crash atomicity claim. Stop concurrent editors during application.
    """
    if not isinstance(changes,list) or not 1<=len(changes)<=12: raise ValueError('1..12 changes required')
    prepared=[]; seen=set(); total=0
    for item in changes:
        p=safe_path(root,item['path']); key=str(p).casefold()
        if key in seen: raise ValueError('duplicate target refused')
        seen.add(key)
        if not p.parent.is_dir(): raise ValueError('create parent directories explicitly first')
        before=bounded_read(p) if p.exists() else None
        expected=item.get('expected_sha256')
        if before is None:
            if expected!='absent': raise ValueError('new file requires absent precondition')
            enc='utf-8'; old=''
        else:
            if expected!=digest(before): raise ValueError('hash conflict; reread before editing')
            old,enc=decode(before)
            if redact(old)!=old: raise ValueError('sensitive content refused; use approved secret-aware tooling')
        content=item['text']
        if not isinstance(content,str) or redact(content)!=content: raise ValueError('sensitive or invalid replacement refused')
        # Text is the complete new file; preserve existing BOM and uniform newlines.
        if before is not None and '\r\n' in old and '\n' not in old.replace('\r\n',''):
            content=content.replace('\r\n','\n').replace('\n','\r\n')
        after=content.encode(enc)
        if before and before.startswith(codecs.BOM_UTF16_BE): after=codecs.BOM_UTF16_BE+content.encode('utf-16-be')
        total+=len(after)
        if len(after)>MAX_FILE or total>4*MAX_FILE: raise ValueError('patch size limit')
        prepared.append((p,before,after))
    temps=[]; written=[]
    def current(p): return bounded_read(p) if p.exists() else None
    try:
        for p,before,after in prepared:
            fd,name=tempfile.mkstemp(prefix='.operator-',suffix='.tmp',dir=p.parent)
            temps.append(name)
            with os.fdopen(fd,'wb') as f: f.write(after); f.flush(); os.fsync(f.fileno())
            if before is not None: shutil.copymode(p,name)
        for (p,before,after),name in zip(prepared,temps):
            if current(p)!=before: raise ValueError('concurrent edit detected')
            os.replace(name,p); written.append((p,before,after))
            if current(p)!=after: raise ValueError('write verification failed')
    except Exception:
        conflict=False
        for p,before,after in reversed(written):
            if current(p)!=after: conflict=True; continue
            if before is None: p.unlink()
            else:
                fd,name=tempfile.mkstemp(prefix='.operator-recover-',dir=p.parent); temps.append(name)
                with os.fdopen(fd,'wb') as f: f.write(before); f.flush(); os.fsync(f.fileno())
                shutil.copymode(p,name); os.replace(name,p)
        if conflict: raise ValueError('rollback conflict: concurrent changes preserved; inspect targets') from None
        raise
    finally:
        for name in temps:
            try: Path(name).unlink(missing_ok=True)
            except OSError: pass
    return {'changed':[{'path':str(p.relative_to(root_path(root))),'sha256':digest(after),'bytes':len(after)} for p,_,after in prepared],
            'verified':True,'atomicity':'per-file; not crash-atomic across files'}

def registry_path():
    base=os.environ.get('LOCALAPPDATA')
    if not base: raise ValueError('LOCALAPPDATA unavailable; registry disabled')
    return Path(base)/'ChatGPT/WindowsLaptopOperator/workspace_registry.json'

def workspace_update(alias,root):
    if not re.fullmatch(r'[A-Za-z0-9 _-]{1,60}',alias): raise ValueError('invalid alias')
    p=registry_path(); p.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive writer lock: fail immediately instead of silently losing another update.
    lock=p.with_suffix('.lock')
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: raise ValueError('registry busy; inspect stale lock only after confirming owner exited') from None
    try:
        os.close(fd); data=json.loads(bounded_read(p)) if p.exists() else {}
        snap=workspace_snapshot(root); info=project_detect(snap['repo_root'])
        entry={'root':snap['repo_root'],'is_git':snap['is_git'],'branch':snap['branch'],'head':snap['head'],'verified_at':time.time(),'project':info}
        raw=json.dumps(entry,ensure_ascii=True)
        if redact(raw)!=raw: raise ValueError('sensitive metadata refused')
        if alias not in data and len(data)>=100: raise ValueError('registry limited to 100 projects')
        data[alias]=entry
        fd,name=tempfile.mkstemp(dir=p.parent,prefix='.registry-')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(data,f);f.flush();os.fsync(f.fileno())
            os.replace(name,p)
        finally: Path(name).unlink(missing_ok=True)
    finally: lock.unlink(missing_ok=True)
    return {'alias':alias,'saved':True,'state_file':str(p)}

def workspace_lookup(alias,ttl=3600):
    data=json.loads(bounded_read(registry_path()))
    if alias not in data: raise ValueError('unknown workspace alias')
    entry=data[alias]; snap=workspace_snapshot(entry['root']); fp=fingerprints(snap['repo_root'])
    stale=(time.time()-entry['verified_at']>min(max(int(ttl),0),86400) or
           snap['is_git']!=entry.get('is_git',True) or snap['repo_root']!=entry['root'] or snap['head']!=entry['head'] or snap['branch']!=entry['branch'] or fp!=entry['project']['fingerprints'])
    return {'alias':alias,'stale':stale,'git':snap,'project':project_detect(snap['repo_root']) if stale else entry['project'],
            'cache_authority':False}
