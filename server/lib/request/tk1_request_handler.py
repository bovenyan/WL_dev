from lib.request.wikkit_request_handler import req_handler
from lib.db.tk1_device_db import tk1_device_db


class tk1_req_handler(req_handler):
    def __init__(self, conf_path):
        super(tk1_req_handler, self).__init__(conf_path, "tk1")
        self.dbi = tk1_device_db(conf_path)

    def reply_device_status(self, dev_id):
        reply = super(tk1_req_handler, self).reply_device_status(dev_id)

        if bool(reply):
            return reply

        self.dbi.device_reset_usr(dev_id)
