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

##################################################################################
# usage: private-ca-renew-w_yaml.py <project-id> <YAML File>
# This script assumes all Google Load balancer certs in a project are self-manged.
# The script scans all LBs in a project and renew LB cert if the remaining life-time
# of the cert is lower than a ratio (REMAIN_CERT_LIFE_TIME_RATIO)
###################################################################################

import argparse
import time
import subprocess
import yaml
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from google.oauth2 import service_account

import googleapiclient.discovery
from six.moves import input
from pprint import pprint
from private_ca_functions import *

 # REMAIN_CERT_LIFE_TIME_RATIO is the remining precentage cert life span to renew
 # for example if the value is 40, then the cert will be renewed when it has less than 40% from
 # the life span of the cert. Thus, if the life span of the cert is 24 hrs, then it will be renewed whitin 9.6 hrs (40% of 24hrs)
 # before the end of the 24 hrs.
 # One more example, if REMAIN_CERT_LIFE_TIME_RATIO = 50, if a cert is issued for 30 days, then it will be renewed after 15 days.
REMAIN_CERT_LIFE_TIME_RATIO = 10

# SA_AUTH indicates if the script is executed from outside the GCP platform, if set to True then the script auth with the patform via 
# service account keys which are refernced in the "service_account.Credentials.from_service_account_file" API.
# If the script is executed from a VM in GCP or CloudShell then set this variable to False, in that case the script will inherent the
# VM service account.
# In both cases, the SA or the user needs to have the apprioiate IAM permissions to get & set SSL certicate on load-balancers and to issue
# new certiciates from GCP private CA service.
SA_AUTH = False


# [START run]
def main(project , yaml_file):


    if (SA_AUTH):
        # assuming script runs outside GCP, use a pre-configured ServiceAccount. 
        # make sure NOT to include credential file in the code or your repo, follow the Service Account best practices.
        # TODO: move to script input vars
        credentials = service_account.Credentials.from_service_account_file(
            '/home/namera/proj-2-SA.json',
            scopes=["https://www.googleapis.com/auth/cloud-platform"],)
        service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
        project = "assafproject-2"
    else:
        # assuming script runs on GCP and assume the VM (or underlying role)
        service = googleapiclient.discovery.build('compute', 'v1')

    #parse YAML file
    f = open(yaml_file)
    data = yaml.safe_load(f)
    f.close()

    #print (data)

    for item_in_yaml in data['ssl_resources']:
        print (item_in_yaml)
        resource_name = data['ssl_resources'][item_in_yaml]['name']
        type = data['ssl_resources'][item_in_yaml]['type']
        subordinate_ca = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        subordinate_ca_region = data['ssl_resources'][item_in_yaml]['subordinate-ca-region']
        cert_renew_ratio = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        if "region" in data['ssl_resources'][item_in_yaml]:
            region = data['ssl_resources'][item_in_yaml]['region']
        else:
            print ("No region specified, assuming Global")
            region = "global"

        #print (resource_name)
        #print (type)
        print ("region is:")
        print (region)
    
     

    # Process resources types
        if type == 'GLB' or type == "ILB":
            print ("Procssing {} GLB".format(resource_name))
            #read Load Balancer
            response = private_ca_read_target_https(service, project, resource_name, region)
            #read SSL cert
            ssl_certificate_list = response[u'sslCertificates']
            # process each cert in cert list
            for cert_name in ssl_certificate_list:
                print (cert_name)
                cert_name = cert_name.split("/")[-1]
                #print (cert_name)
                cert_expiration_date_in_datetime , cert_creation_date_in_datetime = get_cert_dates (service, project, cert_name, region)
                # Calc cert life-time, i.e.: cert-expiraton-date (minus) cert expiration date , keep result in seconds
                duration = cert_expiration_date_in_datetime - cert_creation_date_in_datetime
                cert_total_life_time_in_sec = round(duration.total_seconds())
                #print ("cert_life_time_in_sec = {} ".format(cert_total_life_time_in_sec))

                #Calc remining life of cert, i.e.: cert-expiraton-date (minus) now, keep result in seconds
                now = datetime.now()
                duration = cert_expiration_date_in_datetime - now
                cert_remaining_time_in_sec = round(duration.total_seconds())

                print ("Resource: {}, Cert: {} , creation: {} ,expire: {} , cert life time in sec: {:,}, remining time in sec: {:,}".format(resource_name, cert_name, cert_creation_date_in_datetime ,cert_expiration_date_in_datetime, cert_total_life_time_in_sec , cert_remaining_time_in_sec)) # + " creation: " + creation
                
                if (cert_remaining_time_in_sec<0) or (cert_remaining_time_in_sec*100/cert_total_life_time_in_sec < REMAIN_CERT_LIFE_TIME_RATIO):
                    # Issue new cert, create LB SSL and install new SSL to LB.
                    print ("Renewing SSL cert for LB " + resource_name)
                    _new_cert_name = "cert-" + datetime.now().strftime("%Y%m%d%H%M%S")
                    private_ca_issue_LB_cert_from_subordinate(service, project, subordinate_ca , subordinate_ca_region=subordinate_ca_region, cert_name = _new_cert_name , lb_region=region)
                    # Update LB's cert
                    private_ca_update_target_https_proxy_ssl (service, project, resource_name , _new_cert_name , region)
                    
                    # Check if new cert is slisted in the LB
                    response = private_ca_read_target_https(service, project, resource_name, region)
                    #read SSL cert
                    ssl_certificate_list = response[u'sslCertificates']
                    print ("Update LB has this SSL cert: " + str(ssl_certificate_list))
                    print ("new cert name = " + _new_cert_name)
                    update_sucess = False
                    for cert_name in ssl_certificate_list:
                        if (_new_cert_name in cert_name):
                            update_sucess = True
                            break;
                    if (update_sucess == True):
                         print("Updated LB's SSL Cert successfully")
                    else:
                        print("mmmm, Something went wrong ... do some error handling here!")

                else:
                    print ("Cert {}, has {}% of its life, skipping cert renewal!".format(resource_name, round((cert_remaining_time_in_sec*100/cert_total_life_time_in_sec),1)))
                    print ("-" * 50)

#        if type == 'ILB':
#            print ("Processing Internal Load Balancer")
#            print ("Procssing {} ILB".format(resource_name))
 #           #read GLB





if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument('yaml_file', help='Path to YAMl file')

    args = parser.parse_args()
    #print (args.subordinate_name)


    main(args.project_id , args.yaml_file)
# [END run]
