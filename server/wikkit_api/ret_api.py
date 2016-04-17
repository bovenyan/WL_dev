from wikkit_api import app
from flask import request, jsonify, abort
import socket
import json
import ConfigParser


config = ConfigParser.ConfigParser()
config.read("./config.ini")
host = socket.gethostname()
algo_port = int(config.get('algoconfig', 'port'))

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
            app_socket.close

            return jsonify({"success": True})
        except Exception, e:
            return jsonify({"success": False, "reason": str(e)})
    else:
        abort(400)

# # TODO: tempo for retrieving IP
# @app.route("/usr/<int:devId>/getip", methods=['GET'])
# def usr_getip(devId):
#     if devId in dev_ip_map:
#         return jsonify({"ip": dev_ip_map[devId]})
#     else:
#         return jsonify({"ip": ""})
