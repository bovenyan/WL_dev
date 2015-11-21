import ConfigParser
import requests
import json

config = ConfigParser.ConfigParser()
config.read("./config.ini")
url = "http://" + config.get("clientConfig", "server")
headers = {'Content-Type': 'application/json'}

while(True):
    in_put = raw_input('type help for help \n Wikkit Platform > ')

    element = in_put.split()

    if (element is None):
        continue

    if (element[0] == "exit"):
        return

    if (element[0].startswith("cam-")):   # control a cam
        try:
            camDev = element[0].split('-')

            devID = int(camDev[1])

            if (element[1] == "management"):
                pass

            if (element[1] == "operation"):
                pass

            if (element[1] == "shot"):
                with open('dev_'+str(devID)+".jpg", 'wb') as handle:
                    response = requests.get(url+"/usr/picture/"+str(devID))
                    if not response.ok:
                        print "picture receive failed"
                        break

                    for block in response.iter_content(1024):
                        handle.write(block)

            if (element[1] == "servo"):
                if (element[2] == "position"):
                    data = {"pos_x": int(element[3]), "pos_y": int(element[4])}
                    requests.post(url+"/usr/servo/"+str(devID),
                                  data=json.dumps(data),
                                  headers=headers)
                if (element[2] == "monitor"):
                    # TODO monitor
                    pass

        except Exception, e:
            print "read code"

    print "read code"
