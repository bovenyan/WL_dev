from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
import db_conn as db
import ConfigParser
import os
from process_mgmt import kill_pids_of_port

"""
Code by bovenyan
"""

APP_VERSION = "1.0"
app = Flask(__name__)
db_api = db.db_api("./config.ini")

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
@app.route("/dev/<dev_type>/<int:dev_id>/status", methods=['GET'])
def dev_check_status(dev_type, dev_id):
    global ssh_timeout
    global manage_timeout

    record = db_api.device_get_rec(dev_type, dev_id)

    if record is None:
        abort(400)

    reply = {"mode": "operation", "options": {}, "reason": None}
    # [mode, options, reason]

    last_updated = record[0]
    manage_flags = int(record[1])

    # RESET MODE OR FLOP TO RESET
    if ((manage_flags >> 4) % 2 != 0):  # reset
        db_api.device_reset_mgmt(dev_type, dev_id)
        db_api.device_reset_op(dev_type, dev_id)
        reply["mode"] = "reset"
        manage_timeout = int(config.get('opconfig', 'manageTO'))
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)

    if (datetime.now() - last_updated > timedelta(0, ssh_timeout,  # ssh timeout
                                                  0)):
        db_api.device_reset_mgmt(dev_id)
        db_api.device_reset_op(dev_id)
        reply["mode"] = "reset"
        manage_timeout = int(config.get('opconfig', 'manageTO'))
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)   # reset ssh

    # OPERATIONAL MODE
    if (manage_flags % 2 == 0):  # operation
        reply["mode"] = "operation"
        db_api.device_reset_user(dev_id)
        return jsonify(reply)

    # MANAGEMENT MODE
    reply["mode"] = "management"
    # management timeout
    if (datetime.now() - last_updated > timedelta(0, manage_timeout,
                                                  0)):
        db_api.device_reset_mgmt(dev_id)
        db_api.device_reset_op(dev_id)
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
        db_api.device_reset_user(dev_id)  # reset for next immediately
        return jsonify(reply)

    # picture taking
    picture = bool((op_codes >> 4) % 2)   # tested
    if (picture):
        reply["options"]["type"] = "picture"
        db_api.device_reset_user(dev_id)  # reset for next immediately
        return jsonify(reply)

    # ssh enable
    ssh_enable = bool((op_codes >> 5) % 2)   # tested
    ssh_disable = bool((op_codes >> 6) % 2)   # tested
    if (ssh_enable and not ssh_disable):
        reply["options"]["type"] = "ssh"
        reply["options"]["op"] = "start"
        db_api.device_reset_user(dev_id)  # reset for next immediately
        return jsonify(reply)

    if (ssh_enable and ssh_disable):
        # kill_pids_of_port(10000+dev_id)
        reply["options"]["type"] = "ssh"
        db_api.device_reset_user(dev_id)  # reset for next immediately
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        reply["options"]["op"] = "restart"
        return jsonify(reply)

    if (ssh_disable and not ssh_enable):
        # kill_pids_of_port(10000+dev_id)
        reply["options"]["type"] = "ssh"
        db_api.device_reset_user(dev_id)  # reset for next immediately
        reply["options"]["op"] = "stop"
        ssh_timeout = int(config.get('opconfig', 'sshTO'))
        return jsonify(reply)

    db_api.device_reset_user(dev_id)
    return jsonify(reply)


@app.route("/dev/<dev_type>/<int:dev_id>/report", methods=['POST'])
def dev_report_done(dev_type, dev_id):
    content = request.json
    if not content:
        return jsonify({})

    if isinstance(content, dict):
        if ("servo" in content and content["servo"]):  # servo
            pos_x = int(content["pos_x"])
            pos_y = int(content["pos_y"])
            db_api.device_update_pos(dev_id, pos_x, pos_y)
            db_api.device_reset_user(dev_id)

        if ("picture" in content and content["picture"]):  # picture
            db_api.device_reset_user(dev_id)

        if ("ssh" in content and content["ssh"]):  # ssh   # tested
            db_api.device_reset_user(dev_id)

    return jsonify({"success": True})


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


# User API
@app.route("/usr/version", methods=['GET'])
def usr_check_version():
    return jsonify({"version": APP_VERSION})


@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['GET'])  # tested
def usr_check_mgmt(dev_type, dev_id):
    return jsonify({"is_mgmt": db_api.user_check_dev_mgmt(dev_type, dev_id)})


@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['POST'])  # tested
def usr_enable_mgmt(dev_type, dev_id):
    content = request.json
    if (isinstance(content, bool)):
        if (bool(content)):
            result = db_api.usr_enable_mgmt(dev_id)

            if (not result[1]):  # need wait
                wait = timedelta(0, 600, 0) - (datetime.now() -
                                               db_api.get_lastseen(dev_id))
                wait = wait.seconds

                return jsonify({"success": True,
                                "wait": wait})
            else:  # already set
                return jsonify({"success": result[0]})
        else:
            return jsonify({"success": db_api.disable_mgmt(dev_id)})

    return jsonify({"success": False})


@app.route("/usr/<dev_type>/<int:dev_id>/renew/<int:time>", methods=["POST"])
def usr_renew_mgmt(dev_type, dev_id, time):
    if (db_api.user_check_dev_mgmt(dev_type, dev_id)):
        global manage_timeout
        if (time > 30*60):
            return jsonify({"success": False, "is_mgmt": True})
        else:
            manage_timeout = max(time, manage_timeout)
            db_api.update_activity(dev_id)
            return jsonify({"success": True, "is_mgmt": True})

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<dev_type>/<int:dev_id>/servo", methods=['POST'])
def usr_move_servo(dev_id):
    if (db_api.user_check_dev_mgmt(dev_type, dev_id)):
        content = request.json

        if ('inc_dec' in content and 'xy' in content):
            db_api.user_servo_inc(dev_id,
                                  content['inc_dec'],
                                  content['xy'])
            return jsonify({"success": True})

        if ('pos_x' in content and 'pos_y' in content):  # tested
            db_api.user_servo_pos(dev_id,
                                  content['pos_x'],
                                  content['pos_y'])
            return jsonify({"success": True})
        return jsonify({"success": False, "is_mgmt": True})

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<dev_type>/<int:dev_id>/picture/<op>", methods=['POST'])
def usr_take_picture(dev_id, op):
    if (db_api.user_check_dev_mgmt(dev_type, dev_id)):
        if (op == 'shot'):
            return jsonify({"success":
                            db_api.user_take_pic(dev_id),
                            "is_mgmt": True})
        return jsonify({"success": False, "is_mgmt": True})
        """
        if (op == 'query'):
            if (db_api.user_check_dev_fetch(dev_id)):
                return jsonify({"success": True,
                                "file": str(dev_id),
                                "is_mgmt": True})
            return jsonify({"success": False,
                            "is_mgmt": True})

        if (op == 'get'):
            content = request.json
            if (isinstance(content, dict) and "file" in content):
                return send_from_directory(file_dir,
                                           "dev_" + str(dev_id) + '.jpg')
            return jsonify({"success": False,
                            "is_mgmt": True})
        """

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<dev_type>/<int:dev_id>/ssh/<op>", methods=['POST'])   # tested
def usr_control_ssh(dev_type, dev_id, op):
    if (db_api.user_check_dev_mgmt(dev_type, dev_id)):
        if (op == "start"):
            return jsonify({"success": db_api.user_ssh_enable(dev_id),
                            "port": 10000+dev_id})

        if (op == "stop"):
            return jsonify({"success": db_api.user_ssh_disable(dev_id)})

        if (op == "zombie"):
            kill_pids_of_port(10000+dev_id)
            return jsonify({"success": True})

        if (op == "restart"):
            db_api.user_ssh_restart(dev_id)
            return jsonify({"success": db_api.user_ssh_restart(dev_id),
                            "port": 10000+dev_id})

        if (op == "renew"):
            content = request.json

            if (isinstance(content, int)):
                if content > 90*60:
                    return jsonify({"success": False})
                else:
                    global ssh_timeout
                    db_api.update_activity(dev_id)
                    ssh_timeout = max(content, ssh_timeout)
                    return jsonify({"success": True})
            else:
                return jsonify({"success": False})

    return jsonify({"success": False, "is_mgmt": False})


@app.route("/usr/<dev_type>/<int:dev_id>/reset", methods=['POST'])
def usr_reset(dev_id):
    db_api.user_reset(dev_id)
    # TODO close device ssh id
    return jsonify({"success": True})


if __name__ == '__main__':
    """ Main
    """
    app.run(debug=True, host='0.0.0.0')
