import requests
import json
# from pressKey import press

headers = {'Content-Type': 'application/json'}


class cam(object):
    def __init__(self, url, dev_id, fileAdapt):
        self.dev_id = str(int(dev_id))
        self.url = url + str(int(dev_id))
        self.active = True
        self.manage_mode = False
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
                self.manage_mode = True
                return
            else:
                print "not yet ready... please wait for 5 min"
                return

        if (element[0] == "operation"):  # tested
            self._reset_operation()
            return

        if (element[0] == "exit"):  # tested
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
            self._handle_ssh()
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
                return content["success"]
            else:
                print "Warning Impossible Output, mind MIM attack "
        return False

    def _reset_operation(self):
        response = requests.post(self.url + "/mode",
                                 headers=headers, data=json.dumps(False))
        if (self._validate_response(response)):
            self.manage_mode = False
        else:
            print "failed to set operation"
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
        print "         start an ssh tunnel from cloud to the camera: e.g. >ssh"
        print "         "
        print "         turn the servo: e.g. >servo posision 30 50"
        print "         "
        print "         reset the device: e.g. >reset"
        print "             Note: this will only reset ssh, not servo position"
        print "Enter Operational mode: e.g. >operation"
        print "     In operational mode: you can:"
        print "         do nothing currently"

    def _handle_camera(self, element):
        if (element[0] == "shot"):
            requests.post(self.url + "/picture/shot")
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
                print "device busy, try again later or reset device"

        if (element[0] == "get" and len(element) == 2):
            file_url = self.url + "/picture/get"
            remote_file_name = "dev_" + str(element[1]) + ".jpg"
            file_name = "dev_" + self.dev_id + ".jpg"
            self.fileAdapt.recv_from_url(file_url,
                                         remote_file_name,
                                         file_name)
            requests.post(self.url+"/picture/fetched")

    def _handle_ssh(self):  # tested
        response = requests.get(self.url+"/ssh")
        if (response.ok and "port" in response.json()):
            print "ssh tunnel started, please:"
            print "1. logon dev@cloud"
            print "2. cloud> ssh pi@localhost -p " + \
                str(response.json()["port"])
        else:
            print "failed..."

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
            self.print_help()
        except Exception, e:
            print str(e)
            self.print_help()
