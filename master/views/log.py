import hashlib

from master.db import db
from master.app import app
from master.models import Node, create_level_node, create_data_node, get_root_node, get_levels, get_leafs, validate_chain, get_subtrees
from master.views.models import json_response

from flask import request



@app.route("/api/log/new")
def log_new():
    # for i in range(1, 51):
    #     data = {"name": f"Name-{i}",
    #             "data": f"Datablock-{i}"}
        # append(data)

    # node1 = create_data_node({"data": "test1"})
    # node2 = create_data_node({"data": "test2"})
    # create_level_node(node1, node2)
    # print("yay")
    # node3 = create_level_node(node1, node2)
    # print(node3.left)
    # print(node3.right)
    return "Ok?"


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

@app.route("/api/log/tree/id/<id>")
@json_response
def log_get_id(id):
    return (db.session.query(Node).filter(Node.id == id)).first()

@app.route("/api/log/tree/hash/<hash>")
@json_response
def log_get_hash(hash):
    return (db.session.query(Node).filter(Node.hash == hash)).first()

@app.route("/api/log/tree/validate/hash/<hash>")
@json_response
def log_get_validation(hash):
    node = (db.session.query(Node).filter(Node.hash == hash)).first()
    if node is None:
        return "No such object"
    side = lambda x: "RIGHT" if x.is_right() else "LEFT"
    # ({LEFT,RIGHT}, Node)
    path = [(side(node), node)]
    while node.parent is not None:
        if node.is_left():
            path.append(("RIGHT", node.get_child().right))
        elif node.is_right():
            path.append(("LEFT", node.get_child().left))
        node = node.get_child()
    return path

@app.route("/api/log/tree/validate/id/<id>")
@json_response
def log_get_validation_id(id):
    node = (db.session.query(Node).filter(Node.id == id)).first()
    if node is None:
        return "No such object"
    side = lambda x: "RIGHT" if x.is_right() else "LEFT"
    # ({LEFT,RIGHT}, Node)
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

@app.route("/api/log/tree/append", methods=["POST"])
def log_tree_append():
    data = request.get_json(silent=True)
    if get_leafs().count() == 0:
        create_data_node(data)
        return
    subtrees = get_subtrees()
    new_node = create_data_node(data)
    for node in reversed(subtrees):
        new_parent = create_level_node(node, new_node)
        new_node = new_parent
        db.session.commit()
    return "Ok"
