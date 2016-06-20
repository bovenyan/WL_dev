from flask import Flask
import lib.db_conn as db

app = Flask(__name__)

db_api = db.db_api("./config.ini")
import wikkit_api.dev_api
import wikkit_api.face_api
import wikkit_api.ret_api
