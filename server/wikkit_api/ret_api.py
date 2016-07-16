from wikkit_api import app, db_api
from flask import request, jsonify, abort
import socket
import string
import random
import hashlib
import json
import os
import shutil
import ConfigParser
from datetime import datetime, timedelta


config = ConfigParser.ConfigParser()
config.read("./config.ini")
host = socket.gethostname()
feature_port = int(config.get('retconfig', 'feature_port'))
upload_port = int(config.get('retconfig', 'upload_port'))
chunk_path = config.get('retconfig', 'chunkpath')
file_path = config.get('retconfig', 'filepath')
max_concurrent_trans = int(config.get('retconfig', 'maxconcurrenttrans'))
inactive_timeout = int(config.get('retconfig', 'inactiveTO'))

# TODO: modify this temp_ip_solution
# dev_ip_map = {}


@app.route("/tk1/return_customer/d_feature/<int:cam_id>", methods=['POST'])
def tk1_post_feature(cam_id):
    content = request.json
    if not content:
        abort(400)

    if (isinstance(content, dict) and "img" in content and
       "start_t" in content and "feature" in content):
        # TODO: Admission Control
        content['cameras_id'] = cam_id
        try:
            app_socket = socket.socket()
            app_socket.connect((host, feature_port))
            app_socket.send(json.dumps(content, separators=(',', ':')))
            app_socket.close()

            return jsonify({"success": True})
        except Exception, e:
            return jsonify({"success": False, "reason": str(e)})
    else:
        abort(400)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def cal_chksum(file_name):
    digester = hashlib.md5()
    with open(file_name, "rb") as f:
        for piece in iter(lambda: f.read(4096), b""):
            digester.update(piece)
    return digester.hexdigest()


@app.route("/night/<int:devId>/req_start", methods=['GET'])
def req_start(devId):
    oldest_active = datetime.now() - timedelta(0, inactive_timeout, 0)

    active_trans_no = db_api.get_active_upload(oldest_active)

    if active_trans_no < max_concurrent_trans:
        print "currently active : " + str(active_trans_no)
        chunk_path_dev = chunk_path + str(devId)

        print chunk_path_dev
        try:
            shutil.rmtree(chunk_path_dev + "/")
        except Exception as e:
            print str(e)

        try:
            os.makedirs(chunk_path_dev)
        except OSError as exc:
            print str(exc)

        # call(["mkdir -p " + chunk_path_dev], shell=True)
        # call(["rm " + chunk_path_dev + "/*"], shell=True)
        # call(["rm " + file_path_dev + "/*"], shell=True)

        filename = id_generator()

        db_api.update_upload_activity(devId)

        return jsonify({"filename": filename})
    else:
        return jsonify({})


@app.route("/night/<int:devId>/send_chunk", methods=['POST'])
def send_chunks(devId):
    if (request.files is None or 'file' not in request.files):
        abort(400)
    chunk = request.files['file']
    chunk_path_dev = chunk_path + str(devId)

    chksum = request.form.get('chksum')
    chunkname = request.form.get('chunkname')

    chunk.save(os.path.join(chunk_path_dev, chunkname))

    chksum_cal = cal_chksum(chunk_path_dev + "/" + chunkname)

    if chksum == chksum_cal:
        return jsonify({})
    else:
        return jsonify({"fail_code": 1})


@app.route("/night/<int:devId>/confirm_done", methods=['POST'])
def confirm_done(devId):
    content = request.json
    if (not content and "filename" not in content):
        abort(400)

    filename = content['filename']

    file_path_dev = file_path + str(devId) + "/"
    chunk_path_dev = chunk_path + str(devId) + "/" + filename + "*"

    try:
        shutil.rmtree(file_path_dev + "/")
    except Exception as e:
        print str(e)

    try:
        os.makedirs(file_path_dev)
    except OSError as exc:
        print str(exc)

    os.system("/bin/cat " + chunk_path_dev + "*" + " > " +
              file_path_dev + filename)

    db_api.update_upload_activity(devId, False,
                                  datetime.now() - timedelta(0,
                                                             inactive_timeout,
                                                             0))

    try:
        app_socket = socket.socket()
        app_socket.connect((host, upload_port))
        app_socket.send(str(devId) + ":" + file_path_dev + filename)
        app_socket.close()

        return jsonify({"success": True})
    except Exception, e:
        return jsonify({"success": False, "reason": str(e)})


@app.route("/night/<int:devId>/info_kill", methods=['POST'])
def info_kill(devId):
    chunk_path_dev = chunk_path + str(devId)
    file_path_dev = file_path + str(devId)

    try:
        shutil.rmtree(chunk_path_dev + "/")
        shutil.rmtree(file_path_dev + "/")
    except Exception as e:
        print str(e)

    print("device " + str(devId) + " too slow ... killed")
    db_api.update_upload_activity(devId, False,
                                  datetime.now() - timedelta(0,
                                                             inactive_timeout,
                                                             0))
    return jsonify({})
