#!/usr/bin/env python3
"""Technical progression checks. Instructor assessment still checks evidence quality."""
import argparse,json,urllib.request,urllib.parse,subprocess,sys
from pathlib import Path
ES='http://10.10.0.10:9200'; KB='http://10.10.0.10:5601'
def get(url,payload=None):
    req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json','kbn-xsrf':'cr-dos'})
    with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
def verify(stage,task,runid,evidence):
    rules=json.loads(Path(__file__).with_name('stage_checks.json').read_text()); spec=rules[stage]
    requirement=spec['tasks'][task-1]; file=Path(evidence)/requirement['file']
    if not file.is_file() or file.stat().st_size<80: raise ValueError('Create substantive '+str(file)+' with your actual observations first.')
    if task==1 and stage in ('CR-DOS-01','CR-DOS-06'):
        subprocess.run([sys.executable,str(Path(__file__).with_name('health.py'))],check=True)
    else:
        count=get(ES+'/cr-dos-waf-*/_count',{'query':{'bool':{'filter':[{'term':{'run_id':runid}},{'term':{'phase':spec['phase']}}]}}}).get('count',0)
        if count<5: raise ValueError('Fewer than five matching '+spec['phase']+' HTTP events. Generate traffic and wait for Filebeat.')
    if task==3 and spec['searches']:
        q=urllib.parse.urlencode({'type':'search','per_page':100,'search_fields':'title','search':stage+'-'+runid+'-*'})
        found=get(KB+'/api/saved_objects/_find?'+q).get('saved_objects',[])
        titles={x['attributes'].get('title','') for x in found}
        missing=[stage+'-'+runid+'-'+name for name in spec['searches'] if stage+'-'+runid+'-'+name not in titles]
        if missing: raise ValueError('Missing Discover saved searches: '+', '.join(missing))
    if stage=='CR-DOS-03' and task==3:
        count=get(ES+'/cr-dos-waf-*/_count',{'query':{'bool':{'filter':[{'term':{'run_id':runid}},{'term':{'status':429}}]}}}).get('count',0)
        if count<1: raise ValueError('No matching 429 events yet. Repeat the protected traffic comparison.')
    print(requirement['passkey'])
    print('Technical progression check passed. LMS evidence quality remains subject to instructor assessment.')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=['CR-DOS-'+str(i).zfill(2) for i in range(1,7)]); p.add_argument('task',type=int,choices=[1,2,3]); p.add_argument('--run-id',required=True); p.add_argument('--evidence',required=True); a=p.parse_args()
    try: verify(a.stage,a.task,a.run_id,a.evidence)
    except Exception as e: print('Check failed: '+str(e),file=sys.stderr); sys.exit(1)
