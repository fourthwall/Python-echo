import requests
import os

# these are AWS environment variables - set them for your OpenHAB installation
hostname = os.environ['hostname']
port = os.environ['port']
user = os.environ['user']
password = os.environ['password']


# sends commands to OpenHAB for an item via its restful interface
# returns True for successful outcome, False for error.
# name is the item name, value is the payload data.
def postCommand(name, value):
    try:
        resp = requests.post("http://" + hostname + ":" + str(port) + "/rest/items/" + name,
                             headers={'Content-Type': 'text/plain', 'Content-Length': str(len(value))}, data=value,
                             auth=(user, password))
    except requests.exceptions.RequestException as e:
        print("HTTP error occured: " + str(e))
        return False
    if resp.status_code not in (200, 201):  # bad response
        print("got bad HTTP response code:" + resp.status_code)
        return False
    print("Successful request made: " + name + " " + value)  # All OK
    return True


# Obtains an "item" from the OpenHAB restful interface.
def getItem(name):
    try:
        resp = requests.get("http://" + hostname + ":" + str(port) + "/rest/items/" + name, auth=(user, password))
        if resp.status_code not in (200, 201):
            print("got bad HTTP response code:" + resp.status_code)
            return False
        json = resp.json()
    except Exception as e:
        print("Error: " + str(e))
        return False
    return json
