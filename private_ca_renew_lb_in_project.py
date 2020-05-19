
###################################################################################
# usage: private-ca-renew-gclb.py <project-id> <private ca subordinate name>
# This script assumes all Google Load balancer certs in a project are self-manged.
# The script scans all LBs in a project and renew LB cert if the remaining life-time
# of the cert is lower than a ratio (REMAIN_CERT_LIFE_TIME_RATIO)
###################################################################################

import argparse
import time
import subprocess
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
#import datetime

import googleapiclient.discovery
from six.moves import input
from google.cloud import storage
from pprint import pprint
from private_ca_functions import *

 # REMAIN_CERT_LIFE_TIME_RATIO is the remining precentage cert life span to renew
 # for example if the value is 40, then the cert will be renewed when it has less than 40% from
 # the life span of the cert. Thus, if the life span of the cert is 24 hrs, then it will be renewed whitin 9.6 hrs (40% of 24hrs)
 # before the end of the 24 hrs.
 # One more example, if REMAIN_CERT_LIFE_TIME_RATIO = 50, if a cert is issued for 30 days, then it will be renewed after 15 days.
REMAIN_CERT_LIFE_TIME_RATIO = 10


def get_cert_dates(service, project, cert_name):
    cert_request = service.sslCertificates().get(project=project, sslCertificate=cert_name)
    cert_response = cert_request.execute()
    expire = cert_response[u'expireTime']
    creation = cert_response[u'creationTimestamp']
    date_format = "%Y-%m-%dT%H:%M:%S"

    # Parse cert epiration date to datetime format
    cert_expiration_date = cert_response[u'expireTime']
    split_string = cert_expiration_date.split(".", 1)
    cert_expiration_date = split_string[0]
    #print cert_expiration_date
    cert_expiration_date_in_datetime = datetime.strptime(cert_expiration_date, date_format)
    cert_expi_for_print = cert_expiration_date_in_datetime.strftime("%m/%d/%Y, %H:%M:%S")
    #print ("Cert Expiration Date2: ")
    #print (cert_expiration_date_in_datetime)

    cert_creation_date = cert_response[u'creationTimestamp']
    split_string = cert_creation_date.split(".", 1)
    cert_creation_date = split_string[0]
    cert_creation_date_in_datetime = datetime.strptime(cert_creation_date, date_format)
    cert_creation_for_print = cert_creation_date_in_datetime.strftime("%m/%d/%Y, %H:%M:%S")
    #print ("Cert Creation Date: ")
    #print (cert_creation_date_in_datetime)

    #return cert_response[u'expireTime'], cert_response[u'creationTimestamp']
    return cert_expiration_date_in_datetime , cert_creation_date_in_datetime





# [START run]
def main(project , subordinate_name):
    service = googleapiclient.discovery.build('compute', 'v1')

    #issue_cert_from_private_ca_subordinate(service, project, 'server-tls-2' , cert_name = 'cert-2')
    #private_ca_list_ssl_certs(service, project)

    # read all LB in the project
    request = service.targetHttpsProxies().list(project=project)
    while request is not None:
        response = request.execute()

        for target_https_proxy in response['items']:
            # TODO: Change code below to process each `target_https_proxy` resource:
            # get cert list from https-proxy
            pprint(target_https_proxy)
            ssl_certificate_list = target_https_proxy[u'sslCertificates']
            # process each cert in cert list
            for cert_name in ssl_certificate_list:
                #print cert_name
                cert_name = cert_name.split("/")[-1]
                print (cert_name)
                cert_expiration_date_in_datetime , cert_creation_date_in_datetime = get_cert_dates (service, project, cert_name)
                print ("Cert: {} , creation: {} ,expire: {}".format(cert_name, cert_creation_date_in_datetime ,cert_expiration_date_in_datetime)) # + " creation: " + creation

                # Calc remining life of cert, i.e.: cert-expiraton-date (minus) now, keep result in seconds
                now = datetime.now()
                duration = cert_expiration_date_in_datetime - now
                cert_remaining_time_in_sec = duration.total_seconds()
                print ("cert_remaining_time_in_sec = {} ".format(cert_remaining_time_in_sec))

                # Calc cert life-time, i.e.: cert-expiraton-date (minus) cert expiration date , keep result in seconds
                duration = cert_expiration_date_in_datetime - cert_creation_date_in_datetime
                cert_total_life_time_in_sec = duration.total_seconds()
                print ("cert_life_time_in_sec = {} ".format(cert_total_life_time_in_sec))

                # Renew LB cert if cert has expired (i.e.: cert_remaining_time_in_sec is negative number ) or when cert_life_time_in_sec is below remain_cert_life_time_ratio

                if (cert_remaining_time_in_sec<0) or (cert_remaining_time_in_sec*100/cert_total_life_time_in_sec < REMAIN_CERT_LIFE_TIME_RATIO):
                    # Issue new cert, create LB SSL and install new SSL to LB.
                    print ("Renewing SSL cert for LB " + target_https_proxy[u'name'])

                    _new_cert_name = "cert-" + datetime.now().strftime("%Y%m%d%H%M%S")

                    private_ca_issue_cert_from_subordinate(service, project, subordinate_name , cert_name = _new_cert_name )
                    # Update LB's cert
                    private_ca_update_target_https_proxy_ssl (service, project, target_https_proxy[u'name'] , _new_cert_name)



        request = service.targetHttpsProxies().list_next(previous_request=request, previous_response=response)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('project_id', help='Your Google Cloud project ID.')
    parser.add_argument('subordinate_name', help='Issuer Subordinate CA')

    args = parser.parse_args()
    print (args.subordinate_name)


    main(args.project_id , args.subordinate_name)
# [END run]
