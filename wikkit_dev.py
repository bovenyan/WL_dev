from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
import db_conn as db
import ConfigParser
import os

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
            ?? curl -i -H "Content-Type: application/json" \
               -X GET http://localhost:5000/dev/<devId>
    """
    record = db_api.device_get_rec(devId)

    if record is None:
        abort(400)

    last_updated = record[1]
    manage_flags = int(record[2])

    if (manage_flags % 2 != 0):  # operation mode
        db_api.device_reset_op(devId)
        return jsonify({"manage": False})

    # verify the keep alive for management
    if (datetime.now() - last_updated > timedelta(0, manage_keepalive,
                                                  0)):
        db_api.device_reset_op(devId)
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
    video = bool((op_codes >> 5) % 2)

    # script updating
    update = bool((op_codes >> 6) % 2)
    commit = False
    if (not update):  # update and commit cannot happen together
        commit = bool((op_codes >> 7) % 2)

    return jsonify({"servo_active": servo_active,
                    "servo_turn_mode": servo_turn_mode,
                    "servo_inc_xy": servo_inc_xy,
                    "pos_x": pos_x,
                    "pos_y": pos_y,
                    "picture": picture,
                    "video": video,
                    "update": update,
                    "commit": commit})


@app.route("/dev/<int:devId>", methods=['POST'])
def dev_report_done(devId):
    """ Device Interface
        HowTo use:
            ?? curl -i -H "Content-Type: application/json" \
               -X POST -d {""} \
                http://localhost:5000/dev/<devId>
    """

    content = request.json
    if not content:
        abort(400)

    if "servo_turned" in content:
        pos_x = int(content['pos_x'])
        pos_y = int(content['pos_y'])

        if bool(content["servo_turned"]):
            db_api.device_flop_mgmt(devId, False)
            db_api.device_update_pos(devId, pos_x, pos_y)

    if "picture_taken" in content and bool(content["picture_taken"]):
        db_api.device_flop_mgmt(devId, True)

    if "update_complete" in content and content["update_complete"]:
        db_api.device_flop_mgmt(devId, False)

    if "commit_complete" in content and content["commit_complete"]:
        db_api.device_flop_mgmt(devId, False)

    return jsonify({"success": True})


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif'])


@app.route("/dev/<int:devId>/picture", methods=['POST'])
def dev_post_picture(devId):
    file = request.files['file']
    if file and allowed_file(file.filename):
        file.save(os.path.join(file_dir, 'dev_'+str(devId)+'_test.png'))

    return jsonify({"success": True})

if __name__ == '__main__':
    """ Main
    """
    app.run(debug=True, host='0.0.0.0')
