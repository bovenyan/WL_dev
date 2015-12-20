from flask import Flask, request, jsonify, abort, send_from_directory
from datetime import datetime, timedelta
import db_conn as db
import ConfigParser
import os
from process_mgmt import kill_pids_of_port

"""
Code by bovenyan
"""

app = Flask(__name__)
db_api = db.db_api("./config.ini")

config = ConfigParser.ConfigParser()
config.read("./config.ini")
manage_timeout = int(config.get('opconfig', 'manageTO'))
ssh_timeout = int(config.get('opconfig', 'sshTO'))
file_dir = "./"


@app.route("/")
def index():
    """ GET Index
        Showing that the application is ready
    """
    # return jsonify(msg="It's Working! Go ahead!")
    return "<h1 style='color:blue'>Wikkit dev platform working!</h1>"


# DEVICE API
@app.route("/dev/<int:devId>/status", methods=['GET'])
def dev_check_status(devId):
    record = db_api.device_get_rec(devId)

    if record is None:
        abort(400)

    reply = {"mode": "operation", "options": {}, "reason": None}
    # [mode, options, reason]

    last_updated = record[0]
    manage_flags = int(record[1])


    if ((manage_flags >> 4) % 2 != 0):  # tested
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "reset"
        return jsonify(reply)

    if (manage_flags % 2 == 0):  # tested
        reply["mode"] = "operation"
        return jsonify(reply)

    # handle management timeout
    reply["mode"] = "management"
    if (datetime.now() - last_updated > timedelta(0, ssh_timeout,  # tested
                                                  0)):
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "reset"
        # kill_pids_of_port(10000+devId)
        return jsonify(reply)   # reset ssh

    if (datetime.now() - last_updated > timedelta(0, manage_timeout,  # tested
                                                  0)):
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "operation"
        return jsonify(reply)   # flop to operation

    # no apply or result not ready
    if ((manage_flags >> 2) % 2 == 0 or (manage_flags >> 3) % 2 != 0):  # tested
        return jsonify(reply)  # do nothing , keep managing

    # management options
    op_codes = int(record[4])

    # exam servo turning
    servo_active = bool(op_codes % 2)
    if (servo_active):
        reply["options"]["type"] = "servo"
        reply["options"]["servo_turn_mode"] = bool((op_codes >> 1) % 2)
        reply["options"]["servo_inc_xy"] = int((op_codes >> 2) % 4)
        reply["options"]["pos_x"] = int(record[3])
        reply["options"]["pos_y"] = int(record[4])
        db_api.device_reset_user(devId)  # reset for next immediately
        return jsonify(reply)

    # picture taking
    picture = bool((op_codes >> 4) % 2)   # tested
    if (picture):
        reply["options"]["type"] = "picture"
        db_api.device_set_busy(devId)
        return jsonify(reply)

    # ssh enable
    ssh_enable = bool((op_codes >> 5) % 2)   # tested
    ssh_disable = bool((op_codes >> 6) % 2)   # tested
    if (ssh_enable and not ssh_disable):
        reply["options"]["type"] = "ssh"
        reply["options"]["op"] = "start"
        db_api.device_reset_user(devId)  # reset for next immediately
        return jsonify(reply)
    if (ssh_enable and ssh_disable):
        # kill_pids_of_port(10000+devId)
        reply["options"]["type"] = "ssh"
        db_api.device_reset_user(devId)  # reset for next immediately
        reply["options"]["op"] = "restart"
        return jsonify(reply)
    if (ssh_disable and not ssh_enable):
        # kill_pids_of_port(10000+devId)
        reply["options"]["type"] = "ssh"
        db_api.device_reset_user(devId)  # reset for next immediately
        reply["options"]["op"] = "stop"
        return jsonify(reply)

    # TODO script updating
    # update = bool((op_codes >> 6) % 2)
    # commit = False
    # if (not update):  # update and commit cannot happen together
        # commit = bool((op_codes >> 7) % 2)
    #    pass

    # operation not recognized
    db_api.device_reset_user(devId)
    return jsonify(reply)


@app.route("/dev/<int:devId>/report", methods=['POST'])
def dev_report_done(devId):
    content = request.json
    if not content:
        return jsonify({})

    if isinstance(content, dict):
        if ("servo" in content and content["servo"]):  # servo
            pos_x = int(content["pos_x"])
            pos_y = int(content["pos_y"])
            db_api.device_update_pos(devId, pos_x, pos_y)
            db_api.device_reset_user(devId)

        if ("picture" in content and content["picture"]):  # picture
            db_api.device_reset_user(devId)

        if ("ssh" in content and content["ssh"]):  # ssh   # tested
            db_api.device_reset_user(devId)

        # if ("update" in content):
        #     pass

        # if ("commit" in content):
        #     pass

    return jsonify({"success": True})


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif'])


@app.route("/dev/<int:devId>/picture", methods=['POST'])
def dev_post_picture(devId):
    if 'file' not in request.files:
        abort(400)
    file = request.files['file']
    if file and allowed_file(file.filename):
        file.save(os.path.join(file_dir, 'dev_' + str(devId) + '.jpg'))
        return jsonify({"success": True})

    return jsonify({"success": False})


# User API
@app.route("/usr/<int:devId>/mode", methods=['POST'])  # tested
def usr_enable_mgmt(devId):
    content = request.json
    if (isinstance(content, bool)):
        if (bool(content)):
            return jsonify({"success": db_api.enable_mgmt(devId)})
        else:
            return jsonify({"success": db_api.disable_mgmt(devId)})

    return jsonify({"success": False})


@app.route("/usr/<int:devId>/servo", methods=['POST'])
def usr_move_servo(devId):
    if (db_api.user_check_dev_mgmt(devId)):
        content = request.json

        if ('inc_dec' in content and 'xy' in content):
            db_api.user_servo_inc(devId,
                                  content['inc_dec'],
                                  content['xy'])
            return jsonify({"success": True})

        if ('pos_x' in content and 'pos_y' in content):  # tested
            db_api.user_servo_pos(devId,
                                  content['pos_x'],
                                  content['pos_y'])
            return jsonify({"success": True})

    return jsonify({"success": False})

"""
cam-1 shot -> cam-1 fetch code -> cam-1 fetch file
"""


@app.route("/usr/<int:devId>/picture/<op>", methods=['POST'])
def usr_take_picture(devId, op):
    if (db_api.user_check_dev_mgmt(devId)):
        if (op == 'shot'):
            return jsonify({"success":
                            db_api.user_take_pic(devId)})

        if (op == 'query'):
            if (db_api.user_check_dev_fetch(devId)):
                return jsonify({"success": True,
                                "file": str(devId)})
            return jsonify({"success": False})

        if (op == 'get'):
            content = request.json
            if (isinstance(content, dict) and "file" in content):
                return send_from_directory(file_dir,
                                           "dev_" + str(devId) + '.jpg')
            return jsonify({"success": False})

        if (op == 'fetched'):
            db_api.enable_mgmt(devId)

    return jsonify({"success": False})


@app.route("/usr/<int:devId>/ssh/<op>", methods=['POST'])   # tested
def usr_enable_ssh(devId, op):
    if (db_api.user_check_dev_mgmt(devId)):
        if (op == "start"):
            return jsonify({"success": db_api.user_ssh_enable(devId),
                            "port": 10000+devId})

        if (op == "stop"):
            return jsonify({"success": db_api.user_ssh_disable(devId)})

        if (op == "zombie"):
            kill_pids_of_port(10000+devId)
            return jsonify({"success": True})

        if (op == "restart"):
            db_api.user_ssh_restart(devId)
            return jsonify({"success": db_api.user_ssh_restart(devId),
                            "port": 10000+devId})


@app.route("/usr/<int:devId>/mode", methods=['POST'])
def usr_set_mode(devId):
    content = request.json
    if (isinstance(content, list)):
        if ('mgmt' in content):
            db_api.user_enable_mgmt(devId)
            return jsonify({"success": True})
        if ('oper' in content):
            db_api.user_disable_mgmt(devId)
            return jsonify({"success": True})

    return jsonify({"success": False})


@app.route("/usr/<int:devId>/reset", methods=['POST'])
def usr_reset(devId):
    db_api.user_reset(devId)
    # TODO close device ssh id
    return jsonify({"success": True})


if __name__ == '__main__':
    """ Main
    """
    app.run(debug=True, host='0.0.0.0')
