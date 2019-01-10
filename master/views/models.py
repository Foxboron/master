from functools import wraps

from flask import json, request
from debian.deb822 import Deb822

from master.app import app
from master.db import db
from master.models import Buildinfo, Package, Buildinfo, LinkMetadata, Version


def json_response(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        response = func(*args, **kwargs)
        code = 200
        if isinstance(response, tuple):
            response, code = response
        dump = json.dumps(list(response), indent=2, sort_keys=False)
        return dump, code, {'Content-Type': 'application/json; charset=utf-8'}
    return wrapped


@app.route('/api/buildinfo', methods=['PUT', 'POST', 'GET'])
def api_buildinfo_id():
    pkg = db.get_or_create(Package, name="Test")
    # ver = db.get_or_create(Version, version="1.0.0", package=pkg)
    ver2 = db.get_or_create(Version, version="1.2.0", package=pkg)
    # db.get_or_create(LinkMetadata, version=ver, text="Test")
    # db.get_or_create(Buildinfo, version=ver, text="Test")
    db.get_or_create(LinkMetadata, version=ver2, text="Test3")
    db.get_or_create(Buildinfo, version=ver2, text="Test3")
    db.session.commit()
    return "Ok?"

@app.route('/new_build', methods=['POST'])
def new_build():
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

    pkg = db.get_or_create(Package, name=source)
    ver = db.get_or_create(Version, version=version, package=pkg)
    db.get_or_create(LinkMetadata, version=ver)
    db.get_or_create(Buildinfo, version=ver)
    db.session.commit()

    return

@app.route('/api/buildinfos', methods=['PUT', 'POST', 'GET'])
@json_response
def api_buildinfos():
    entries = (db.session.query(Package)).all()
    return map(lambda x: x.to_json(), entries)
