#!/usr/bin/env python3
import argparse,json,urllib.request
ES='http://10.10.0.10:9200'
def query(index,payload):
    req=urllib.request.Request(ES+'/'+index+'/_search',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=20) as r: return json.load(r)
def metrics(runid,minutes,start=None,end=None):
    timefilter={'gte':start or 'now-'+str(minutes)+'m'}
    if end: timefilter['lte']=end
    aggs={'status_codes':{'terms':{'field':'status','size':12}},'clients':{'terms':{'field':'remote_addr','size':10}},'paths':{'terms':{'field':'uri','size':10}},'latency':{'percentiles':{'field':'request_time','percents':[50,95]}},'per_phase':{'terms':{'field':'phase','size':10},'aggs':{'responses':{'terms':{'field':'status','size':12}},'latency':{'percentiles':{'field':'request_time','percents':[95]}}}},'per_10_seconds':{'date_histogram':{'field':'@timestamp','fixed_interval':'10s','min_doc_count':0}},'limiting':{'terms':{'field':'limit_req_status','size':10}}}
    result=query('cr-dos-waf-*',{'size':0,'track_total_hits':True,'query':{'bool':{'filter':[{'term':{'run_id':runid}},{'range':{'@timestamp':timefilter}}]}},'aggs':aggs})
    return {'run_id':runid,'time_filter':timefilter,'latency_unit':'seconds','histogram_bucket_unit':'requests per 10 seconds','matched_requests':result.get('hits',{}).get('total',{}).get('value',0),'aggregations':result.get('aggregations',{})}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--run-id',required=True); p.add_argument('--minutes',type=int,default=15); p.add_argument('--from-utc'); p.add_argument('--to-utc'); a=p.parse_args()
    print(json.dumps(metrics(a.run_id,a.minutes,a.from_utc,a.to_utc),indent=2))
