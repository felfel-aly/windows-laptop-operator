"""Task-owned child processes; bounded in-memory output; no PID adoption."""
from collections import deque
import subprocess
import threading
import time
import uuid
from operator_core import redact, root_path

class Processes:
    def __init__(self, root, commands=None):
        self.root=root_path(root); self.commands=commands or {}; self.children={}
        if not isinstance(self.commands,dict) or len(self.commands)>16: raise ValueError('at most 16 approved commands')
        for label,argv in self.commands.items():
            if not isinstance(label,str) or not isinstance(argv,list) or not argv or len(argv)>64 or not all(isinstance(x,str) and len(x)<4096 for x in argv):
                raise ValueError('manifest requires labels mapped to exact argv arrays')
            if any(redact(x)!=x for x in argv): raise ValueError('secret-bearing command refused')

    def start(self,label):
        if label not in self.commands: raise ValueError('command not in task-approved manifest')
        for token,item in self.children.items():
            if item['label']==label and item['p'].poll() is None:return {'token':token,'pid':item['p'].pid,'reused':True}
        if sum(x['p'].poll() is None for x in self.children.values())>=8: raise ValueError('8 active children limit')
        if len(self.children)>=100: raise ValueError('task history full; start a new session')
        p=subprocess.Popen(self.commands[label],cwd=self.root,stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        token=uuid.uuid4().hex; item={'p':p,'label':label,'tail':deque(maxlen=16),'bytes':0,'started':time.monotonic()}
        self.children[token]=item
        def drain():
            try:
                while True:
                    chunk=p.stdout.read1(1024)
                    if not chunk: break
                    item['bytes']+=len(chunk); item['tail'].append(chunk)
            finally:p.stdout.close()
        thread=threading.Thread(target=drain,daemon=True);item['thread']=thread;thread.start()
        return {'token':token,'pid':p.pid,'reused':False}

    def status(self,token):
        if token not in self.children: raise ValueError('unknown task-owned process token')
        x=self.children[token];p=x['p'];code=p.poll()
        if code is not None:x['thread'].join(timeout=0.5)
        tail=redact(b''.join(list(x['tail'])).decode('utf-8','replace'))[-8000:]
        return {'token':token,'pid':p.pid,'label':x['label'],'alive':code is None,
                'exit_code':code,'elapsed_ms':round((time.monotonic()-x['started'])*1000),
                'output_tail':tail,'output_bytes':x['bytes'],'truncated':x['bytes']>8000}

    def stop(self,token):
        if token not in self.children: raise ValueError('refusing unowned process')
        p=self.children[token]['p']
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
        return self.status(token)

    def pipeline(self,labels,timeout=60):
        if not isinstance(labels,list) or not 1<=len(labels)<=12:raise ValueError('1..12 labels required')
        if any(x not in self.commands for x in labels):raise ValueError('unapproved check label')
        results=[]
        for label in labels:
            started=self.start(label);p=self.children[started['token']]['p'];timed_out=False
            try:p.wait(timeout=min(max(float(timeout),0.1),300))
            except subprocess.TimeoutExpired:self.stop(started['token']);timed_out=True
            result=self.status(started['token']);result['timeout']=timed_out;results.append(result)
            if result['exit_code'] or timed_out:break
        return {'results':results,'passed':len(results)==len(labels) and all(x['exit_code']==0 and not x['timeout'] for x in results)}

    def health(self,token,url):
        import urllib.request
        import urllib.parse
        self.status(token);u=urllib.parse.urlsplit(url)
        if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.username or u.password or u.query or u.fragment:
            raise ValueError('health accepts credential-free loopback HTTP only')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        with opener.open(url,timeout=2) as r:
            return {'token':token,'http_status':r.status,'alive':self.status(token)['alive'],
                    'note':'HTTP response does not prove port ownership; verify PID via connector if needed'}

    def close(self):
        for token in self.children:self.stop(token)
