from master.app import app
from master.db import db
from master.models import Buildinfo, Package, LinkMetadata, Version

from flask import render_template


@app.route("/")
def index():
    entries = (db.session.query(Package).distinct(Package.name)).all()
    return render_template("index.html", packages=entries)


@app.route("/sources/<pkgname>")
def all_sources_pkg(pkgname):
    entries = (
        db.session.query(Package, Version, LinkMetadata, Buildinfo)
        .join(Version, Version.package_id == Package.id)
        .filter(Package.name==pkgname)
        .filter(LinkMetadata.version_id==Version.id)
        .filter(LinkMetadata.uuid==Buildinfo.uuid)
    ).all()
    return render_template("source.html", package=pkgname, entries=entries)


@app.route("/sources/<name>/<version>")
def all_sources_version(name, version):
    entries = (
        db.session.query(Version, Buildinfo, LinkMetadata)
        .filter(Package.name == name)
        .filter(Version.version == version)
        .filter(Buildinfo.uuid == LinkMetadata.uuid)
    ).all()
    return render_template("source.html", package=name, entries=entries)


@app.route("/sources/<name>/<version>/buildinfo")
def get_buildinfo(name, version):
    entries = (
        db.session.query(Buildinfo)
        .filter(Package.name == name)
        .filter(Version.version == version)
        .order_by(Buildinfo.id.desc())
    ).first()
    return entries.text


@app.route("/sources/<name>/<version>/metadata")
def get_metadata(name, version):
    entries = (
        db.session.query(LinkMetadata)
        .filter(Package.name == name)
        .filter(Version.version == version)
        .order_by(LinkMetadata.id.desc())
    ).first()
    return entries.text
