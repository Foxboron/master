from flask import request, g

from master.app import app
from master.views.models import json_response
from master.keys import *


@app.route("/api/crypto/key")
@json_response
def show_keys():
    return get_public_key()


@app.route("/api/crypto/verify", methods=['POST'])
@json_response
def verify_tree_root():
    data = request.get_json(silent=True)
    if not data.get("hash"):
        return {"status": "Missing hash field"}, 400
    if not data.get("signature"):
        return {"status": "Missing signature field"}, 400
    signature = {'keyid': get_public_key()["keyid"], 
                 'sig': data["signature"]}
    verfied = verify_data(signature, data["hash"])
    return {"status": "ok",
            "verified": verfied}, 400


