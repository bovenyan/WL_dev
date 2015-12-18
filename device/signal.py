from multiprocessing import Process, Lock, Queue
from subprocess import Popen, PIPE
from time import sleep
import ConfigParser
import requests
import json
import os
import signal
from servo import servo


class signaling(object):
    def __init__(self, conf_path):
        config = ConfigParser.ConfigParser()
        config.read(conf_path)

        self.dev_id = int(config.get("servoConfig", "devID"))

        self.mgmt_sleep = int(config.get("servoConfig", "mgmtSleep"))
        self.op_sleep = int(config.get("servoConfig", "opSleep"))
        self.blaster = open('/dev/servoblaster', 'w')
        self.rest_addr = self.server_ip + ":" + self.server_port
        self.url = "http://" + self.rest_addr + "/dev/" + str(self.dev_id)

        self.des_queue_x = Queue()
        self.des_queue_y = Queue()
        self.cur_queue_x = Queue()
        self.cur_queue_y = Queue()

        lock = Lock()
        self.servo_x = servo(config, 0, self.blaster, lock,
                             self.des_queue_x, self.cur_queue_x)
        self.servo_y = servo(config, 1, self.blaster, lock,
                             self.des_queue_y, self.cur_queue_y)

        self.step = int(config.get("servoConfig", "step"))
        self.server_ip = config.get("servoConfig", "serverIP")
        self.server_port = config.get("servoConfig", "serverPort")

        self.process = Process(target=self.signal_channel, args=())
        self.process.start()
        self.ssh = None

    def signal_channel(self):
        headers = {'Content-Type': 'application/json'}

        servo_positions = [0, 0]

        while True:
            # TODO check conn
            ans = requests.get(self.url)
            ans = ans.json()

            if 'reset' in ans:
                Popen(["pkill", "ssh"])
                continue

            if ans['manage']:  # management mode
                # TODO: Shutdown all the operational video
                sleep(self.mgmt_sleep)

                response = {}

                if ('servo_active' in ans and ans['servo_active']):  # servo
                    if (not ans['servo_turn_mode']):  # inc
                        if(not ans['servo_inc_xy']):  # x=0, y=1
                            self.des_queue_x.put(servo_positions[0] + self.step)
                        else:
                            self.des_queue_y.put(servo_positions[1] + self.step)
                    else:  # pos
                        self.des_queue_x.put(ans['pos_x'])
                        self.des_queue_y.put(ans['pos_y'])

                    sleep(1)  # wait for servo to react and get position
                    if (not self.cur_queue_x.empty()):
                        servo_positions[0] = self.cur_queue_x.get()
                    if (not self.cur_queue_y.empty()):
                        servo_positions[1] = self.cur_queue_y.get()

                    if (servo_positions[0] == int(ans['pos_x']) and
                       servo_positions[1] == int(ans['pos_y'])):
                        response["servo_turned"] = True   # turned as expected
                    else:
                        response["servo_turned"] = False

                    response["pos_x"] = servo_positions[0]
                    response["pos_y"] = servo_positions[1]

                if ('picture' in ans and ans['picture']):  # take picture
                    filename = "dev" + str(self.dev_id) + ".jpg"
                    os.popen("rm " + filename)
                    os.popen("raspistill -t 10 -o " + filename + " &")
                    sleep(1)  # wait for picture to take

                    try:
                        open(filename)
                    except IOError:
                        # print "cannot open"
                        response["picture_taken"] = False
                    else:
                        # TODO check conn
                        resp = requests.post(self.url + "/picture",
                                             files={"file": open(filename,
                                                                 'rb')})

                    if (resp.status_code == 200):
                        response["picture_taken"] = True
                    else:
                        response["picture_taken"] = False

                if ('ssh' in ans and ans['ssh']):
                    self.ssh = Popen(["ssh", "-R",
                                      "10000:localhost:22",
                                      "dev@"+self.server_ip,
                                      "-o StrictHostKeyChecking=no"],
                                     stdout=PIPE,
                                     stderr=PIPE)
                    response["tunnel_opened"] = True

                # TODO update script
                if ('update' in ans and ans['update']):
                    pass
                elif ('commit' in ans and ans['commit']):
                    pass

                # Response completion of jobs
                # TODO check conn
                resp = requests.post(self.url, data=json.dumps(response),
                                     headers=headers)
            else:
                sleep(self.op_sleep)

    def distroy_channel(self):
        self.process.terminate()
        self.servo_x.disable_servo()
        self.servo_y.disable_servo()


if __name__ == "__main__":
    ss = signaling("/home/pi/wikkit/singal/config.ini")
    signal.pause()
    ss.distroy_channel()
