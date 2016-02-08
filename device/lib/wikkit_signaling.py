from subprocess import Popen
from time import sleep
import requests
from process_mgmt import kill_pids_of_port
import json
import logging

logging.basicConfig(filename='signaling.log', level=logging.DEBUG)


class wikkit_signaling(object):
    def __init__(self, config, config_file_name):
        self.config = config
        self.config_file_name = config_file_name

        self.dev_id = int(config.get("signalConfig", "devID"))
        self.mgmt_sleep = int(config.get("signalConfig", "mgmtSleep"))
        self.op_sleep = int(config.get("signalConfig", "opSleep"))
        self.server_ip = config.get("signalConfig", "serverIP")
        self.dev_type = config.get("signalConfig", "devType")

        server_port = str(int(config.get("signalConfig", "serverPort")))

        rest_addr = self.server_ip + ":" + server_port
        self.url = "http://" + rest_addr + "/dev/" + \
            self.dev_type + "/" + str(self.dev_id)

        self.ssh_pipe = None

    def reload_config(self):
        self.mgmt_sleep = int(self.config.get("signalConfig", "mgmtSleep"))
        self.op_sleep = int(self.config.get("signalConfig", "opSleep"))

    def save_config(self):
        self.config.set("signalConfig", "mgmtSleep", self.mgmg_sleep)
        self.config.set("signalConfig", "opSleep", self.op_sleep)
        with open(self.config_file_name, 'w') as config_file:
            self.config.write(config_file)

    def _handle_reset(self):
        kill_pids_of_port(self.server_ip, 22)
        del self.ssh_pipe
        self.ssh_pipe = None

    def _handle_mgmt(self, reply, options):
        response = {}

        if ("type" in options and options["type"] == "ssh"):
            if ("op" in options and options["op"] == "start"):
                logging.warning("ssh started")
                if self.ssh_pipe is None:
                    self.ssh_pipe = Popen(["ssh", "-R",
                                           str(10000+self.dev_id) +
                                           ":localhost:22",
                                           "dev@"+self.server_ip,
                                           "-o StrictHostKeyChecking=no",
                                           "-N", "&"])
                    response["tunnel_opened"] = True

            if ("op" in options and options["op"] == "stop"):
                logging.warning("ssh stopped")
                kill_pids_of_port(self.server_ip, 22)
                del self.ssh_pipe
                self.ssh_pipe = None
                response["tunnel_opened"] = False

            if ("op" in options and options["op"] == "restart"):
                kill_pids_of_port(self.server_ip, 22)
                sleep(1)
                del self.ssh_pipe
                self.ssh_pipe = Popen(["ssh", "-R",
                                       str(10000+self.dev_id) +
                                       ":localhost:22",
                                       "dev@"+self.server_ip,
                                       "-o StrictHostKeyChecking=no",
                                       "-N", "&"])
                response["tunnel_opened"] = True

        return response

    def _handle_oper(self, reply):
        sleep(self.op_sleep)

    def run(self):
        headers = {'Content-Type': 'application/json'}
        report_url = self.url + "/report"

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
                self._handle_reset()

            if 'management' == reply["mode"]:
                sleep(self.mgmt_sleep)
                options = reply["options"]

                if (not isinstance(options, dict)):
                    continue

                response = self._handle_mgmt(reply, options)

                try:
                    requests.post(report_url,
                                  data=json.dumps(response),
                                  headers=headers,
                                  timeout=5)
                except Exception, e:
                    logging.error(str(e))

            if 'operation' == reply["mode"]:
                self._handle_oper(reply)
