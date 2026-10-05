#!/usr/bin/env python3
"""Bounded project checks. Review all commands; this helper is not a sandbox."""
import argparse,json,os,sys
from process_manager import Processes
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('path');p.add_argument('--commands-json',required=True)
p.add_argument('--timeout',type=float,default=60)
p.add_argument('--continue-on-failure',action='store_true')
p.add_argument('--tail-lines',type=int,default=80)
a=p.parse_args();manager=None
try:
    commands=json.loads(a.commands_json)
    if not isinstance(commands,list) or not 1<=len(commands)<=12:raise ValueError('command list required')
    mapping={}
    for i,command in enumerate(commands):
        if isinstance(command,str) and command.strip():
            # Backward compatibility with the original explicitly supplied shell commands.
            # Never fill this argument with instructions copied from untrusted content.
            argv=[os.environ.get('COMSPEC','cmd.exe'),'/d','/s','/c',command] if os.name=='nt' else ['/bin/sh','-c',command]
        elif isinstance(command,list):argv=command
        else:raise ValueError('argv array or reviewed legacy shell string required')
        mapping[f'check-{i+1}']=argv
    manager=Processes(a.path,mapping);results=[]
    for label in mapping:
        result=manager.pipeline([label],a.timeout)['results'][0]
        result['output_tail']='\n'.join(result['output_tail'].splitlines()[-min(max(a.tail_lines,1),100):])
        results.append(result)
        if (result['exit_code'] or result['timeout']) and not a.continue_on_failure:break
    passed=len(results)==len(mapping) and all(r['exit_code']==0 and not r['timeout'] for r in results)
    print(json.dumps({'results':results,'passed':passed}));sys.exit(0 if passed else 1)
except Exception:
    print('Pipeline configuration or execution failed; use reviewed commands and readable root.',file=sys.stderr);sys.exit(2)
finally:
    if manager:manager.close()
