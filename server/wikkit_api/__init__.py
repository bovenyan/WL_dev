from flask import Flask
app = Flask(__name__)

import wikkit_dev.dev_api
import wikkit_dev.face_api
import wikkit_dev.ret_api
