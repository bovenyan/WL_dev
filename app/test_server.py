from flask import request, jsonify, abort, Flask
from datetime import datetime, timedelta
import string
import random

app = Flask(__name__)

active_transmission = {}
max_concurrent_trans = 5
kill_timeout = 1800
chunk_path = "/tmp/night-chunks/"
file_path = "/tmp/night-files/"
from subprocess import call


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def clear_inactive_transmission():
    for idx in range(len(active_transmission)):
        if (datetime.now() - active_transmission[key] >
            timedelta(0, kill_timeout, 0)):
            del active_transmission[key]

def cal_chksum(file_name):
    digester = hashlib.md5()
    with open(file_name, "rb") as f:
        for piece in iter(lambda: f.read(4096), b""):
            digester.update(piece)
    return digester.hexdigest()

@app.route("/night/<int:devId>/req_start", methods=['GET'])
def req_start(devId):
    if len(active_transmission) >= max_concurrent_trans:
        clear_inactive_transmission()

    if len(active_transmission) < max_concurrent_trans:
        chunk_path_dev = chunk_path + str(devId)
        call(["mkdir", "-p", chunk_path_dev])
        call(["rm", chunk_path_dev + "/*"])

        filename = id_generator()
        active_transmission[filename] = datetime.now()
        return jsonify({"filename": filename})
    else:
        return jsonify({})

@app.route("/night/<int:devId>/send_chunk", methods=['POST'])
def send_chunks(devId):
    if ('file' not in requests.files):
        abort(400)
    chunk = requests.files['file']
    chunk_path_dev = chunk_path + str(devId)

    chksum = request.form.get['chksum']
    chunkname = request.form.get['chunkname']

    chunk.save(os.path.join(chunk_path_dev, chunkname))

    chksum_cal = cal_chksum(chunk, chunk_path_dev + "/" + chunkname)

    if chksum == chksum_cal:
        return jsonify({})
    else:
        return jsonify({"fail_code": 1})

@app.route("/night/<int:devId>/send_chunk", methods=['POST'])
def confirm_done(devId):
    if (requests.json() is None or "filename" not in requests.json()):
        abort(400)

    file_path_dev = file_path + str(devId)
    call(["mkdir", "-p", file_path_dev])
    call(["cat", chunk_path + filename + "*", ">", file_path + filename])

    del active_transmission[filename]

@app.route("/night/<int:devId>/info_kill", methods=['POST'])
def info_kill(devId):
    chunk_path_dev = chunk_path + str(devId) + "/*"
    call(["rm", "-r", chunk_path_dev])
    print("device " + str(devId) + "too slow ... killed"
