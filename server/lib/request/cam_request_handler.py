from lib.request.wikkit_request_handler import req_handler
from lib.db.cam_device_db import cam_db_api


class cam_req_handler(req_handler):
    def __init__(self, config):
        super(cam_req_handler, self).__init__(config, "piCam")
        self.dbi = cam_db_api(config)

    def reply_device_status(self, dev_id):
        reply = super(cam_req_handler, self).reply_device_status(dev_id)

        if not (reply is None):
            return reply

        reply = {"mode": "management", "options": {}, "reason": None}
        # exam servo turn
        servo_active = bool(self.op_codes % 2)
        if (servo_active):
            reply["options"]["type"] = "servo"
            reply["options"]["servo_turn_mode"] = bool((self.op_codes >> 1) % 2)
            reply["options"]["servo_inc_xy"] = int((self.op_codes >> 2) % 4)
            reply["options"]["pos_x"] = int(self.record["pos_x"])
            reply["options"]["pos_y"] = int(self.record["pos_y"])
            reply["options"]["save_config"] = int((self.op_codes >> 7) % 2)

            self.dbi.device_reset_usr(dev_id)  # reset for next immediately

            return reply

        # picture taking
        picture = bool((self.op_codes >> 4) % 2)   # tested
        if (picture):
            reply["options"]["type"] = "picture"
            self.dbi.device_reset_usr(dev_id)  # reset for next immediately
            return reply

        # unknown
        self.dbi.device_reset_usr(dev_id)
        return reply

    def handle_dev_report(self, dev_id, content):
        super(cam_req_handler, self).handle_dev_report(dev_id, content)

        if ("servo" in content and content["servo"]):  # servo
            pos_x = int(content["pos_x"])
            pos_y = int(content["pos_y"])
            self.dbi.device_update_pos(dev_id, pos_x, pos_y)
            self.dbi.device_reset_usr(dev_id)

        if ("picture" in content and content["picture"]):  # picture
            self.dbi.device_reset_usr(dev_id)

    def handle_usr_turn_servo(self, dev_id, content):
        if self.handle_usr_check_mode(dev_id):
            if ('inc_dec' in content and 'xy' in content):
                self.dbi.usr_servo_inc(dev_id, content['inc_dec'],
                                       content['xy'])
                return {"success": True, "is_mgmt": True}

            if ('pos_x' in content and 'pos_y' in content):
                self.dbi.usr_servo_pos(dev_id,
                                       content['pos_x'],
                                       content['pos_y'])
                return {"success": True, "is_mgmt": True}

            if ('save_pos' in content):
                self.dbi.usr_servo_sav(dev_id)
                return {"success": True, "is_ngnt": True}

            return {"success": False, "is_mgmt": True}
        else:
            return {"success": False, "is_mgmt": False}

    def handle_usr_take_picture(self, dev_id, op):
        if self.handle_usr_check_mode(dev_id):
            if op == "shot":
                return {"success": self.dbi.usr_take_pic(dev_id),
                        "is_mgmt": True}

            return {"success": False, "is_mgmt": True}

        return {"success": False, "is_mgmt": False}

"""
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif'])

@app.route("/dev/<dev_type>/<int:dev_id>/picture", methods=['POST'])
def dev_post_picture(dev_type, dev_id):
    if 'file' not in request.files:
        abort(400)
    file = request.files['file']
    if file and allowed_file(file.filename):
        file.save(os.path.join(file_dir, 'dev_' + str(dev_id) + '.jpg'))
        return jsonify({"success": True})

    return jsonify({"success": False})

"""
