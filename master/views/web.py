from master.app import app
from master.db import db
from master.models import Buildinfo, Package, Buildinfo, LinkMetadata, Version

from flask import render_template


@app.route('/')
def index():
    entries = (db.session.query(Package)).all()
    print(entries)
    return render_template('index.html', packages=entries)


@app.route('/sources/<name>')
def all_sources_pkg(name):
    entries = (db.session.query(Version, Buildinfo, LinkMetadata)
            .group_by(Version.id)
            ).all()
    return render_template('source.html', package=name, entries=entries)

@app.route('/sources/<name>/<version>')
def all_sources_version(name, version):
    entries = (db.session.query(Version, Buildinfo, LinkMetadata)
            .filter(Package.name == name)
            .filter(Version.version == version)
            .group_by(Version.id)).all()
    return render_template('source.html', package=name , entries=entries)


@app.route('/sources/<name>/<version>/buildinfo')
def get_buildinfo(name, version):
    entries = (db.session.query(Buildinfo)
            .filter(Package.name == name)
            .filter(Version.version == version)).first()
    return entries.text

@app.route('/sources/<name>/<version>/metadata')
def get_metadata(name, version):
    entries = (db.session.query(LinkMetadata)
            .filter(Package.name == name)
            .filter(Version.version == version)).first()
    return entries.text
