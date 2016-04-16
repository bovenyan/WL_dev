from flask import request, jsonify, abort
from wikkit_api import app
import os
import datetime
import ConfigParser
import random

config = ConfigParser.ConfigParser()
config.read("./config.ini")
image_dir = config.get('faceconfig', 'imgdir')


@app.route("/wikkitface/groups", methods=['POST'])
def post_groups():
    content = request.json

    if (not ("group_name" in content)):
        abort(400)

    name = content["group_name"]

    group_id = 1

    return jsonify({"group_id": group_id, "group_name": name})


@app.route("/wikkitface/groups", methods=['GET'])
def get_groups():
    groups_info = []
    groups_info.append({"group_id": 1, "group_name":  "wikkit"})
    groups_info.append({"group_id": 2, "group_name":  "302"})
    return jsonify({"groups": groups_info})


@app.route("/wikkitface/groups/<int:group_id>", methods=['GET'])
def get_group(group_id):
    if (group_id == 0):
        group_info = {}
        group_info["group_id"] = 1
        group_info["group_name"] = "wikkit"
        group_info["persons"] = [{"person_id": 1}, {"person_id": 2}]

        return jsonify(group_info)

    if (group_id == 1):
        group_info = {}
        group_info["group_id"] = 2
        group_info["group_name"] = "302"
        group_info["persons"] = [{"person_id": 1}]

        return jsonify(group_info)

    abort(400)


@app.route("/wikkitface/persons", methods=['POST'])
def post_persons():
    content = request.json
    if (not ("person_id" in content and "person_name" in content)):
        abort(400)

    group_ids = []

    if ("group_ids" in content and not isinstance(content["group_ids"])):
        abort(400)
    else:
        group_ids = content["group_ids"]

    face_ids = []
    if ("face_ids" in content and not isinstance(content["face_ids"])):
        abort(400)
    else:
        face_ids = content["face_ids"]

    try:
        person_id = int(content["person_id"])
        person_name = int(content["person_name"])

        return jsonify({"person_id": person_id,
                        "person_name": person_name,
                        "group_ids": group_ids,
                        "face_ids": face_ids})
    except Exception, e:
        print str(e)
        abort(400)


@app.route("/wikkitface/persons/<int:person_id>", methods=['GET'])
def get_person(person_id):
    if (person_id == 1):
        person_info = {}
        person_info["person_id"] = 1
        person_info["person_name"] = "leo"
        person_info["group_ids"] = [1, 2]
        person_info["face_ids"] = [3]

        return jsonify(person_id)

    if (person_id == 2):
        person_info = {}
        person_info["person_id"] = 2
        person_info["person_name"] = "leo"
        person_info["group_ids"] = [1]
        person_info["face_ids"] = [3]

        return jsonify(person_id)

    abort(400)


@app.route("/wikkitface/persons/<int:person_id>", methods=['DELETE'])
def delete_person(person_id):
    if (person_id == 1 or person_id == 2):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed"})


def allowed_face_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['jpg', 'jpeg', 'png'])


@app.route("/wikkitface/persons/<int:person_id>/addFace", methods=['POST'])
def post_face(person_id):
    if 'image' not in request._files:
        abort(400)

    file = request.files['image']

    if file and allowed_face_file(file.filename):
        file.save(os.path.join(image_dir, 'face_' + str(person_id) +
                               datetime.datetime.now().isoformat()))
        return jsonify({"face_id": 1, "person_id": person_id})

    abort(400)


@app.route("/wikkitface/persons/<int:person_id>/faces/<int:face_id>",
           methods=['DELETE'])
def delete_face(person_id, face_id):
    if (face_id == 1):
        os.system("rm " + image_dir + "/face_" + str(face_id) + "*")
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed"})


@app.route("/wikkitface/detect", methods=['POST'])
def detect_face():
    if 'image' not in request.files:
        abort(400)

    file = request.files['image']

    if file and allowed_face_file(file.filename):
        face_info = {"face_id": "1", "left": 145, "right": 147,
                     "top": 305.0, "bottom": 305.0, "age": 34,
                     "gender": 99,
                     "landmarks": [{"x": 48, "y": 55}, {"x": 69, "y": 33}]}

        return jsonify({"faces": face_info})

    abort(400)


@app.route("/wikkitface/verify/<int:person_id>", methods=['POST'])
def verify_face(person_id):
    if not (person_id in range(1, 4)):
        abort(400)
    if 'image' not in request.files:
        abort(400)

    file = request.files['image']
    if file and allowed_face_file(file.filename):
        return jsonify({"ismatch": False, "confidence": 50.5024})


@app.route("/wikkitface/recognize/<int:group_id>", methods=['POST'])
def recognize_face(group_id):
    if (group_id != 1 and group_id != 2):
        abort(400)

    if 'image' not in request.files:
        abort(400)

    file = request.files['image']
    if file and allowed_face_file(file.filename):
        recog_info = {"candidates": [{"person_id": 1,
                                      "person_name": "leo",
                                      "face_id": 2,
                                      "confidence": 88.90695571899414},
                                     {"person_id": 2,
                                      "person_name": "john",
                                      "face_id": 5,
                                      "confidence": 54.86775207519531},
                                     {"person_id": 3,
                                      "person_name": "frank",
                                      "face_id": 6,
                                      "confidence": 32.77520751953186}
                                     ]}
        return jsonify(recog_info)

    abort(400)


@app.route("/wikkitface/compare", methods=['POST'])
def compare_face():
    content = request.json
    if not ("face_id1" in content and "face_id2" in content):
        abort(400)

    try:
        same_person = int(content["face_id1"]) - int(content["face_id2"])
        same_person = bool(same_person % 2)
        return jsonify({"similarity": random.randint(1, 100),
                        "isSamePerson": same_person})
    except Exception, e:
        print str(e)
        abort(400)
