# GCP-CA-Service-Helper-Scripts

This repository includes helper scripts for the GCP Certificate Authority Service.

## Installation
pip3 install -r requirements.txt
```sh
 export CLOUDSDK_PYTHON_SITEPACKAGES=1;
 ```

## Renew Load-Balancers self-managed certifications in a project
Overview:
This script rotates external load balancers SSL certificate when the certificate's remaining cert life is less then a threshold. For example, if remaining cert life threshold is set to  50%, then a 30 days cert will be renewed 15 days before expiration. If remaining cert life threshold is set to 90%, then a 24hrs cert will be renewed 2.4hrs before certification expiration.
The script assumes all certificates are issued from a pre-configured subordinate CA named 'private-ca-subordinate-name'.

Usage:
```sh
python3 private_ca_renew_lb_in_project.py <project-id> <private-ca-subordinate-name>
```
