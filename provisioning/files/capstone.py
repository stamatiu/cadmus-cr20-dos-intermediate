#!/usr/bin/env python3
"""15-minute scheduled mixed traffic. Every generator is bounded to its slot."""
import argparse,datetime,subprocess,sys,time,re
from pathlib import Path
def mark(phase): print(datetime.datetime.now(datetime.timezone.utc).isoformat()+' '+phase,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run-id',required=True); a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',a.run_id): p.error('Invalid run-id')
    traffic=str(Path(__file__).with_name('traffic.py')); origin=time.monotonic()
    plan=[('baseline',180),('attack',180),('legitimate',120),('slow-headers',180),('attack',120),('legitimate',120)]
    deadline=origin
    for phase,duration in plan:
        mark(phase); deadline+=duration
        if phase=='slow-headers':
            cmd=['slowhttptest','-H','-c','20','-r','2','-i','5','-l','170','-u','http://10.10.0.30/','-p','3']
        else: cmd=[sys.executable,traffic,phase,'--seconds',str(duration),'--run-id',a.run_id]
        try: subprocess.run(cmd,timeout=max(1,deadline-time.monotonic()),check=False)
        except subprocess.TimeoutExpired: pass
        remaining=deadline-time.monotonic()
        if remaining>0: time.sleep(remaining)
    mark('capstone finished')
