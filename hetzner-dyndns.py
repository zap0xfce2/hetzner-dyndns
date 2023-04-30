import requests
import json
import sys
import os

from dotenv import load_dotenv
load_dotenv('.env')

# Set Variables
dns_zone = os.getenv("DNS_ZONE")
dyndns_names = os.getenv("DYNDNS_NAMES").split(",")
api_key = os.getenv("API_KEY")

# DO NOT SET!
dyndns_ttl = 7200
external_ip_address = ""  # Do not set!
dns_record_id = ""  # Do not set!
dns_record_type = ""  # Do not set!

# Get External IP Address
response = requests.get("https://ipv4.icanhazip.com")
if response.status_code == 200:
    external_ip_address = response.text.strip()
else:
    print("There was an error retrieving the external IP address. Please check your internet connection and try again.")
    sys.exit(1)

# Get Zone ID for dns_zone
url = "https://dns.hetzner.com/api/v1/zones?name={}".format(dns_zone)
headers = {"Auth-API-Token": api_key}
response = requests.get(url, headers=headers)
zone_id = response.json()["zones"][0]["id"]

# Get all DNS Records for Zone dns_zone
url = "https://dns.hetzner.com/api/v1/records?zone_id={}".format(zone_id)
response = requests.get(url, headers=headers)
dns_records = response.json()["records"]

# Manage Record
for dyndns_name in dyndns_names:
    dns_record_id = ""
    dns_record_type = ""
    for record in dns_records:
        if record["name"] == dyndns_name:
            dns_record_id = record["id"]
            dns_record_type = record["type"]
            break

    # Assert that the Record is from Type A
    if len(dns_record_type) > 0 and dns_record_type != "A":
        print("The DNS Record {} already exists with a Record Type of {}. Needs to be Type A.".format(dyndns_name, dns_record_type))
        sys.exit(1)

    # Create or update DYNDNS Record
    if len(dns_record_id) == 0 and len(external_ip_address) > 0:
        url = "https://dns.hetzner.com/api/v1/records"
        body = {"name": dyndns_name, "type": "A", "value": external_ip_address, "zone_id": zone_id, "ttl": dyndns_ttl}
        response = requests.post(url, headers=headers, json=body)
        print("Creating a new record...")
    elif len(dns_record_id) > 0 and len(external_ip_address) > 0:
        # Check IP bevore updating it
        url = "https://dns.hetzner.com/api/v1/records/{}".format(dns_record_id)
        response = requests.get(url, headers=headers)
        record_ip = response.json()["record"]["value"]
        if record_ip != external_ip_address:
            url = "https://dns.hetzner.com/api/v1/records/{}".format(dns_record_id)
            body = {"name": dyndns_name, "type": "A", "value": external_ip_address, "zone_id": zone_id, "ttl": dyndns_ttl}
            response = requests.put(url, headers=headers, json=body)
            print("Updating the IP of the record...")
        else:
            print("Your IP is the same as the record's IP. No update necessary!")

    if response.status_code != 200 and response.status_code != 201:
        print("There was an Error DNS name {} registration. Proceed with next entry!".format(dyndns_name))
        continue
