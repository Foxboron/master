import inspect
from datetime import datetime
from collections import OrderedDict
from functools import wraps

from master.db import db



def recurse(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if len(inspect.stack()) > 25:
            return None
        return func(*args, **kwargs)
    return wrapped



class Buildinfo(db.Model):
    __tablename__ = 'buildinfo'
    id = db.Column(db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = db.Column(db.Text(), index=True, nullable=False)
    version = db.relationship("Version", back_populates="buildinfo")
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'))

    def __repr__(self):
        return '<buildinfo: {}>'.format(self.id)
    
    @recurse
    def to_json(self, recurse=True):
        j = OrderedDict()
        j["id"] = self.id
        j['date'] = self.created
        j["text"] = self.text
        j["versions"] = self.version.to_json(recurse=False) 
        return j


class LinkMetadata(db.Model):
    __tablename__ = 'linkmetadata'
    id = db.Column(db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    text = db.Column(db.Text(), index=True, nullable=False)

    version = db.relationship("Version", back_populates="linkmetadata")
    version_id = db.Column(db.Integer, db.ForeignKey('version.id'))

    def __repr__(self):
        return '<linkmetadata: {}>'.format(self.id)

    @recurse
    def to_json(self, recurse=True):
        j = OrderedDict()
        j["id"] = self.id
        j["text"] = self.text
        j['date'] = self.created
        j["versions"] = self.version.to_json(recurse=False) 
        return j

class Version(db.Model):
    __tablename__ = 'version'
    id = db.Column(db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    version = db.Column(db.String(64), nullable=False)

    buildinfo = db.relationship("Buildinfo", back_populates="version")
    linkmetadata = db.relationship("LinkMetadata", back_populates="version")

    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    package = db.relationship("Package", back_populates="version")

    def __repr__(self):
        return '<Version: {}>'.format(self.version)

    @recurse
    def to_json(self, recurse=True):
        j = OrderedDict()
        j["id"] = self.id
        j['date'] = self.created
        j["version"] = self.version
        j["linkmetadata"] = list(map(lambda x: x.to_json(recurse=False), self.linkmetadata))
        j["buildinfo"] = list(map(lambda x: x.to_json(recurse=False), self.buildinfo))
        j["package"] = self.package.to_json(recurse=False)
        return j

class Package(db.Model):
    __tablename__ = 'package'
    id = db.Column(db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(96), index=True, nullable=False)
    version = db.relationship("Version", back_populates="package")

    def __repr__(self):
        return '<Package: {}>'.format(self.name)
    
    @recurse
    def to_json(self, recurse=True):
        j = OrderedDict()
        j["id"] = self.id
        j['date'] = self.created
        j["name"] = self.name
        j["versions"] = list(map(lambda x: x.to_json(recurse=False), self.version))
        return j
