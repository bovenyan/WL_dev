from flask import request, jsonify, abort
import ConfigParser
from lib.request.cam_request_handler import cam_req_handler
from lib.request.tk1_request_handler import tk1_req_handler

from wikkit_api import app

"""
Code by bovenyan
"""

APP_VERSION = "1.1-beta"

config = ConfigParser.ConfigParser()
config.read("./config.ini")
manage_timeout = int(config.get('opconfig', 'manageTO'))
ssh_timeout = int(config.get('opconfig', 'sshTO'))
file_dir = "./"
notify_reset = False

device_class = {}
config = ConfigParser.ConfigParser()
config.read("./config.ini")
device_class["piCam"] = cam_req_handler(config)
device_class["tk1"] = tk1_req_handler(config)


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
        print "CHECK: " + str(reply)
        return jsonify(reply)
    else:
        abort(400)  # invalid type


@app.route("/dev/<dev_type>/<int:dev_id>/report", methods=['POST'])
def dev_report_done(dev_type, dev_id):
    content = request.json
    print "REPORT: " + str(content)
    if not (dev_type in device_class):
        abort(400)

    if not content:
        return jsonify({})

    if isinstance(content, dict):
        device_class[dev_type].handle_dev_report(dev_id, content)

    return jsonify({"success": True})


# User API
@app.route("/usr/version", methods=['GET'])   # 1.1 OK
def usr_check_version():
    """negotiate version
    """
    return jsonify({"version": APP_VERSION})


@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['GET'])  # 1.1 OK
def usr_check_mgmt(dev_type, dev_id):
    """check the (actual) mode of the device
    """
    if dev_type in device_class:
        return jsonify({"is_mgmt":
                        device_class[dev_type].handle_usr_check_mode(dev_id)})
    else:
        abort(400)


@app.route("/usr/<dev_type>/<int:dev_id>/mode", methods=['POST'])  # 1.1 OK
def usr_enable_mgmt(dev_type, dev_id):
    """enable/diable management
    """
    content = request.json

    if (isinstance(content, bool) and dev_type in device_class):
        reply = device_class[dev_type].handle_usr_enable_mgmt(dev_id, content)
        return jsonify(reply)
    else:
        abort(400)


@app.route("/usr/<dev_type>/<int:dev_id>/renew/<int:time>", methods=["POST"])
def usr_renew_mgmt(dev_type, dev_id, time):
    """renew the time for management
    """
    if dev_type in device_class:
        reply = device_class[dev_type].handle_usr_mgmt_renew(dev_id, time)
        return jsonify(reply)
    else:
        abort(400)


@app.route("/usr/<dev_type>/<int:dev_id>/servo", methods=['POST'])  # 1.1 OK
def usr_move_servo(dev_type, dev_id):
    """control servo position
    """
    content = request.json

    if (dev_type != "piCam" or not isinstance(content, dict)):
        abort(400)
    else:
        reply = device_class["piCam"].handle_usr_turn_servo(dev_id, content)
        return jsonify(reply)


@app.route("/usr/<dev_type>/<int:dev_id>/picture/<op>", methods=['POST'])
def usr_take_picture(dev_type, dev_id, op):     # 1.1 OK
    """control camera
    """
    if dev_type != "piCam":
        abort(400)
    else:
        reply = device_class["piCam"].handle_usr_take_picture(dev_id, op)
        return jsonify(reply)


@app.route("/usr/<dev_type>/<int:dev_id>/ssh/<op>", methods=['POST'])   # 1.1 OK
def usr_control_ssh(dev_type, dev_id, op):
    """ Handle ssh operation
    """
    if dev_type in device_class:
        content = request.json
        reply = device_class[dev_type].handle_usr_cntl_ssh(dev_id, op, content)

        return jsonify(reply)
    else:
        abort(400)


@app.route("/usr/<dev_type>/<int:dev_id>/reset", methods=['POST'])  # 1.1 OK
def usr_reset(dev_type, dev_id):
    """ Reset the device
    """
    if dev_type in device_class:
        reply = device_class[dev_type].handle_usr_reset(dev_id)
        return jsonify(reply)
    else:
        abort(400)

