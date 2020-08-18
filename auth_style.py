#!/usr/bin/python
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
