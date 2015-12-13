from multiprocessing import Process, Lock, Queue
from subprocess import Popen, PIPE
from time import sleep
import ConfigParser
import requests
import json
import os


class servo_sig(object):
    def __init__(self, conf_path):
        config = ConfigParser.ConfigParser()
        config.read(conf_path)

        self.dev_id = int(config.get("servoConfig", "devID"))

        self.mgmt_sleep = int(config.get("servoConfig", "mgmtSleep"))
        self.op_sleep = int(config.get("servoConfig", "opSleep"))
        self.blaster = open('/dev/servoblaster', 'w')

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
        self.server_ip = config.get("serverConfig", "serverIP")
        self.server_port = config.get("serverConfig", "serverPort")
        self.rest_addr = self.server_ip + ":" + self.server_port

        self.process = Process(target=self.signal_channel, args=())
        self.process.start()
        self.ssh = None

    def signal_channel(self):
        dev_url = "http://" + self.rest_addr + "/dev/" + str(self.dev_id)
        headers = {'Content-Type': 'application/json'}

        servo_positions = [0, 0]

        while True:
            # TODO check conn
            ans = requests.get(dev_url)
            ans = ans.json()

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
                        resp = requests.post(dev_url + "/picture",
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
                    pass

                # TODO update script
                if ('update' in ans and ans['update']):
                    pass
                elif ('commit' in ans and ans['commit']):
                    pass

                # Response completion of jobs
                # TODO check conn
                resp = requests.post(dev_url, data=json.dumps(response),
                                     headers=headers)
            else:
                sleep(self.op_sleep)

    def distroy_channel(self):
        self.process.terminate()
        self.servo_x.disable_servo()
        self.servo_y.disable_servo()


class servo(object):
    def __init__(self, config, sID, blaster, lock, des_queue, cur_queue):
        self.cur_pos = 0
        self.blaster = blaster
        self.servo_str = "P1-" + config.get("servoConfig",
                                            "servo"+str(sID)+"Pin") + "="
        self.sID = sID

        volt_str = config.get("servoConfig", "servo"+str(sID) + "volt")
        volt_str = volt_str.split(",")
        self.servo_voltage = [int(volt_str[0]), int(volt_str[1])]
        self.ratio = float(self.servo_voltage[1] - self.servo_voltage[0])/180

        self.lock = lock
        self.sleepTime = 0.1

        self.des_queue = des_queue
        self.cur_queue = cur_queue

        # init
        lock.acquire()
        self.blaster.write(self.servo_str +
                           str(90 * self.ratio + self.servo_voltage[0]) + '\n')
        self.blaster.flush()
        lock.release()

        sleep(2)

        self.process = Process(target=self.move, args=())
        self.process.start()

    def move(self):
        cur_pos = 0
        while True:
            sleep(self.sleepTime)
            if (self.des_queue.empty()):
                pass
            else:
                des_pos = self.des_queue.get()

                if (des_pos == cur_pos or des_pos > 90 or des_pos < -90):
                    # posistion range [-90, 90]
                    pass
                else:
                    volt = float(des_pos + 90) * self.ratio + \
                                self.servo_voltage[0]
                    volt = max(self.servo_voltage[0], volt)
                    volt = min(self.servo_voltage[1], volt)
                    # print "voltage : " + str(volt)
                    self.lock.acquire()
                    self.blaster.write(self.servo_str + str(volt) + '\n')
                    self.blaster.flush()
                    self.lock.release()
                    cur_pos = des_pos
                    # print "servo" + str(self.sID) + " cur: " + str(cur_pos)
                    # print "servo" + str(self.sID) + " dst: " + str(des_pos)
                    self.cur_queue.put(cur_pos)

    def disable_servo(self):
        self.process.terminate()


if __name__ == "__main__":
    ss = servo_sig("./config.ini")
    raw_input("press enter to continue")
    ss.distroy_channel()
