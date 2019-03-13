import hashlib
import time

from flask import request, g

from master.db import db
from master.app import app
from master.models import Node
from master.models import get_root_node, append, get_levels, get_all_nodes
from master.models import get_leafs, validate_chain, get_all_nodes_in_tree, graphviz_tree
from master.models import consistency_path
from master.views.models import json_response


@app.route("/api/log/new")
def log_new():
    for i in range(1, 11):
        data = {"name": f"Name-{i}",
                "data": f"Datablock-{i}"}
        node = append(data)
        print(f"Created node {i}")
    return "Ok?"


@app.route("/api/log/tree/stats")
@json_response
def log_get_tree_stats():
    engine = db.get_engine().name
    bytes_used = 0
    if engine == "postgresql":
        if "humanize" in request.args.keys():
            bytes_used = db.engine.execute("SELECT pg_size_pretty (pg_relation_size('node'));").first()[0]
        else:
            bytes_used = db.engine.execute("SELECT pg_relation_size('node');").first()[0]
    elif engine == "sqlite":
        suffixes = ['bytes', 'kB', 'mB', 'gB', 'tB', 'pB']
        def humansize(nbytes):
            i = 0
            while nbytes >= 1024 and i < len(suffixes)-1:
                nbytes /= 1024.
                i += 1
            f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
            return '%s %s' % (f, suffixes[i])
        if "humanize" in request.args.keys():
            bytes_used = humansize(db.engine.execute("SELECT sum(pgsize-unused) FROM dbstat WHERE name='node';").first()[0])
        else:
            bytes_used = db.engine.execute("SELECT sum(pgsize-unused) FROM dbstat WHERE name='node';").first()[0]
    return {"root node": get_root_node().to_json(),
            "level nodes": get_levels().count(),
            "leaf nodes": get_leafs().count(),
            "total nodes": get_all_nodes().count(),
            "bytes used": bytes_used}


@app.route("/api/log/tree/root")
@json_response
def log_get_tree_root():
    print(get_levels().count())
    print(get_leafs().count())
    return get_root_node()


@app.route("/api/log/tree")
@json_response
def log_get_tree_all():
    return (db.session.query(Node)).all()


@app.route("/api/log/tree/leaf/index/<id>")
@json_response
def log_get_leaf_index(id):
    return (db.session.query(Node).filter(Node.leaf_index == id)).first()


@app.route("/api/log/tree/id/<id>")
@json_response
def log_get_id(id):
    return (db.session.query(Node).filter(Node.id == id)).first()


@app.route("/api/log/tree/hash/<hash>")
@json_response
def log_get_hash(hash):
    return (db.session.query(Node).filter(Node.hash == hash)).first()


def _get_validation_chain(node):
    side = lambda x: "RIGHT" if x.is_right() else "LEFT"
    path = [(side(node), node.to_json())]
    while node.get_child() is not None:
        if node.is_left():
            path.append(("RIGHT", node.get_child().right.to_json()))
        elif node.is_right():
            path.append(("LEFT", node.get_child().left.to_json()))
        node = node.get_child()
    root = get_root_node()
    return {"root": root.to_json(),
            "path": path}


@app.route("/api/log/tree/validate/hash/<hash>")
@json_response
def log_get_validation(hash):
    node = (db.session.query(Node).filter(Node.hash == hash)).first()
    if node is None:
        return "No such object", 400
    path = _get_validation_chain(node)
    path["validation"] = validate_chain(path["root"], path["path"])
    print(path["validation"])
    return path


@app.route("/api/log/tree/validate/id/<id>")
@json_response
def log_get_validation_id(id):
    node = (db.session.query(Node).filter(Node.leaf_index == id)).first()
    if node is None:
        return {"status": "No such object"}, 400
    path = _get_validation_chain(node)
    path["validation"] = validate_chain(path["root"], path["path"])
    print(path["validation"])
    return path

@app.route("/api/log/tree/consistency/<old_hash>/<leafs>")
@app.route("/api/log/tree/consistency/")
@json_response
def log_get_consistency_proof(leafs=6, old_hash="64fd4d81ed081f789ca5827f9a3f05215a58a66c23d1ba6c8986ec02e729464a2c5ca0cd881931ea14d8bc79087976ee9de07a8cf7c13d1f1a11aa6180d2f261"):
    old_path, full_path = consistency_path(leafs)
    return {"root": get_root_node().to_json(),
            "inclusion": validate_chain({"hash": old_hash}, old_path),
            "consistency": validate_chain({"hash": get_root_node().hash}, full_path),
            "path": full_path}

@app.route("/api/log/tree/validate/chain", methods=['POST'])
@json_response
def log_validate_chain(id):
    data = request.get_json(silent=True)
    if not data.get("root"):
        return {"status": "No valid root"}, 400
    if not data.get("path"):
        return {"status": "No valid path"}, 400
    ret = validate_chain(data["root"], data["chain"])
    if ret:
        return {"status": ret,
                "root": data["root"]}
    return {"status": ret}, 300


@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
    now = time.time()
    duration = now - g.start
    response.headers["X-Duration"] = duration
    return response


@app.route("/api/log/tree/append", methods=["POST"])
@json_response
def log_tree_append():
    data = request.get_json(silent=True)
    try:
        node = append(data)
    except:
        return {"status": "Could not append"}, 400
    return {"status": "ok",
            "node": node.to_json()}, 200


@app.route("/api/log/tree/graphviz")
def log_tree_graphviz():
    nodes = get_all_nodes_in_tree()
    return graphviz_tree(get_leafs().count(), nodes)
