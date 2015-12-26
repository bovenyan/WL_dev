import ConfigParser
import lib.file_trans as fTrans
import requests
from lib.cam import cam
from lib.welcome import print_welcome

# config parsing
config = ConfigParser.ConfigParser()
conf_path = "./config.ini"
config.read(conf_path)

# Init
url = "http://" + config.get("signal", "server") + "/usr/"
headers = {'Content-Type': 'application/json'}
fileAdapt = fTrans.fileAdapter(conf_path)
device = None

# negotiate version
negotiated = False
version = "0.0"
version = config.get("general", "version")
try:
    response = requests.get(url + "version", headers=headers)
    if (response.ok and isinstance(response.json(), dict) and
       "version" in response.json()):
        if (response.json()["version"] != version):
            print "Local Version is outdated, Please run \"git pull\" to update"
        else:
            print_welcome()
            print "Version 1.0"
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
            print "Type an device id to enter device mode: e.g. >cam-1"
            print "Exit this platform: e.g. exit"

        if (element[0] == "exit"):  # tested
            print "Exiting... Bye"
            break

        if (element[0].startswith("cam-")):   # control a cam   # tested
            camDev = element[0].split('-')
            try:
                dev_id = int(camDev[1])
                device = cam(url, dev_id, fileAdapt)
            except Exception, e:
                print str(e)
                print "maybe connection is bad, retry..."
                continue

    else:
        if (device.manage_mode):
            query = raw_input("Wikkit Device " + str(device.dev_id) +
                              ": (management) > ")
        else:
            query = raw_input("Wikkit Device " + str(device.dev_id) +
                              ": (operation) > ")
        try:
            device.route_query(query)

            if (not device.active):
                del device
                device = None

        except Exception, e:
            print str(e)
            print "Connection is unstable, retry..."
            continue
