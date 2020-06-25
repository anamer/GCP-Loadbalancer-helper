#!/usr/bin/python
from google.cloud import bigquery
from google.oauth2 import service_account
import googleapiclient.discovery
import pprint


credentials = service_account.Credentials.from_service_account_file(
    '/home/namera/vpcsc-demo.json',
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
project="assafproject-3"



request = service.targetHttpsProxies().get(project=project, targetHttpsProxy="a2108357a954811eabbe442010a80017")
response = request.execute()

# TODO: Change code below to process the `response` dict:
#pprint(response)

pprint (response)

##pprint (credentials)
'''
client = Client.from_service_account_json('home/namera/vpcsc-demo.json')


buckets = client.list_buckets(project='assafproject-3')
for bucket in buckets:
   print (bucket.name)
'''
