import hashlib
import math
import json
from datetime import datetime
from collections import OrderedDict

from master.keys import sign_data
from master.db import db
from .util import recurse

from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy_utils import JSONType



class Node(db.Model):
    __tablename__ = "node"

    id = db.Column(
        db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True
    )
    leaf_index = db.Column(db.Integer(), default=0)
    type = db.Column(db.String(10), nullable=False)
    hash = db.Column(db.String(128))
    signature = db.Column(db.String(128))
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data = db.Column(JSONB)
    height = db.Column(db.Integer(), default=0)
    children_right_id = db.Column(db.Integer, db.ForeignKey("node.id"))
    children_left_id = db.Column(db.Integer, db.ForeignKey("node.id"))

    right = db.relationship("Node",
            foreign_keys='Node.children_right_id',
            uselist=False,
            backref=db.backref('children_right', remote_side=[id]))

    left = db.relationship("Node", 
            foreign_keys='Node.children_left_id',
            uselist=False,
            backref=db.backref('children_left', remote_side=[id]))

    children_id = db.Column(db.Integer, db.ForeignKey("node.id"))

    def is_type(self, type):
        return self.type == type

    def __str__(self):
        return f"<Node: {self.type} ({self.get_hash()})>"

    def __repr__(self):
        return self.__str__()

    def get_name(self):
        """ Internal function to generate graphviz """
        return self.get_hash()[:10].upper()

    def is_left(self):
        if self.children_left:
            return self.children_left.left == self
        return False

    def is_right(self):
        if self.children_right:
            return self.children_right.right == self
        return False

    def get_child(self):
        if self.children_right:
            return self.children_right
        if self.children_left:
            return self.children_left

    def get_hash(self, new=None):
        if not self.hash or new:
            h = hashlib.sha512()
            h.update(self.type.encode('utf-8'))
            if self.data:
                for k, v in self.data.items():
                    h.update((k+v).encode('utf-8'))
            self.append_parents(h)
            self.hash = h.hexdigest()
        return self.hash

    def append_parents(self, h):
        if self.left:
            h.update(self.left.get_hash().encode('utf-8'))
        if self.right:
            h.update(self.right.get_hash().encode('utf-8'))
        return h

    @recurse
    def to_json(self):
        j = OrderedDict()
        j["id"] = self.id
        j["type"] = self.type
        j["created"] = self.created
        j["hash"] = self.get_hash()
        j["signature"] = self.signature
        j["height"] = self.height
        j["right"] = ""
        j["left"] = ""
        j["parent"] = ""
        j["data"] = {}
        if self.get_child():
            j["parent"] = self.get_child().get_hash()
        if self.right:
            j["right"] = self.right.get_hash()
        if self.left:
            j["left"] = self.left.get_hash()
        if self.data:
            try:
                j["data"] = json.loads(self.data)
            except:
                j["data"] = self.data
        return j


@event.listens_for(Node, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.get_hash()
    return target

@event.listens_for(Node, 'after_update')
def receive_after_update(mapper, connection, target):
    target.get_hash(new=True)
    return target

def get_all_nodes():
    return (db.session.query(Node).order_by(Node.id.desc()))


def get_leafs():
    return db.session.query(Node).filter(Node.type == "data")


def get_levels():
    return db.session.query(Node).filter(Node.type == "level")


def get_root_node():
    return (db.session.query(Node).order_by(Node.id.desc())).first()


def get_subtrees():
    subtrees = []
    leaf_count = get_leafs().count()
    loose_leafs = leaf_count - 2**int(math.log(leaf_count, 2))
    the_node = get_root_node()
    while loose_leafs:
        subtrees.append(the_node.left)
        the_node = the_node.right
        loose_leafs -= 2**int(math.log(loose_leafs, 2))
    subtrees.append(the_node)
    return subtrees


def append(data):
    if get_leafs().count() == 0:
        n = create_data_node(data)
        db.session.commit()
        return n
    subtrees = get_subtrees()
    # If there are less subtrees we can't connect the new
    # root in a proper way.
    if len(subtrees) >= 2:
        root = get_root_node()
        db.session.delete(root)
        db.session.commit()
    new_node = create_data_node(data)
    ret = new_node
    for node in reversed(subtrees):
        new_parent = create_level_node(node, new_node)
        new_node = new_parent
    signature = sign_data(new_node.hash)
    new_node.signature = signature["sig"]
    db.session.commit()
    return ret

def get_heights(num):
    ret = []
    while num:
        height = math.floor(math.log(num, 2))
        num -= 2**height
        ret.append(height)
    return ret

def subroots(id, height):
    node = (db.session.query(Node)
            .filter(Node.leaf_index == id)
            .filter(Node.type == "data")
            ).first()
    i = 0
    while i < height:
        next_node = node.get_child()
        i += 1
        node = next_node
    return node

def inclusion_path(position):
    heights = get_heights(position)
    path = []
    start = 1
    for h in heights:
        next_subroot = subroots(start, h)
        if next_subroot.get_child() and next_subroot.get_child().get_child():
            if next_subroot.get_child().is_left():
                path.append(("LEFT", next_subroot))
            else:
                path.append(("RIGHT", next_subroot))
        else:
            if next_subroot.is_left():
                path.append(("LEFT", next_subroot))
            else:
                path.append(("RIGHT", next_subroot))
        start += 2**h
    path[-1] = ("LEFT", path[-1][1])
    return path

def inclusion_proof(position):
    path = [("LEFT", node.to_json()) for side, node in inclusion_path(position)]
    n = len(path)-1
    path = (path[n:] + path[:n])
    return path


def straighten_path(signed_hashes, start):
    signed_hashes = list(signed_hashes)
    if not signed_hashes: return None
    if len(signed_hashes) <= 1: return signed_hashes[0][1]
    i = start
    ret = []
    h = list(signed_hashes[i])
    h[0] = "LEFT"
    ret.append(h)
    while len(signed_hashes) > 1:
        if signed_hashes[i][0] == "LEFT":
            if i == 0: new_sign = "LEFT"
            else: new_sign = signed_hashes[i + 1][0]
            new_hash = (signed_hashes[i][1], signed_hashes[i + 1][1])
            h = list(signed_hashes[i+1])
            h[0] = "RIGHT"
            ret.append(h)
            move = +1
        else:
            new_sign = signed_hashes[i - 1][0]
            new_hash = (signed_hashes[i - 1][1], signed_hashes[i][1])
            h = list(signed_hashes[i-1])
            h[0] = "LEFT"
            ret.append(h)
            move = -1
        signed_hashes[i] = (new_sign, new_hash)
        del signed_hashes[i+move]
        if move < 0: i -= 1
    return ret

def consistency_path(position):
    path = inclusion_path(position)
    other_side = []
    subpath = path[:]
    while subpath[-1][-1].get_child() is not None:
        last_root = subpath[-1][-1]
        if last_root is last_root.get_child().left:
            if last_root.get_child().is_right():
                other_side.append(("RIGHT", last_root.get_child().right))
            else:
                other_side.append(("LEFT", last_root.get_child().right))
            subpath = subpath[:-1]
        else:
            subpath = subpath[:-2]
        subpath.append(("", last_root.get_child()))
    return path, other_side

def consistency_proof(position):
    path, other_side = consistency_path(position)
    path = [(side, node.to_json()) for side, node in path]
    n = len(path)-1
    other_side = [(side, node.to_json()) for side, node in other_side]
    full_path = straighten_path(path+other_side, n)
    path = [("LEFT", node) for side, node in path]
    path = (path[n:] + path[:n])
    return path, full_path



def create_level_node(left, right):
    # Invalidate old children.
    # Should probably do this in the ORM.
    right.children_left = None
    right.children_right = None
    left.children_left = None
    left.children_right = None
    if left is None:
        raise Exception("Left is None")
    if right is None:
        raise Exception("Right is None")
    return db.create(Node, type="level", right=right, left=left, height=left.height+1)


def create_data_node(data):
    return db.create(Node, type="data", data=data, leaf_index=get_leafs().count()+1)


def get_all_nodes_in_tree():
    nodes = []
    root_node = get_root_node()
    nodes.append(root_node)
    for v in get_all_nodes().all():
        if v in nodes:
            nodes.append(v.left)
            nodes.append(v.right)
    return nodes


def graphviz_tree(number, tree):
    s = []
    s.append("graph graphname {")
    s.append("labelloc=\"t\";")
    s.append(f"label=\"Nodes: {number}\";")
    for v in tree:
        if not v:
            continue
        if v.left:
            s.append(f"\"{v.get_name()}\" -- \"{v.left.get_name()}\";")
        if v.right:
            s.append(f"\"{v.get_name()}\" -- \"{v.right.get_name()}\";")
    s.append("}")
    return "\n".join(s)


def validate_chain(root, chain):
    chain = chain[:]
    s = chain.pop(0)[1]["hash"]
    for node in chain:
        h = hashlib.sha512()
        if node[0] == "LEFT":
            h.update(("level"+node[1]["hash"]+s).encode('utf-8'))
        if node[0] == "RIGHT":
            h.update(("level"+s+node[1]["hash"]).encode('utf-8'))
        s = h.hexdigest()
    return root["hash"] == s


