import ConfigParser
import file_trans as fTrans
from cam import cam

config = ConfigParser.ConfigParser()
conf_path = "./config.ini"
config.read(conf_path)
url = "http://" + config.get("signalConfig", "server") + "/usr/"
headers = {'Content-Type': 'application/json'}
# serverSSHport = config.get("clientConfig", "sshTunnelPort")
fileAdapt = fTrans.fileAdapter(conf_path)
device = None

while(True):
    if (device is None):
        query = raw_input('Wikkit Platform > ')

        element = query.split()
        if (element is None or len(element) == 0):  # tested
            continue
        if (element[0] == "help"):  # tested
            print "some help for main"

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
                print "some help"

    else:
        if (device.manage_mode):
            query = raw_input("Wikkit Device " + str(device.dev_id) +
                              ": (management) > ")
        else:
            query = raw_input("Wikkit Device " + str(device.dev_id) +
                              ": (operation) > ")
        device.route_query(query)

        if (not device.active):
            del device
            device = None
