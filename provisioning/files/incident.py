#!/usr/bin/env python3
import argparse,datetime,subprocess,sys
from pathlib import Path
def mark(phase): print(datetime.datetime.now(datetime.timezone.utc).isoformat()+' '+phase,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run-id',required=True); a=p.parse_args()
    for phase,duration in [('baseline',60),('attack',180),('legitimate',120)]:
        mark(phase)
        subprocess.run([sys.executable,str(Path(__file__).with_name('traffic.py')),phase,'--seconds',str(duration),'--run-id',a.run_id],check=True)
    mark('incident finished')
