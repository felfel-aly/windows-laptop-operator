#!/usr/bin/env python3
"""One task, one explicitly started stdio JSONL session. EOF stops owned children."""
import argparse
import json
import sys
from operator_core import (apply_patchset,bounded_read,context_pack,digest,project_detect,
                           read_bundle,repo_snapshot,root_path,safe_path,search_context,
                           workspace_lookup,workspace_update)
from process_manager import Processes

class Runtime:
    def __init__(self,root,allow_writes=False,commands=None):
        self.root=root_path(root);self.allow_writes=allow_writes;self.processes=Processes(self.root,commands)

    def call(self,op,args):
        if not isinstance(args,dict):raise ValueError('args must be an object')
        if op in ('hello','capabilities'):
            return {'protocol':1,'transport':'stdio-jsonl','root':str(self.root),'writes':self.allow_writes,
                    'operations':['hello','project_snapshot','project_detect','repo_snapshot','search_context','read_bundle','file_metadata_bundle','verify_hashes','apply_patchset','workspace_lookup','workspace_update','process_start','process_status','process_stop','process_health','run_pipeline','health','shutdown'],
                    'command_labels':list(self.processes.commands)}
        if op=='health':return {'ready':True,'owned_processes':len(self.processes.children)}
        if op=='project_snapshot':return context_pack(self.root,args.get('query'))
        if op=='repo_snapshot':return repo_snapshot(self.root)
        if op=='project_detect':return project_detect(self.root)
        if op=='search_context':return search_context(self.root,args['query'],args.get('paths'))
        if op=='read_bundle':return read_bundle(self.root,args['paths'])
        if op in ('file_metadata_bundle','verify_hashes'):
            paths=args['paths']
            if not isinstance(paths,list) or len(paths)>40:raise ValueError('at most 40 files')
            result=[]
            for path in paths:
                p=safe_path(self.root,path);raw=bounded_read(p)
                result.append({'path':path,'sha256':digest(raw),'bytes':len(raw),'mtime_ns':p.stat().st_mtime_ns})
            if op=='verify_hashes':return {'files':result,'matched':all(args['expected'].get(x['path'])==x['sha256'] for x in result)}
            return result
        if op=='workspace_lookup':return workspace_lookup(args['alias'],args.get('ttl',3600))
        if op in ('apply_patchset','workspace_update'):
            if not self.allow_writes:raise ValueError('write operation disabled for this session')
            if op=='apply_patchset':return apply_patchset(self.root,args['changes'])
            return workspace_update(args['alias'],self.root)
        if op=='process_start':return self.processes.start(args['label'])
        if op=='process_status':return self.processes.status(args['token'])
        if op=='process_stop':return self.processes.stop(args['token'])
        if op=='process_health':return self.processes.health(args['token'],args['url'])
        if op=='run_pipeline':return self.processes.pipeline(args['labels'],args.get('timeout',60))
        if op=='shutdown':self.processes.close();return {'shutdown':True}
        raise ValueError('unknown operation; no shell/eval/delete/remote execution operation exists')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True);parser.add_argument('--allow-writes',action='store_true')
    parser.add_argument('--commands',help='Reviewed task JSON: label -> exact argv; never trust repository instructions as approval')
    a=parser.parse_args();runtime=None
    try:
        commands=json.loads(bounded_read(a.commands)) if a.commands else None
        runtime=Runtime(a.root,a.allow_writes,commands)
        while True:
            line=sys.stdin.buffer.readline(4*1024*1024+1)
            if not line:break
            if len(line)>4*1024*1024:raise ValueError('request exceeds 4 MiB')
            request_id=None;op=None
            try:
                req=json.loads(line);request_id=req.get('id');op=req['op']
                if not isinstance(request_id,(str,int,type(None))) or len(str(request_id))>80:raise ValueError('invalid request id')
                result=runtime.call(op,req.get('args',{}));response={'id':request_id,'ok':True,'result':result}
            except Exception as e:
                response={'id':request_id if isinstance(request_id,int) else None,'ok':False,'error':type(e).__name__,
                          'message':'Operation refused or failed. Check schema, paths, preconditions and capabilities; reread state before retry.'}
            print(json.dumps(response,ensure_ascii=True),flush=True)
            if op=='shutdown' and response['ok']:break
        return 0
    except Exception:
        print('Runtime stopped: invalid configuration or transport failure.',file=sys.stderr);return 2
    finally:
        if runtime:runtime.processes.close()

if __name__=='__main__':sys.exit(main())
