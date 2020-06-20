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

    #print (data)

    for item_in_yaml in data['ssl_resources']:
        #print (item_in_yaml)
        resource_name = data['ssl_resources'][item_in_yaml]['name']
        type = data['ssl_resources'][item_in_yaml]['type']
        subordinate_ca = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        cert_renew_ratio = data['ssl_resources'][item_in_yaml]['subordinate-ca']
        #print (resource_name)
        #print (type)

    # Process resources types
        if type == 'GLB':
            print ("Procssing {} GLB".format(resource_name))
            #read GLB
            response = private_ca_read_global_target_https(service, project, resource_name)
            #read SSL cert
            ssl_certificate_list = response[u'sslCertificates']
            # process each cert in cert list
            for cert_name in ssl_certificate_list:
                #print (cert_name)
                cert_name = cert_name.split("/")[-1]
                #print (cert_name)
                cert_expiration_date_in_datetime , cert_creation_date_in_datetime = get_cert_dates (service, project, cert_name)
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
                    private_ca_issue_LB_cert_from_subordinate(service, project, subordinate_ca , cert_name = _new_cert_name )
                    # Update LB's cert
                    private_ca_update_target_https_proxy_ssl (service, project, resource_name , _new_cert_name)
                    # Check if new cert is slisted in the LB
                    response = private_ca_read_global_target_https(service, project, resource_name)
                    #read SSL cert
                    ssl_certificate_list = response[u'sslCertificates']
                    print ("Update LB has this SSL cert: " + str(ssl_certificate_list))
                    if (_new_cert_name in ssl_certificate_list):
                        print("Updated LB's SSL Cert successfully")
                    else:
                        print("ERROR: Could not find new SSL cert in LB!")
                else:
                    print ("Cert {}, has {}% of its life, skipping cert renewal!".format(resource_name, round((cert_remaining_time_in_sec*100/cert_total_life_time_in_sec),1)))
                    print ("-" * 50)




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
