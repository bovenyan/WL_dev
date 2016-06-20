from wikkit_api import app
from flask import request, jsonify, abort
import socket
import json
import ConfigParser
from datetime import datetime, timedelta


config = ConfigParser.ConfigParser()
config.read("./config.ini")
host = socket.gethostname()
algo_port = int(config.get('retconfig', 'port'))
chunk_path = config.get('retconfig', 'chunkpath')
file_path = config.get('retconfig', 'filepath')
max_concurrent_trans = int(config.get('retconfig', 'maxconcurrenttras'))
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
            app_socket.connect((host, algo_port))
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
 
    active_trans_no = db_api.get_active_upload(self, oldest_active) 

    if active_trans_no < max_concurrent_trans:
        chunk_path_dev = chunk_path + str(devId) 
	file_path_dev = file_path + str(devId)

        call(["mkdir", "-p", chunk_path_dev])
        call(["rm " + chunk_path_dev + "/*"], shell=True)

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

    file_path_dev = file_path + str(devId) + "/" + filename
    chunk_path_dev = chunk_path + str(devId) + "/" + filename + "*"

    call(["mkdir", "-p", file_path_dev])
    call(["cat " + chunk_path_dev + "*" + " > " + file_path_dev + filename],
	shell=True)

    db_api.update_upload_activity(self, devId, False, 
                                  datetime.now() - timedelta(0, inactive_timeout, 0))

    return jsonify({})


@app.route("/night/<int:devId>/info_kill", methods=['POST'])
def info_kill(devId):
    chunk_path_dev = chunk_path + str(devId) + "/*"
    call(["rm", "-r", chunk_path_dev])
    print("device " + str(devId) + "too slow ... killed")
    db_api.update_upload_activity(self, devId, False, 
                                  datetime.now() - timedelta(0, inactive_timeout, 0))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
