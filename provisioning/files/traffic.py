#!/usr/bin/env python3
"""Fixed-target, fixed-budget HTTP traffic for the isolated CADMUS lab."""
import argparse, concurrent.futures, json, time, urllib.request, urllib.error, re, uuid
from collections import Counter
TARGET='http://10.10.0.30'
PROFILES={'baseline':(2,1),'legitimate':(2,1),'attack':(60,8)}
def request(profile, runid, number):
    path='/api/search?q=lab' if profile=='attack' else ['/', '/status', '/about', '/missing'][number%4] if profile=='baseline' else '/'
    req=urllib.request.Request(TARGET+path,headers={'X-CR-DOS-Phase':profile,'X-CR-DOS-Run':runid,'User-Agent':'cr-dos/'+profile})
    start=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=3) as r: r.read(); status=r.status
    except urllib.error.HTTPError as e: e.read(); status=e.code
    except (urllib.error.URLError,TimeoutError,OSError): status=0
    return status,time.monotonic()-start
def run(profile,seconds,runid):
    rate,workers=PROFILES[profile]; started=time.monotonic(); futures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        outstanding=set()
        for n in range(rate*seconds):
            wait=started+n/rate-time.monotonic()
            if wait>0: time.sleep(wait)
            if time.monotonic()-started>=seconds: break
            outstanding={f for f in outstanding if not f.done()}
            if len(outstanding)>=workers: continue
            f=pool.submit(request,profile,runid,n); futures.append(f); outstanding.add(f)
        results=[f.result() for f in futures]
    latency=sorted(t for _,t in results); count=Counter(str(s) for s,_ in results)
    report={'profile':profile,'run_id':runid,'target':TARGET,'duration_budget_seconds':seconds,'elapsed_seconds':round(time.monotonic()-started,3),'requests':len(results),'status_counts':dict(count),'mean_seconds':round(sum(latency)/len(latency),4) if latency else None,'p95_seconds':round(latency[max(0,int(.95*len(latency))-1)],4) if latency else None,'note':'status 0 denotes a client transport error'}
    print(json.dumps(report,indent=2),flush=True)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('profile',choices=PROFILES); p.add_argument('--seconds',type=int,default=60); p.add_argument('--run-id',default=uuid.uuid4().hex[:10]); a=p.parse_args()
    if not 1<=a.seconds<=180: p.error('seconds must be 1..180')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',a.run_id): p.error('run-id must use 1..40 letters, digits, underscores or hyphens')
    run(a.profile,a.seconds,a.run_id)
