from types import MethodType
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import ClauseElement
from .app import app

db = None

def db_get(self, model, defaults=None, **kwargs):
    return self.session.query(model).filter_by(**kwargs).first()


def db_create(self, model, defaults=None, **kwargs):
    params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
    params.update(defaults or {})
    instance = model(**params)
    self.session.add(instance)
    self.session.flush()
    return instance


def db_get_or_create(self, model, defaults=None, **kwargs):
    instance = self.get(model, defaults, **kwargs)
    if instance:
        return instance
    return self.create(model, defaults, **kwargs)

db = SQLAlchemy(app)
db.get = MethodType(db_get, db)
db.create = MethodType(db_create, db)
db.get_or_create = MethodType(db_get_or_create, db)
