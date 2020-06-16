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




# [START run]
def main(project , yaml_file):
    service = googleapiclient.discovery.build('compute', 'v1')

    #parse YAML file
    f = open(yaml_file)
    data = yaml.safe_load(f)
    f.close()

    print (data)

    for item_in_yaml in data['ssl_resources']:
        print (item_in_yaml)
        name = data['ssl_resources'][item_in_yaml]['name']
        type = data['ssl_resources'][item_in_yaml]['type']
        subordinate_ca = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        cert_renew_ratio = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        print (name)
        print (type)

    # Process resources types
        if type == 'GLB':
            print ("Procssing {} GLB".format(name))
            #read GLB
            response = private_ca_read_global_target_https(service, project, "demo-lb-target-proxy" )
            #read SSL cert
            ssl_certificate_list = response[u'sslCertificates']
            # process each cert in cert list
            for cert_name in ssl_certificate_list:
                print (cert_name)
                cert_name = cert_name.split("/")[-1]
                #print (cert_name)
                cert_expiration_date_in_datetime , cert_creation_date_in_datetime = get_cert_dates (service, project, cert_name)
                print ("Cert: {} , creation: {} ,expire: {}".format(cert_name, cert_creation_date_in_datetime ,cert_expiration_date_in_datetime)) # + " creation: " + creation
                if (cert_remaining_time_in_sec<0) or (cert_remaining_time_in_sec*100/cert_total_life_time_in_sec < REMAIN_CERT_LIFE_TIME_RATIO):
                    # Issue new cert, create LB SSL and install new SSL to LB.
                    print ("Renewing SSL cert for LB " + name)
                    _new_cert_name = "cert-" + datetime.now().strftime("%Y%m%d%H%M%S")
                    private_ca_issue_cert_from_subordinate(service, project, subordinate_name , cert_name = _new_cert_name )
                    # Update LB's cert
                    private_ca_update_target_https_proxy_ssl (service, project, target_https_proxy[u'name'] , _new_cert_name)

    exit (1)
    # read all LB in the project
    request = service.targetHttpsProxies().list(project=project)
    while request is not None:
        response = request.execute()

        for target_https_proxy in response['items']:
            # TODO: Change code below to process each `target_https_proxy` resource:
            # get cert list from https-proxy
            #pprint(target_https_proxy)
            ssl_certificate_list = target_https_proxy[u'sslCertificates']
            # process each cert in cert list
            for cert_name in ssl_certificate_list:
                #print cert_name
                cert_name = cert_name.split("/")[-1]
                #print (cert_name)
                cert_expiration_date_in_datetime , cert_creation_date_in_datetime = get_cert_dates (service, project, cert_name)
                print ("Cert: {} , creation: {} ,expire: {}".format(cert_name, cert_creation_date_in_datetime ,cert_expiration_date_in_datetime)) # + " creation: " + creation

        request = service.targetHttpsProxies().list_next(previous_request=request, previous_response=response)




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
