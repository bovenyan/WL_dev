import requests
import json
from time import sleep

headers = {'Content-Type': 'application/json'}


class WikkitDevice(object):
    def __init__(self, url, dev_type, dev_id):
        self.url = url + dev_type + "/" + str(dev_id)
        self.dev_id = dev_id
        self.active = True
        self.manage_mode = False
        self.dev_type = dev_type
        self.name = dev_type + "-" + str(dev_id)

        # fetch initate state
        response = requests.get(self.url + "/mode", headers=headers)

        if (response.ok and not (response.json() is None)):
            if ("is_mgmt" in response.json()):
                self.manage_mode = response.json()["is_mgmt"]

    def route_query(self, query):
        element = query.split()

        if (element is None or len(element) == 0):  # no query
            return True

        if (element[0] == "help"):  # print help
            self._print_help()
            return True

        if (element[0] == "reset"):  # reset the device
            requests.post(self.url+"/reset")
            self.manage_mode = False
            return True

        if (element[0] == "management"):  # enter management
            response = requests.post(self.url + "/mode",
                                     headers=headers, data=json.dumps(True))
            if (self._validate_response(response)):
                content = response.json()
                if ("wait" in content):
                    wait = int(content["wait"])
                    print "Management Set, Device not ready..."
                    if ("miss" in content):
                        if int(content["miss"]) > 1000:
                            print "Fatal: Device haven't been reported for " + \
                                str(content["miss"]) + " cycles"
                            print "Please Notify Administrator asap."
                            return True
                        else:
                            print "Warning: Device occationally experience" + \
                                  "poor connection, expect unstable performance"

                    print "Please wait for " + str(wait) + " seconds"
                    sleep(wait)

                # TODO: Check the status to confirm

                print "Device management ready"
                self.manage_mode = True
                return True
            else:
                print "Failed..."
                return True

        if (element[0] == "operation"):  # enter operation mode
            self._reset_operation()
            return True

        if (element[0] == "exit"):  # exit the program
            if (self.manage_mode):
                confirm = raw_input("return operational ?(y/N):")
                if (confirm == 'y' or confirm == 'Y'):
                    self._reset_operation()
            self.active = False
            return True

        """
        Ops in management
        """
        if (element[0] == "ssh"):   # tested
            if (len(element) > 1):
                self._handle_ssh(element[1:])
            else:
                self._print_help()
            return

        """
        Ops in operation
        """

        return False

    def _validate_response(self, response):  # validating server response
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

    def _reset_operation(self):  # flop back to operational mode
        response = requests.post(self.url + "/mode",
                                 headers=headers, data=json.dumps(False))
        if (self._validate_response(response)):
            self.manage_mode = False
        else:
            print "Failed..."
            return

    def _handle_ssh(self, element):
        if (element[0] == "start"):
            response = requests.post(self.url+"/ssh/start")
            self._print_ssh_help(response)
            return True

        if (element[0] == "stop"):
            response = requests.post(self.url+"/ssh/stop")
            if (self._validate_response(response)):
                print "ssh stopped"
            else:
                print "failed to stop"
            return True

        if (element[0] == "restart"):
            response = requests.post(self.url+"/ssh/restart")
            self._print_ssh_help(response)
            return True

        if (element[0] == "zombie"):
            res = raw_input("Are you sure the ssh tunnel turns zombie? (y/N)")
            if (res == 'y' or res == 'Y'):
                print "Killing Zombies..."
                response = requests.post(self.url + "/ssh/zombie")
                print "Resetting..."
                response = requests.post(self.url+"/ssh/restart")
                self._print_ssh_help(response)
            else:
                print "Abort..."
            return True

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
                    return False
            response = requests.post(self.url + "/ssh/renew",
                                     headers=headers,
                                     data=json.dumps(time*60))
            if (not self._validate_response(response)):
                print "failed..."
            else:
                print "Renewed " + str(time) + " minutes."
                return True

        return False

    def _print_ssh_help(self, response):  # help for ssh tunnel
        if (self._validate_response(response) and
           "port" in response.json()):
            openPort = response.json()["port"]

            if (self.dev_type == "piCam"):
                print "ssh tunnel started, please login with another terminal"
                print "   > ssh pi@<alicloud IP> -p " + str(openPort)
                print "   > sftp -P " + str(openPort) + " pi@<alicloud IP>"
            if (self.dev_type == "tk1"):
                print "ssh tunnel started, please login with another terminal"
                print "   > ssh ubuntu@<alicloud IP> -p " + str(openPort)
                print "   > sftp -P " + str(openPort) + " pi@<alicloud IP>"
        else:
            print "Failed to start..."

    def _print_help(self):
        if self.manage_mode:
            print "Status: You are in Management Mode"
            print "  Mangement Mode Options:"
            print "    Check the Status of Current Management Session: > status"
            print "     "
            print "    Go to Operational Mode: > operation"
            print "     "
            print "    Return to upper-level menu: > exit"
            print "     "
            print "    Create access to the device (ssh/sftp/scp):"
            print "      - start a tunnel: > ssh start"
            print "      - stop a tunnel:  > ssh stop"
            print "      - restart a tunnel: > ssh restart"
            print "      - renew n minutes for ssh: > ssh renew 20"
            print "           Note: by default ssh has a hard timeout of 30 min"
            print "      - fix dead ssh tunnel: > ssh zombie"
            print "           Note: This can be DANGER, please try <stop> first"
            print "     "
            print "    Reset the device: e.g. > reset"
            print "           Note: This will not affect servo position"
            print "     "
        else:
            print "Status: You are in Operational Mode"
            print "  Operational Mode Options"
            print "    Check the Status of Current Operational Status: > status"
            print "     "
            print "    Go to Management Mode: > management"
            print "     "
            print "    Return to upper-level menu: > exit"
            print "     "
