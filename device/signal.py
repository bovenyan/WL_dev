from multiprocessing import Process, Lock, Queue
from subprocess import Popen
from time import sleep
import ConfigParser
import requests
import json
import os
import signal
from servo import servo
from process_mgmt import kill_pids_of_port

import logging

logging.basicConfig(filename='rasPi.log', level=logging.DEBUG)


class signaling(object):
    def __init__(self, conf_path):
        config = ConfigParser.ConfigParser()
        config.read(conf_path)

        self.dev_id = int(config.get("signalConfig", "devID"))
        self.mgmt_sleep = int(config.get("signalConfig", "mgmtSleep"))
        self.op_sleep = int(config.get("signalConfig", "opSleep"))
        self.server_ip = config.get("signalConfig", "serverIP")
        self.server_port = str(int(config.get("signalConfig", "serverPort")))
        self.rest_addr = self.server_ip + ":" + self.server_port
        self.url = "http://" + self.rest_addr + "/dev/" + str(self.dev_id)

        self.des_queue_x = Queue()
        self.des_queue_y = Queue()
        self.cur_queue_x = Queue()
        self.cur_queue_y = Queue()

        self.blaster = open('/dev/servoblaster', 'w')

        # debug **
        # self.debug_count = 10
        # self.debug_url = "http://"+"127.0.0.1:8000"+"/dev/"+str(self.dev_id)
        # self.debug_report_url = self.debug_url + "/report"
        # debug **

        lock = Lock()
        self.servo_x = servo(config, 0, self.blaster, lock,
                             self.des_queue_x, self.cur_queue_x)
        self.servo_y = servo(config, 1, self.blaster, lock,
                             self.des_queue_y, self.cur_queue_y)

        self.step = int(config.get("servoConfig", "step"))

        self.process = Process(target=self.signal_channel, args=())
        self.process.start()

    def signal_channel(self):
        headers = {'Content-Type': 'application/json'}

        servo_positions = [0, 0]
        report_url = self.url + "/report"
        ssh_pipe = None

        while True:
            try:
                reply = requests.get(self.url + "/status", timeout=5)
                reply = reply.json()

                logging.debug(reply)

            except Exception, e:
                logging.error(str(e))
                sleep(5)
                continue

            if not isinstance(reply, dict) or len(reply) != 3:
                continue

            if 'reset' == reply["mode"]:
                self.des_queue_x.put(0)  # reset servo_x
                self.des_queue_y.put(0)  # reset servo_y
                kill_pids_of_port(self.server_ip, 22)
                del ssh_pipe
                ssh_pipe = None

            if 'management' == reply["mode"]:  # management mode
                # TODO: Shutdown all the operational video
                sleep(self.mgmt_sleep)
                options = reply["options"]
                if (not isinstance(options, dict)):
                    continue

                response = {}
                if ("type" in options and options["type"] == "servo"):
                    servo_turn_mode = 0
                    servo_inc_xy = 0
                    pos_x = 0
                    pos_y = 0

                    try:
                        servo_turn_mode = int(options["servo_turn_mode"])
                        servo_inc_xy = int(options["servo_inc_xy"])
                        pos_x = int(options["pos_x"])
                        pos_y = int(options["pos_y"])

                        if (not servo_turn_mode):
                            if (not servo_inc_xy):
                                self.des_queue_x.put(servo_positions[0] +
                                                     self.step)
                            else:
                                self.des_queue_x.put(servo_positions[1] +
                                                     self.step)
                        else:
                            self.des_queue_x.put(pos_x)
                            self.des_queue_y.put(pos_y)

                        if (not self.cur_queue_x.empty()):
                            servo_positions[0] = self.cur_queue_x.get()
                        if (not self.cur_queue_y.empty()):
                            servo_positions[1] = self.cur_queue_y.get()

                        if (servo_positions[0] == pos_x and
                           servo_positions[1] == pos_y):
                            response["servo"] = True
                            response["pos_x"] = servo_positions[0]
                            response["pos_y"] = servo_positions[1]
                        else:
                            response["servo"] = False

                    except Exception, e:
                        logging.error(str(e))
                        logging.warning("invalid servo input")

                if ("type" in options and options["type"] == "picture"):
                    filename = "dev_" + str(self.dev_id) + ".jpg"
                    os.popen("rm " + filename)
                    os.popen("raspistill -t 10 -o " + filename + " &")
                    sleep(1)  # wait for picture to take

                    try:
                        open(filename)
                    except IOError:
                        logging.error("cannot open")
                        response["picture"] = False
                    else:
                        # TODO check conn
                        try:
                            resp = requests.post(self.url + "/picture",
                                                 files={"file": open(filename,
                                                                     'rb')},
                                                 timeout=5)

                            if (resp.ok):
                                response["picture"] = True
                            else:
                                response["picture"] = False
                        except Exception, e:
                            logging.error(str(e))

                if ("type" in options and options["type"] == "ssh"):
                    if ("op" in options and options["op"] == "start"):
                        logging.warning("ssh started")
                        if ssh_pipe is None:
                            ssh_pipe = Popen(["ssh", "-R",
                                             str(10000+self.dev_id) +
                                              ":localhost:22",
                                              "dev@"+self.server_ip,
                                              "-o StrictHostKeyChecking=no",
                                              "-N", "&"])
                            #                  "-o StrictHostKeyChecking=no",
                            #                  "&"],
                            #                 stdout=PIPE,
                            #                 stderr=PIPE)
                            response["tunnel_opened"] = True
                    if ("op" in options and options["op"] == "stop"):
                        logging.warning("ssh stopped")
                        kill_pids_of_port(self.server_ip, 22)
                        del ssh_pipe
                        ssh_pipe = None
                        response["tunnel_opened"] = False

                    if ("op" in options and options["op"] == "restart"):
                        kill_pids_of_port(self.server_ip, 22)
                        sleep(1)
                        del ssh_pipe
                        ssh_pipe = Popen(["ssh", "-R",
                                          str(10000+self.dev_id) +
                                          ":localhost:22",
                                          "dev@"+self.server_ip,
                                          "-o StrictHostKeyChecking=no",
                                          "-N", "&"])
                        response["tunnel_opened"] = True
                # TODO update script
                # if ('update' in ans and ans['update']):
                #    pass
                # elif ('commit' in ans and ans['commit']):
                #    pass

                # Response completion of jobs
                # TODO check conn

                try:
                    resp = requests.post(report_url,
                                         data=json.dumps(response),
                                         headers=headers,
                                         timeout=5)
                except Exception, e:
                    logging.error(str(e))

            if (reply["mode"] == "operation"):  # tested
                sleep(self.op_sleep)

    def distroy_channel(self):
        self.process.terminate()
        self.servo_x.disable_servo()
        self.servo_y.disable_servo()

if __name__ == "__main__":
    ss = signaling("/opt/wikkit/signal/config.ini")
    signal.pause()
    ss.distroy_channel()
