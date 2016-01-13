from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
import ConfigParser
import os
from process_mgmt import kill_pids_of_port
from lib.request.cam_request_handler import cam_req_handler
from lib.request.tk1_request_handler import tk1_req_handler

"""
Code by bovenyan
"""

APP_VERSION = "1.1-beta"
app = Flask(__name__)
cam_db = cam_dbi.db_api("./config.ini")
tk1_db = tk1_dbi.db_api("./config.ini")

config = ConfigParser.ConfigParser()
config.read("./config.ini")
manage_timeout = int(config.get('opconfig', 'manageTO'))
ssh_timeout = int(config.get('opconfig', 'sshTO'))
file_dir = "./"
notify_reset = False

device_class = {}
device_class["piCam"] = cam_req_handler("./config.ini")
device_class["tk1"] = tk1_req_handler("./config.ini")


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
    if (dev_type in device_class):
        reply = device_class[dev_type].reply_device_status(dev_id)
        return jsonify(reply)
    else:
        abort(400)  # invalid type


@app.route("/dev/<dev_type>/<int:dev_id>/report", methods=['POST'])
def dev_report_done(dev_type, dev_id):
    content = request.json
    if not (dev_type in device_class):
        abort(400)

    if not content:
        return jsonify({})

    if isinstance(content, dict):
        device_class[dev_type].handle_dev_report(dev_id, content)

    return jsonify({"success": True})


# User API
@app.route("/usr/version", methods=['GET'])
def usr_check_version():
    return jsonify({"version": APP_VERSION})

@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['GET'])  # tested
def usr_check_mgmt(dev_type, dev_id):
    if dev_type in device_class:
        return jsonify({"is_mgmt":
                        device_class[dev_type].handle_usr_check_mode(dev_id)})
    else:
        abort(400)

@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['POST'])  # tested
def usr_enable_mgmt(dev_type, dev_id):
    content = request.json

    if (isinstance(content, bool) and dev_type in device_class):
        reply = device_class[dev_type].handle_usr_enable_mgmt(dev_id, content)
        return jsonify(reply)
    else:
        abort(400)

@app.route("/usr/<dev_type>/<int:dev_id>/renew/<int:time>", methods=["POST"])
def usr_renew_mgmt(dev_type, dev_id, time):
    if dev_type in device_class:
        reply = device_class[dev_type].handle_usr_mgmt_renew(dev_id, time)
        return jsonify(reply)
    else:
        abort(400)

@app.route("/usr/<dev_type>/<int:dev_id>/servo", methods=['POST'])
def usr_move_servo(dev_id):
    content = request.json

    if (dev_type != "piCam" or not isinstance(content, dict)):
        abort(400)
    else:
        reply = device_class["piCam"].handle_usr_turn_servo(dev_id, content)
        return jsonify(reply)


@app.route("/usr/<dev_type>/<int:dev_id>/picture/<op>", methods=['POST'])
def usr_take_picture(dev_id, op):
    if dev_type != "piCam":
        abort(400)
    else:
        reply = device_class["piCam"].handle_usr_take_picture(dev_id, op)
        return jsonify(reply)


@app.route("/usr/<dev_type>/<int:dev_id>/ssh/<op>", methods=['POST'])   # tested
def usr_control_ssh(dev_type, dev_id, op):
    if dev_type in device_class:
        content = request.json
        reply = device_class[dev_type].handle_usr_cntl_ssh(dev_id, op, content)

        return jsonify(reply)
    else:
        abort(400)

@app.route("/usr/<dev_type>/<int:dev_id>/reset", methods=['POST'])
def usr_reset(dev_id):
    if dev_type in device_class:
        reply = device_class[dev_type].handle_usr_reset(dev_id)
        return jsonify(reply)
    else:
        abort(400)

if __name__ == '__main__':
    """ Main
    """
    app.run(debug=True, host='0.0.0.0')
