#!/usr/bin/env python3
"""Export a bounded real target-side HTTP PCAP to the sensor; no port mirror is assumed."""
import argparse, json, subprocess, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from pathlib import Path
LOCK=threading.Lock()
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u=urlsplit(self.path)
        if self.client_address[0] not in ('10.10.0.20','127.0.0.1') or u.path!='/capture': self.send_error(403); return
        try: seconds=int(parse_qs(u.query).get('seconds',['30'])[0]); assert 5<=seconds<=60
        except (ValueError,AssertionError): self.send_error(400,'seconds must be 5..60'); return
        if not LOCK.acquire(blocking=False): self.send_error(409,'capture already running'); return
        try:
            route=json.loads(subprocess.check_output(['ip','-j','route','get','10.10.0.40']))[0]
            interface=route['dev']
            with tempfile.TemporaryDirectory(prefix='crdos-capture-') as temp:
                capture=Path(temp)/'capture.pcap'
                proc=subprocess.Popen(['tcpdump','-U','-Z','root','-i',interface,'-s','256','-c','20000','-w',str(capture),'tcp port 80'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                try: proc.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    proc.send_signal(2)
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
                if not capture.exists(): raise RuntimeError('tcpdump did not produce a PCAP')
                body=capture.read_bytes()
                if len(body)>8*1024*1024: raise RuntimeError('capture exceeds lab budget')
                self.send_response(200); self.send_header('Content-Type','application/vnd.tcpdump.pcap'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        except (RuntimeError,subprocess.SubprocessError,KeyError) as e: self.send_error(500,str(e))
        finally: LOCK.release()
    def log_message(self,*args): pass
if __name__=='__main__':
    ThreadingHTTPServer(('10.10.0.30',8081),Handler).serve_forever()
