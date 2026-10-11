#!/usr/bin/env python3
import json, urllib.request, sys
checks=[('Web application','http://10.10.0.30/status'),('Elasticsearch','http://10.10.0.10:9200/'),('Kibana','http://10.10.0.10:5601/api/status')]
failed=False
for label,url in checks:
    try:
        with urllib.request.urlopen(url,timeout=10) as r: body=r.read(); assert r.status==200
        if label=='Kibana': assert json.loads(body)['status']['overall']['level']=='available'
        print(label+': available')
    except Exception as e: print(label+': unavailable ('+str(e)+')'); failed=True
sys.exit(1 if failed else 0)
