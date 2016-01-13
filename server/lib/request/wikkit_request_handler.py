# import lib.db.wikkit_device_db
from flask import abort
from lib.db.wikkit_device_db import db_api
from datetime import datetime, timedelta
import ConfigParser
from lib.request.process_mgmt import kill_pids_of_port


class req_handler(object):
    def __init__(self, conf_path, dev_type):
        self.config = ConfigParser.ConfigParser()
        self.config.read(conf_path)

        self.dbi = db_api(self.config, dev_type)
        self.manage_timeout = None
        self.operate_sleep = int(self.config.get('opconfig', 'operateSL'))
        self.maxSshRenew = int(self.config.get('opconfig', 'maxSshRenew'))
        self.ssh_timeout = None
        self.reset_timeout()

        self.manage_flags = 0
        self.op_codes = 0

    def reset_timeout(self):
        self.manage_timeout = int(self.config.get('opconfig', 'manageTO'))
        self.ssh_timeout = int(self.config.get('opconfig', 'sshTO'))

    def reply_device_status(self, dev_id):
        """ Note, this is an abstract func, never use without reload...
        """
        record = self.dbi.device_get_mode(dev_id)

        if not (record is isinstance(dict)) or not bool(dict):
            abort(400)

        reply = {"mode": "operation", "options": {}, "reason": None}

        last_updated = record["last_updated"]
        self.manage_flags = record["manage_flags"]

        # RESET MODE OR FLOP TO RESET
        # Timeout mechanism: mgmt timeout => ssh timeout
        if (((self.manage_flags >> 4) % 2 != 0) or
            (datetime.now() - last_updated > timedelta(0, self.manage_timeout,
                                                       0))):
            self.dbi.device_reset_mgmt(dev_id)
            self.dbi.device_reset_op(dev_id)
            reply["mode"] = "reset"

            self.reset_timeout()
            return reply

        # ------------- Operational mode -----------------
        if (self.manage_flags % 2 == 0):  # operation
            reply["mode"] = "operation"
            self.dpi.device_reset_usr(dev_id)
            return reply

        # ------------- MANAGEMENT MODE ------------------
        reply["mode"] = "management"

        # management timeout
        if (datetime.now() - last_updated > timedelta(0,
                                                      self.manage_timeout,
                                                      0)):
            self.dbi.device_reset_mgmt(dev_id)
            self.dbi.device_reset_op(dev_id)
            reply["mode"] = "operation"
            return reply

        # no user_bz or result not ready
        if ((self.manage_flags >> 2) % 2 == 0 or
           (self.manage_flags >> 3) % 2 != 0):
            return reply  # do nothing , keep managing

        # management options
        self.op_codes = record["op_codes"]

        # ssh enable
        ssh_enable = bool((self.op_codes >> 5) % 2)
        ssh_disable = bool((self.op_codes >> 6) % 2)

        if (ssh_enable and not ssh_disable):
            reply["options"]["type"] = "ssh"
            reply["options"]["op"] = "start"
            self.dbi.device_reset_usr(dev_id)  # reset for next immediately
            return reply

        if (ssh_enable and ssh_disable):
            reply["options"]["type"] = "ssh"
            self.dbi.device_reset_usr(dev_id)  # reset for next immediately
            self.ssh_timeout = int(self.config.get('opconfig', 'sshTO'))
            reply["options"]["op"] = "restart"
            return reply

        if (ssh_disable and not ssh_enable):
            reply["options"]["type"] = "ssh"
            self.dbi.device_reset_usr(dev_id)  # reset for next immediately
            reply["options"]["op"] = "stop"
            self.ssh_timeout = int(self.config.get('opconfig', 'sshTO'))
            return reply

        """
        Insert other mgmt operation when reloading
        """

        """
        reset user buzy for unknown request when reloading
        self.dbi.device_reset_usr(dev_id)
        """

    def handle_dev_report(self, dev_id, content):
        if ("ssh" in content and content["ssh"]):
            self.dbi.device_reset_usr(dev_id)

    def handle_usr_check_mode(self, dev_id):
        return self.dbi.usr_check_dev_mgmt(dev_id)

    def handle_usr_enable_mgmt(self, dev_id, content):
        if bool(content):
            result = self.dbi.usr_enable_mgmt(dev_id)

            if not result[1]:   # meed wait
                wait = timedelta(0, self.operate_timeout, 0) - \
                       (datetime.now() - self.dbi.get_lastseen(dev_id))
                wait = wait.seconds

                return {"success": True, "wait": wait}
            else:   # already set
                return {"success": result[0]}
        else:
            return {"success": self.dbi.disable_mgmt(dev_id)}

    def handle_usr_mgmt_renew(self, dev_id, time):
        if self.handle_usr_check_mode(dev_id):
            if time <= 0 or time > 30*60:
                return {"success": False, "is_mgmt": True}
            else:
                self.manage_timeout = max(time, self.manage_timeout)
                self.dbi.update_activity(dev_id)
                return {"success": True, "is_mgmt": True}

        return {"success": False, "is_mgmt": False}

    def handle_usr_reset(self, dev_id):
        self.dbi.usr_reset(dev_id)
        return {"success": True}

    def handle_usr_cntl_ssh(self, dev_id, op, content):
        if self.handle_usr_check_mode(dev_id):
            if op == "start":
                return {"success": self.dbi.usr_ssh_enable(dev_id),
                        "port": 10000 + dev_id}

            if op == "stop":
                return {"success": self.dbi.usr_ssh_disable(dev_id)}

            if op == "zombie":
                kill_pids_of_port(10000+dev_id)
                return {"success": True}

            if op == "restart":
                return {"success": self.dbi.usr_ssh_restart(dev_id),
                        "port": 10000 + dev_id}

            if op == "renew":
                if isinstance(content, int):
                    if content <= 0 and content > self.maxSshRenew:
                        return {"success": False}
                    else:
                        self.dbi.update_activity(dev_id)
                        self.ssh_timeout = max(content, self.ssh_timeout)
                        return {"success": True}
                else:
                    return {"success": False}
        else:
            return {"success": False, "is_mgmt": False}
