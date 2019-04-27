import uuid

from flask import request, g

from master.db import db
from master.app import app
from master.models import append, Node, Package, Version, LinkMetadata, Buildinfo
from master.views.models import json_response


from debian.deb822 import Deb822

@app.route("/api/rebuilder")
@json_response
def rebuilder():
    return "ok"

@app.route("/api/rebuilder/submit", methods=['POST'])
@json_response
def rebuilder_submit():
    metadata = request.files['metadata']
    buildinfo = request.files['buildinfo']
    source = None
    version = None
    for paragraph in Deb822.iter_paragraphs(buildinfo):
        for item in paragraph.items():
            if item[0] == 'Source':
                source = item[1]
            if item[0] == 'Version':
                version = item[1]
    buildinfo.seek(0)
    id = uuid.uuid4()
    pkg = db.create(Package, name=source)
    ver = db.create(Version, version=version, package=pkg)
    db.get_or_create(LinkMetadata, version=ver, text=metadata.read().decode("utf-8"), uuid=id)
    db.get_or_create(Buildinfo, version=ver, text=buildinfo.read().decode("utf-8"), uuid=id)
    db.session.commit()
    buildinfo.seek(0)
    metadata.seek(0)
    j = {"type": "inclusion",
         "package": source,
         "version": version,
         "linkmetadata": str(metadata.read()),
         "buildinfo": str(buildinfo.read())}
    try:
        node = append(j)
    except Exception as e:
        print(e)
        return {"status": "Could not append"}, 400
    return {"status": "ok",
            "node": node.to_json()}, 200

@app.route("/api/rebuilder/fetch/<name>/<version>")
@json_response
def rebuilder_fetch(name, version):
    records = (db.session.query(Node)
            .filter(Node.data.op('->>')('package') == name)
            .filter(Node.data.op('->>')('version') == version)
            .order_by(Node.created.desc())
            ).all()
    return records


@app.route("/api/rebuilder/revoke", methods=['POST'])
@json_response
def rebuilder_revoke():
    data = request.get_json(silent=True)
    if data.get("hash"):
        return {"status": "Missing hash field"}, 400
    if data.get("reason"):
        return {"status": "Missing reason field"}, 400

    revoked_node = (db.session.query(Node).filter(Node.hash == data["hash"])).first()
    if revoked_node.type != "data":
        return {"status": "Can't revoke level node"}, 400
    if revoked_node.data["type"] != "inclusion":
        return {"status": "Needs to be a inclusion node"}, 400
    j = {"type": "revoke",
         "package": revoked_node.data["package"],
         "version": revoked_node.data["version"],
         "hash": data["hash"],
         "reason": data["reason"]}
    try:
        node = append(j)
    except:
        return {"status": "Could not append"}, 400
    return {"status": "ok",
            "node": node.to_json()}, 200

