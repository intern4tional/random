#!/usr/bin/env python
"""Foobar.py: Description of what foobar does."""

__author__      = "Caleb Mcgary"
__copyright__   = "Copyright 2024, Tokyo, Japan"

import requests
import datetime

# Base URLS
api_url = "https://esi.evetech.net/latest/"
headers = {'user-agent': 'APP/BRIGHTLY BURNING/0.0.1'}
datasource = "?datasource=tranquility&language=en"

# Endpoints
# reference: https://matthew-brett.github.io/teaching/string_formatting.html
system_details_endpoint = "universe/systems/{}/"
system_jumps = "universe/system_jumps/"

# EVE System object
class EVE_System(object):
    system_id = ""
    system_name = ""
    last_updated = ""
    jumps = ""
    security_status = ""

    def __init__(self, system_id, system_name, last_updated, jumps, security_status):
        self.system_id = system_id
        self.system_name = system_name
        self.last_updated = last_updated
        self.jumps = jumps
        self.security_status = security_status

    def __str__(self):
        return f"{self.system_id},{self.system_name},{self.jumps},{self.security_status}"

# Create EVE System object
def make_system(system_id, system_name, last_updated, total_jumps, jumps_from_last_call):
    eve_system = EVE_System(system_id, system_name, last_updated, total_jumps, jumps_from_last_call)
    return eve_system

# Call EVE API
def make_api_call(endpoint):
    r = requests.get(f"{api_url}{endpoint}{datasource}", headers=headers)
    if (r.status_code==requests.codes.ok):
        return r.json()
    else:
        print("Error: Call Failure")
        print(endpoint," ", r.text)

# Get list of systems
def get_system_jumps():
    return make_api_call(system_jumps)

# Obtain system details for each system
def get_system_details(system_id):
    return make_api_call(system_details_endpoint.format(system_id))


def main():
    # Define holder of objects
    systems = []

    # Get system jumps and clean up result
    print("Getting System Jumps")
    system_jumps=get_system_jumps()

    print("Iterating over 3k systems")
    for s in system_jumps:
        x = get_system_details(s["system_id"])
        system = make_system(s["system_id"], x["name"], datetime.date,s["ship_jumps"], x["security_status"])
        systems.append(system)

    print("Writing results to file")
    with open('C:/src/results.csv', "a+", encoding="utf-8") as f:
        # csv header
        f.write("System_ID:, System_Name:, Jumps:, Security_Status:\n")
        for s in systems:
            f.write(s.__str__()+'\n')
    
    print("Completed")

if __name__ == "__main__": main()