import ConfigParser
import requests
from lib.rasPi_cam import RasPiCam
from lib.tk1 import TK1
from lib.welcome import print_welcome

# config parsing
config = ConfigParser.ConfigParser()
conf_path = "./config.ini"
config.read(conf_path)

# Init
url = "http://" + config.get("signal", "server") + "/usr/"
headers = {'Content-Type': 'application/json'}
device = None

# negotiate version
negotiated = False
version = "0.0"
version = config.get("general", "version")
try:
    response = requests.get(url + "version", headers=headers)
    if (response.ok and isinstance(response.json(), dict) and
       "version" in response.json()):
        serverVersion = response.json()["version"]
        if (serverVersion != version):
            print "Local Version is outdated, server version is " + "v" + \
                serverVersion
            print "Please run \"git pull\" to update the entire repository"
            print "And run \"git checkout " + "v" + serverVersion
        else:
            print_welcome()
            print "Welcome to WikkitDev-Tsuki (version " + version + ")"
            negotiated = True
    else:
        print "Version check Failed. Maybe connection is unstable"

except Exception, e:
    print str(e)
    print "Version check Failed. Maybe connection is unstable"

# processing requests
while(negotiated):
    if (device is None):
        query = raw_input('Wikkit Platform > ')

        element = query.split()
        if (element is None or len(element) == 0):  # tested
            continue

        if (element[0] == "help"):  # tested
            print "**** You are in normal mode****"
            print "Manage device with certain ID: > cam-1 or > tk-1"
            print "Exit this platform: > exit"

        if (element[0] == "exit"):  # tested
            print "Exiting... Bye"
            break

        if (element[0].startswith("cam-")):   # control a rasPi
            div = element[0].split('-')
            try:
                dev_id = int(div[1])
                device = RasPiCam(url, dev_id)
            except Exception, e:
                print str(e)
                print "maybe connection is bad, retry..."
                continue

        if (element[0].startswith("tk-")):
            div = element[0].split('-')
            try:
                dev_id = int(div[1])
                device = TK1(url, dev_id)
            except Exception, e:
                print str(e)
                print "maybe connection is bad, retry..."
                continue

    else:
        if (device.manage_mode):
            query = raw_input("Device " + device.name + ": (management) > ")
        else:
            query = raw_input("Device " + device.name + ": (operational) > ")
        try:
            device.route_query(query)

            if (not device.active):
                del device
                device = None

        except Exception, e:
            print str(e)
            print "Connection is unstable, retry..."
            continue
