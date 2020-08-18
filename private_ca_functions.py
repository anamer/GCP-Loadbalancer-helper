from pprint import pprint
from datetime import datetime
import os

def private_ca_list_ssl_certs(service, project):
    # List certs
    request = service.sslCertificates().list(project=project)
    while request is not None:
        response = request.execute()
        for ssl_certificate in response['items']:
            # TODO: Change code below to process each `ssl_certificate` resource:
            pprint(ssl_certificate)
        request = service.sslCertificates().list_next(previous_request=request, previous_response=response)

    # TODO: Change code below to process the `response` dict:
    pprint(response)
    return response

#def private_ca_issue_an_apply_cert(service, project, subordinate_name)

def private_ca_insert_new_self_managed_LB_cert(service, project, cert_name, cert_data, private_key_data, _region):
    ssl_certificate_body = {
        "name": cert_name,
        "description": "creating new lb ssl cert",
        "certificate": cert_data,  # cert,
        "privateKey": private_key_data,  # private_key,
        # "managed": {
        #    "domains": [
        #    string
        #    ],
        #    "status": enum,
        #    "domainStatus": {
        #    object
        #    }
        #},
        "selfManaged": {
            "certificate": cert_data, # cert,
            "privateKey": private_key_data, # private_key
        }
    }
    print ("in private_ca_insert_new_self_managed_LB_cert region is: " + _region)
    if (_region == "global"):
        request = service.sslCertificates().insert(project=project, body=ssl_certificate_body)
    else:
        request = service.regionSslCertificates().insert(project=project, body=ssl_certificate_body , region=_region)
    response = request.execute()
    pprint (response)
    print ("done insert new self managed cert : project {}, cert name {}".format(project,cert_name))
    #ToDo return response


def private_ca_read_target_https(service, project, target_https_target_name, _region="global"):
    print ("in read target")
    print (_region)
    if (_region == "global"):
        request = service.targetHttpsProxies().get(project=project, targetHttpsProxy=target_https_target_name)
    else:
        request = service.regionTargetHttpsProxies().get(project=project, region=_region, targetHttpsProxy=target_https_target_name)
    response = request.execute()

    # TODO: Change code below to process the `response` dict:
    pprint(response)
    return response





def private_ca_issue_LB_cert_from_subordinate(service, project, private_ca_subodinate, cert_name, san = "www.joonix.net", reusable_config = "leaf-server-tls", subordinate_ca_region="us-west1", lb_region="global" ):
    # given a project name, private ca subordinate and desired cert_name issue new cert
   

    print ("Issue new cert from issuer {}, cert name {} , subordinate location - 2".format(private_ca_subodinate, cert_name, subordinate_ca_region))
    #TODO - replace with Privae CA API
    # since gcloud is executed as stand alone shell with os.system we need to install the cryptography each time
    # this will be replaced with Python SDK as soon as API becomes avaliable.
    _shell_command = """pip3 install --user \"cryptography>=2.2.0\" ; export CLOUDSDK_PYTHON_SITEPACKAGES=1; gcloud alpha privateca certificates create  \
       --issuer """ + private_ca_subodinate + """  --issuer-location """ + subordinate_ca_region + """ \
       --generate-key     --key-output-file ./key \
       --cert-output-file ./cert.crt     --dns-san \" """ + san + """ \"  \
       --reusable-config \"""" + reusable_config + """\" """
    #_shell_command = "gcloud info ; ls -ltr "
    execute_shell_command(_shell_command)

    # Read the cert into memory
    with open('cert.crt') as f:
        _temp_cert = f.read()
    f.close()


    # Read the private_key into memory
    with open('key') as f:
        _temp_key = f.read()
    f.close()


    # Now that we have cert and private_key create a new LB SSL-cert
    print ("in private_ca_issue_LB_cert_from_subordinate region is: " + lb_region)
    private_ca_insert_new_self_managed_LB_cert(service, project, cert_name, _temp_cert, _temp_key , lb_region)

    #remove temp cert and _temp_key
    os.remove("cert.crt")
    os.remove("key")



def private_ca_update_target_https_proxy_ssl (service, project, https_proxy_name, cert_name, _region="global"):
    #TODO: to be replaced with Python SDK
    if (_region == "global"):
        command_region = "" ; # the default is global so we don't need to add anything
    else:
        command_region = "--region=" + _region ; # Add the region string to the command, e.g: us-central1

    _shell_command = "gcloud compute target-https-proxies update " + https_proxy_name + " --ssl-certificates=" + cert_name + " " + command_region

    print ("Executing command: " + _shell_command )    

    execute_shell_command (_shell_command)

def execute_shell_command(bashCommand):
    # TODO: Add try - catch, consider subprocess
    print (bashCommand)
    os.system(bashCommand)

def get_cert_dates(service, project, cert_name, _region):
    if (_region == "global"):
        cert_request = service.sslCertificates().get(project=project, sslCertificate=cert_name)
    else:
        cert_request = service.regionSslCertificates().get(project=project, sslCertificate=cert_name , region = _region)

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
