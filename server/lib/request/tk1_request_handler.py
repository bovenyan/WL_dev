from lib.request.wikkit_request_handler import req_handler
from lib.db.tk1_device_db import tk1_db_api


class tk1_req_handler(req_handler):
    def __init__(self, config):
        super(tk1_req_handler, self).__init__(config, "tk1")
        self.dbi = tk1_db_api(config)

    def reply_device_status(self, dev_id):
        reply = super(tk1_req_handler, self).reply_device_status(dev_id)

        if not (reply is None):
            return reply

        reply = {"mode": "management", "options": {}, "reason": None}

        # unknown
        self.dbi.device_reset_usr(dev_id)
        return reply
