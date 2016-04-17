from flask import Flask
app = Flask(__name__)

import wikkit_api.dev_api
import wikkit_api.face_api
import wikkit_api.ret_api
