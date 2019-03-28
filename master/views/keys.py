from master.app import app
from master.views.models import json_response
from master.keys import *


@app.route("/api/keys")
@json_response
def show_keys():
    return get_public_key()

