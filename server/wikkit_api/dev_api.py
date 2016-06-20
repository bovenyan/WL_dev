from flask import request, jsonify, abort
from datetime import datetime, timedelta
import ConfigParser
import os
from lib.process_mgmt import kill_pids_of_port
from wikkit_api import app


APP_VERSION = "1.0"

config = ConfigParser.ConfigParser()
config.read("./config.ini")
manage_timeout = int(config.get('opconfig', 'manageTO'))
ssh_timeout = int(config.get('opconfig', 'sshTO'))
file_dir = "./"
notify_reset = False


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
    global ssh_timeout
    global manage_timeout
    global dev_ip_map

    record = db_api.device_get_rec(devId)

    if record is None:
        abort(400)

    reply = {"mode": "operation", "options": {}, "reason": None}
    # [mode, options, reason]

    last_updated = record[0]
    manage_flags = int(record[1])

    # TODO record device ip
    # if request.headers.getlist("X-Forwarded-For"):
    #     dev_ip_map[devId] = request.headers.getlist("X-Forwarded-For")[0]
    # else:
    #     dev_ip_map[devId] = request.remote_addr

    # RESET MODE OR FLOP TO RESET
    if ((manage_flags >> 4) % 2 != 0):  # reset
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "reset"
        manage_timeout = int(config.get('opconfig', 'manageTO'))
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)

    if (datetime.now() - last_updated > timedelta(0, ssh_timeout,  # ssh timeout
                                                  0)):
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "reset"
        manage_timeout = int(config.get('opconfig', 'manageTO'))
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)   # reset ssh

    # OPERATIONAL MODE
    if (manage_flags % 2 == 0):  # operation
        reply["mode"] = "operation"
        db_api.device_reset_user(devId)
        return jsonify(reply)

    # MANAGEMENT MODE
    reply["mode"] = "management"
    # management timeout
    if (datetime.now() - last_updated > timedelta(0, manage_timeout,
                                                  0)):
        db_api.device_reset_mgmt(devId)
        db_api.device_reset_op(devId)
        reply["mode"] = "operation"
        return jsonify(reply)   # flop to operation

    # no user_bz or result not ready
    if ((manage_flags >> 2) % 2 == 0 or (manage_flags >> 3) % 2 != 0):
        return jsonify(reply)  # do nothing , keep managing

    # management options
    op_codes = int(record[4])

    # exam servo turning
    servo_active = bool(op_codes % 2)
    if (servo_active):
        reply["options"]["type"] = "servo"
        reply["options"]["servo_turn_mode"] = bool((op_codes >> 1) % 2)
        reply["options"]["servo_inc_xy"] = int((op_codes >> 2) % 4)
        reply["options"]["pos_x"] = int(record[2])
        reply["options"]["pos_y"] = int(record[3])
        print "reply: " + str(reply)
        db_api.device_reset_user(devId)  # reset for next immediately
        return jsonify(reply)

    # picture taking
    picture = bool((op_codes >> 4) % 2)   # tested
    if (picture):
        reply["options"]["type"] = "picture"
        db_api.device_reset_user(devId)  # reset for next immediately
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
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        reply["options"]["op"] = "restart"
        return jsonify(reply)

    if (ssh_disable and not ssh_enable):
        # kill_pids_of_port(10000+devId)
        reply["options"]["type"] = "ssh"
        db_api.device_reset_user(devId)  # reset for next immediately
        reply["options"]["op"] = "stop"
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)

    # TODO script updating
    # update = bool((op_codes >> 6) % 2)
    # commit = False
    # if (not update):  # update and commit cannot happen together
        # commit = bool((op_codes >> 7) % 2)
    #    pass

    # enable management
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
@app.route("/usr/version", methods=['GET'])
def usr_check_version():
    return jsonify({"version": APP_VERSION})


@app.route("/usr/<int:devId>/mode", methods=['GET'])  # tested
def usr_check_mgmt(devId):
    return jsonify({"is_mgmt": db_api.user_check_dev_mgmt(devId)})


@app.route("/usr/<int:devId>/mode", methods=['POST'])  # tested
def usr_enable_mgmt(devId):
    content = request.json
    if (isinstance(content, bool)):
        if (bool(content)):
            result = db_api.usr_enable_mgmt(devId)

            if (not result[1]):  # need wait
                wait = timedelta(0, 120, 0) - (datetime.now() -
                                               db_api.get_lastseen(devId))
                wait = wait.seconds

                return jsonify({"success": True,
                                "wait": wait})
            else:  # already set
                return jsonify({"success": result[0]})
        else:
            return jsonify({"success": db_api.disable_mgmt(devId)})

    return jsonify({"success": False})


@app.route("/usr/<int:devId>/renew/<int:time>", methods=["POST"])
def usr_renew_mgmt(devId, time):
    if (db_api.user_check_dev_mgmt(devId)):
        global manage_timeout
        if (time > 30*60):
            return jsonify({"success": False, "is_mgmt": True})
        else:
            manage_timeout = max(time, manage_timeout)
            db_api.update_activity(devId)
            return jsonify({"success": True, "is_mgmt": True})

    return jsonify({"success": False, "is_mgmt": False})


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
        return jsonify({"success": False, "is_mgmt": True})

    return jsonify({"success": False, "is_mgmt": False})

"""
cam-1 shot -> cam-1 fetch code -> cam-1 fetch file
"""


@app.route("/usr/<int:devId>/picture/<op>", methods=['POST'])
def usr_take_picture(devId, op):
    if (db_api.user_check_dev_mgmt(devId)):
        if (op == 'shot'):
            return jsonify({"success":
                            db_api.user_take_pic(devId),
                            "is_mgmt": True})
        return jsonify({"success": False, "is_mgmt": True})
        """
        if (op == 'query'):
            if (db_api.user_check_dev_fetch(devId)):
                return jsonify({"success": True,
                                "file": str(devId),
                                "is_mgmt": True})
            return jsonify({"success": False,
                            "is_mgmt": True})

        if (op == 'get'):
            content = request.json
            if (isinstance(content, dict) and "file" in content):
                return send_from_directory(file_dir,
                                           "dev_" + str(devId) + '.jpg')
            return jsonify({"success": False,
                            "is_mgmt": True})
        """

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<int:devId>/ssh/<op>", methods=['POST'])   # tested
def usr_control_ssh(devId, op):
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

        if (op == "renew"):
            content = request.json

            if (isinstance(content, int)):
                if content > 90*60:
                    return jsonify({"success": False})
                else:
                    global ssh_timeout
                    db_api.update_activity(devId)
                    ssh_timeout = max(content, ssh_timeout)
                    return jsonify({"success": True})
            else:
                return jsonify({"success": False})

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<int:devId>/reset", methods=['POST'])
def usr_reset(devId):
    db_api.user_reset(devId)
    # TODO close device ssh id
    return jsonify({"success": True})
