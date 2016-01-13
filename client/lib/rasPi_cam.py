import requests
import json
from wikkit_device import WikkitDevice

headers = {'Content-Type': 'application/json'}


class RasPiCam(WikkitDevice):
    def __init__(self, url, dev_id):
        super(RasPiCam, self).__init__(url, "piCam",  dev_id)

    def route_query(self, query):
        if super(RasPiCam, self).route_query(query):
            return True

        element = query.split()

        if (element[0] == "help"):  # print help
            self._print_help()
            return True

        if (element[0] == "shot"):   # take picture
            if (len(element) > 1):
                self._handle_camera(element[1:])
            else:
                self._print_help()
            return True

        if (element[0] == "servo"):  # tested
            if (len(element) > 1):
                self._handle_servo(element[1:])
            else:
                self._print_help()
            return True

        return False

    def _print_help(self):
        print "Status: You are controlling piCam-" + str(self.dev_id)
        super(RasPiCam, self)._print_help()
        if (self.manage_mode):
            print "         shot a picture: e.g. >camera shot"
            print "             To fetch a picture, please use sftp or scp"
            print "             The picture is named dev_<device ID>.jpg in ~"
            print "         "
            print "         turn the servo: e.g. >servo position 30 50"
            print "         "
        else:
            pass

    def _handle_camera(self, element):
        if (element[0] == "shot"):
            response = requests.post(self.url + "/picture/shot")
            if (not self._validate_response(response)):
                print "Failed..."
            return
        if (element[0] == "archive"):
            pass

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
