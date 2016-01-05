import requests
import json
from time import sleep
# from pressKey import press

headers = {'Content-Type': 'application/json'}


class cam(object):
    def __init__(self, url, dev_id, fileAdapt):
        self.dev_id = str(int(dev_id))
        self.url = url + str(int(dev_id))
        self.active = True
        self.manage_mode = False
        response = requests.get(self.url + "/mode", headers=headers)
        if (response.ok and not (response.json() is None)):
            if ("is_mgmt" in response.json()):
                self.manage_mode = response.json()["is_mgmt"]
        self.fileAdapt = fileAdapt

    def route_query(self, query):
        element = query.split()

        if (element is None or len(element) == 0):  # tested
            return

        if (element[0] == "help"):  # tested
            self._print_help()
            return

        if (element[0] == "reset"):  # tested
            requests.post(self.url+"/reset")
            return

        if (element[0] == "management"):  # tested
            response = requests.post(self.url + "/mode",
                                     headers=headers, data=json.dumps(True))
            if (self._validate_response(response)):
                content = response.json()
                if ("wait" in content):
                    wait = int(content["wait"])
                    print "Management Set, Device not ready..."
                    if (wait > 1800):
                        print "Fatal: Device haven't been seen for too long."
                        print "Please Notify Administrator asap."
                        return

                    print "Please wait for " + str(wait) + " seconds"
                    sleep(wait)
                print "Device management ready"
                self.manage_mode = True
                return
            else:
                print "Failed..."
                return

        if (element[0] == "renew"):
            response = requests.post(self.url + "/renew")
            time = 15

            if (len(element) > 1):
                try:
                    time = int(element[1])
                    if time > 30:
                        print "Renew up to 30 minutes, please retry ..."
                        return
                except Exception, e:
                    print str(e)
                    self._print_help()
                    return

            print "Renew " + str(time) + " minutes for management mode"

            response = requests.post(self.url + "/renew/" + str(time))

            if (not self._validate_response(response)):
                print "failed..."

            return

        if (element[0] == "operation"):  # tested
            self._reset_operation()
            return

        if (element[0] == "exit"):  # tested
            if (self.manage_mode):
                confirm = raw_input("return operational ?(y/N):")
                if (confirm == 'y' or confirm == 'Y'):
                    self._reset_operation()
            self.active = False
            return

        if (element[0] == "camera"):   #
            if (len(element) > 1):
                self._handle_camera(element[1:])
            else:
                self._print_help()
            return

        if (element[0] == "ssh"):   # tested
            if (len(element) > 1):
                self._handle_ssh(element[1:])
            else:
                self._print_help()
            return

        if (element[0] == "servo"):  # tested
            if (len(element) > 1):
                self._handle_servo(element[1:])
            else:
                self._print_help()
            return

    def _validate_response(self, response):
        if (response.ok):
            content = response.json()
            if ("success" in content):
                if (content["success"]):
                    return True
                else:
                    if ("is_mgmt" in content and not content["is_mgmt"]):
                        self.manage_mode = False
                        print "Not in Management Mode, Perhaps the device"
                        print "timeouts. Please enable management mode again"
                        return False
            else:
                print "Warning Impossible Output, mind MIM attack "
        return False

    def _reset_operation(self):
        response = requests.post(self.url + "/mode",
                                 headers=headers, data=json.dumps(False))
        if (self._validate_response(response)):
            self.manage_mode = False
        else:
            print "Failed..."
            return

    def _print_help(self):
        print "**** You are in cam mode, you are controlling an RasPi ****"
        print "Exit to normal mode:  e.g. >exit"
        print "Enter Management mode: e.g. >management"
        print "     In management mode, you can:"
        print "         shot a picture: e.g. >camera shot"
        print "         query the id of the newest picture: e.g. >camera query"
        print "         get the picture: e.g. >camera get <PICTURE ID>"
        print "         "
        print "         enable an ssh tunnel from cloud to the camera"
        print "             start a tunnel e.g. >ssh start"
        print "             stop a tunnel e.g. >ssh stop"
        print "             restart a tunnel e.g. >ssh restart"
        print "         "
        print "         turn the servo: e.g. >servo position 30 50"
        print "         "
        print "         reset the device: e.g. >reset"
        print "             Note: this will only reset ssh, not servo position"
        print "Enter Operational mode: e.g. >operation"
        print "     In operational mode: you can:"
        print "         do nothing currently"

    def _handle_camera(self, element):
        if (element[0] == "shot"):
            response = requests.post(self.url + "/picture/shot")
            if (not self._validate_response(response)):
                print "Failed..."
            return

        if (element[0] == "query"):
            response = requests.post(self.url + "/picture/query")
            if (self._validate_response(response)):
                content = response.json()
                if ("file" in content):
                    print "file id: " + str(content["file"])
                    confirm = raw_input("fetch the file?(y/N)")

                    if (confirm == 'y' or confirm == "Y"):
                        file_url = self.url + "/picture/get"
                        file_name = "dev_" + self.dev_id + ".jpg"
                        remote_file_name = "dev_" + content["file"] + ".jpg"
                        self.fileAdapt.recv_from_url(file_url,
                                                     remote_file_name,
                                                     file_name)
                        requests.post(self.url+"/picture/fetched")
                    else:
                        print "fetch by \"> get <file_id>\""
                else:
                    print "Warning: impossible output, mind MIM attack"

            else:
                print "Failed... device busy, try again later or reset device"

        if (element[0] == "get" and len(element) == 2):
            file_url = self.url + "/picture/get"
            remote_file_name = "dev_" + str(element[1]) + ".jpg"
            file_name = "dev_" + self.dev_id + ".jpg"
            self.fileAdapt.recv_from_url(file_url,
                                         remote_file_name,
                                         file_name)
            requests.post(self.url+"/picture/fetched")

    def _handle_ssh(self, element):  # tested
        if (element[0] == "start"):
            response = requests.post(self.url+"/ssh/start")
            if (self._validate_response(response) and
               "port" in response.json()):
                print "ssh tunnel started, please login with another terminal"
                print "If you are logging in a raspberryPi, do:"
                print "> ssh pi@<alicloud IP> -p " + \
                    str(response.json()["port"])
                print "If you are logging in a tk1, do:"
                print "> ssh ubuntu@<alicloud IP> -p " + \
                    str(response.json()["port"])
            else:
                print "failed to start..."
            return

        if (element[0] == "stop"):
            response = requests.post(self.url+"/ssh/stop")
            if (self._validate_response(response)):
                print "ssh stopped"
            return

        if (element[0] == "restart"):
            response = requests.post(self.url+"/ssh/restart")
            if (response.ok and "port" in response.json()):
                print "ssh tunnel started, please:"
                print "1. logon dev@cloud"
                print "2. cloud> ssh pi@localhost -p " + \
                    str(response.json()["port"])
            else:
                print "failed to start..."
            return

        if (element[0] == "zombie"):
            res = raw_input("Are you sure the ssh tunnel turns zombie? (y/N)")
            if (res == 'y' or res == 'Y'):
                response = requests.post(self.url + "/ssh/zombie")
                print "reset before making a new ssh tunnel. resetting..."
                response = requests.post(self.url+"/ssh/restart")
            else:
                print "try again at cloud >ssh@localhost -p <designated port>"
            return

        if (element[0] == "renew"):
            time = 15
            if (len(element) > 1):
                try:
                    time = int(element[1])
                    if (time > 90):
                        print "Renew up to 90 minuts for ssh, please retry..."
                        return
                except Exception, e:
                    print str(e)
                    self._print_help()
                    return
            response = requests.post(self.url + "/ssh/renew",
                                     headers=headers,
                                     data=json.dumps(time))
            if (not self._validate_response(response)):
                print "failed..."
            else:
                return

        self._print_help()

    def _handle_servo(self, element):  # tested
        try:
            if (element[0] == "position"):
                data = {"pos_x": int(element[1]), "pos_y": int(element[2])}
                requests.post(self.url+"/servo",
                              data=json.dumps(data),
                              headers=headers)
                return

            """
            if (element[2] == "monitor"):
                # TODO monitor
                print "entering monitor mode..."
                result = 1
                while result != 0:
                    result = press()
                    if (result == 1):  # up
                        data = {"inc_dec": False, "xy": False}

                    if (result == 2):  # down
                        data = {"inc_dec": True, "xy": False}

                    if (result == 3):  # left
                        data = {"inc_dec": False, "xy": True}

                    if (result == 4):  # left
                        data = {"inc_dec": True, "xy": True}

                    if (result == 5):  # take picture
                        with open('dev_'+self.dev_id+".jpg", 'wb') as handle:
                            response = requests.get(self.url + "/picture")
                            if not response.ok:
                                print "picture receive failed"
                                break

                            for block in response.iter_content(1024):
                                handle.write(block)

                print "exiting monitor mode... Bye"
                continue
            """
            self._print_help()
        except Exception, e:
            print str(e)
            self._print_help()
