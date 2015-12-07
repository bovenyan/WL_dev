from flask import Flask, request, jsonify, abort, send_from_directory
from datetime import datetime, timedelta
import db_conn as db
import ConfigParser
import os
from time import sleep

"""
Code by bovenyan
"""

app = Flask(__name__)
db_api = db.db_api("./config.ini")

config = ConfigParser.ConfigParser()
config.read("./config.ini")
manage_keepalive = int(config.get('opconfig', 'manageTO'))
file_dir = "./"


@app.route("/")
def index():
    """ GET Index
        Showing that the application is ready
    """
    # return jsonify(msg="It's Working! Go ahead!")
    return "<h1 style='color:blue'>Wikkit dev platform working!</h1>"


# DEVICE API
@app.route("/dev/<int:devId>", methods=['GET'])
def dev_check_status(devId):
    """ Device Interface
        HowTo use:
             curl -i -H "Content-Type: application/json" \
             -X GET http://localhost:5000/dev/1
    """
    record = db_api.device_get_rec(devId)

    if record is None:
        abort(400)

    last_updated = record[1]
    manage_flags = int(record[2])

    if (manage_flags % 2 == 0):  # operation mode
        db_api.device_reset(devId)
        return jsonify({"manage": False})

    # verify the keep alive for management
    if (datetime.now() - last_updated > timedelta(0, manage_keepalive,
                                                  0)):
        db_api.device_reset(devId)
        return jsonify({"manage": False})

    # no apply or result not fetched
    if ((manage_flags >> 2) % 2 == 0 or (manage_flags >> 3) % 2 != 0):
        return jsonify({"manage": True})  # do nothing , keep managing

    op_codes = record[5]

    # exam servo turning
    servo_active = bool(op_codes % 2)
    servo_turn_mode = bool((op_codes >> 1) % 2)
    servo_inc_xy = int((op_codes >> 2) % 4)
    pos_x = int(record[3])
    pos_y = int(record[4])

    # picture taking
    picture = bool((op_codes >> 4) % 2)
    ssh = bool((op_codes >> 5) % 2)

    # script updating
    update = bool((op_codes >> 6) % 2)
    commit = False
    if (not update):  # update and commit cannot happen together
        commit = bool((op_codes >> 7) % 2)

    return jsonify({"manage": True,
                    "servo_active": servo_active,
                    "servo_turn_mode": servo_turn_mode,
                    "servo_inc_xy": servo_inc_xy,
                    "pos_x": pos_x,
                    "pos_y": pos_y,
                    "picture": picture,
                    "ssh": ssh,
                    "update": update,
                    "commit": commit})


@app.route("/dev/<int:devId>", methods=['POST'])
def dev_report_done(devId):
    """ Device Interface
        HowTo use:
            curl -i -H "Content-Type: application/json" \
            -X POST -d {""} \
            http://localhost:5000/dev/1
    """

    content = request.json
    print content
    if not content:
        return jsonify({})

    to_fetch = False
    to_flop = False

    if "servo_turned" in content:
        pos_x = int(content['pos_x'])
        pos_y = int(content['pos_y'])

        if bool(content["servo_turned"]):
            db_api.device_update_pos(devId, pos_x, pos_y)
            to_flop = True

    if "picture_taken" in content and bool(content["picture_taken"]):
        to_flop = True
        to_fetch = True

    if "video_taken" in content and bool(content["video_taken"]):
        to_flop = True

    if "update_complete" in content and bool(content["update_complete"]):
        to_flop = True

    if "commit_complete" in content and bool(content["commit_complete"]):
        to_flop = True

    if to_flop:
        db_api.device_flop_mgmt(devId, to_fetch)
        db_api.device_reset_op(devId)

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
        file.save(os.path.join(file_dir, 'dev_'+str(devId)+'_test.jpg'))

    return jsonify({"success": True})


@app.route("/usr/servo/<int:devId>", methods=['POST'])
def usr_move_servo(devId):
    content = request.json

    if ('inc_dec' in content and 'xy' in content):
        db_api.user_servo_inc(devId,
                              content['inc_dec'],
                              content['xy'])
        return jsonify({"success": True})

    if ('pos_x' in content and 'pos_y' in content):
        db_api.user_servo_pos(devId,
                              content['pos_x'],
                              content['pos_y'])
        return jsonify({"success": True})

    return jsonify({"success": False})


@app.route("/usr/picture/<int:devId>", methods=['GET'])
def usr_take_picture(devId):
    db_api.user_take_pic(devId)
    sleep(2)
    return send_from_directory(file_dir, "dev_"+str(devId)+'_test.jpg')


@app.route("/usr/ssh/<int:devId>", methods=['GET'])
def usr_enable_ssh(devId):
    db_api.user_ssh_enable(devId)
    # forward local ssh connections
    return jsonify({"success": True})


if __name__ == '__main__':
    """ Main
    """
    app.run(debug=True, host='0.0.0.0')
