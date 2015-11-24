import ConfigParser
import requests
import json
from pressKey import press

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
	print "Exiting... Bye"
	break;

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
		continue

            if (element[1] == "servo"):
                if (element[2] == "position"):
                    data = {"pos_x": int(element[3]), "pos_y": int(element[4])}
                    requests.post(url+"/usr/servo/"+str(devID),
                                  data=json.dumps(data),
                                  headers=headers)
		    continue

                if (element[2] == "monitor"):
                    # TODO monitor
		    print "entering monitor mode..."

		    result = 1
		    while result != 0:
			result = press()

			url_monitor = url + "/usr/servo/" + str(devID)

			if (result == 1):  # up
			    data = {"inc_dec": False, "xy": False}

			if (result == 2):  # down
			    data = {"inc_dec": True, "xy": False}

			if (result == 3):  # left
			    data = {"inc_dec": False, "xy": True}

			if (result == 4):  # left
			    data = {"inc_dec": True, "xy": True}

			if (result == 5):  # take picture
            		    with open('dev_'+str(devID)+".jpg", 'wb') as handle:
                    		response = requests.get(url+"/usr/picture/"+str(devID))
                    		if not response.ok:
                       		    print "picture receive failed"
                       		    break
				for block in response.iter_content(1024):
                        	    handle.write(block)
			    
		    print "exiting monitor mode... Bye"
                    continue

        except Exception, e:
            print "read code"

