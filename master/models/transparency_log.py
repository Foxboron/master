import hashlib
import math
from datetime import datetime
from collections import OrderedDict

from master.db import db
from .util import recurse

from sqlalchemy_utils import JSONType



class Node(db.Model):
    __tablename__ = "node"

    id = db.Column(
        db.Integer(), index=True, unique=True, primary_key=True, autoincrement=True
    )
    type = db.Column(db.String(10), nullable=False)
    hash = db.Column(db.String(128))
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data = db.Column(JSONType)
    height = db.Column(db.Integer(), default=1)

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
        return self.get_hash().hexdigest()[:10].upper()

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

    # def is_root(self):
    #     """ Root nodes should have no parent, but a right and left node """
    #     return self.parent is None and self.right and self.left

    def get_hash(self):
        if not self.hash:
            h = hashlib.sha512()
            h.update(self.type.encode('utf-8'))
            if self.data:
                for k, v in self.data.items():
                    h.update((k+v).encode('utf-8'))
            self.append_parents(h)
            self.hash = h.hexdigest()
            db.session.commit()
        return self.hash

    def recalc_hash(self):
        self.hash = hashlib.sha512()
        for k, v in self.data.items():
            self.hash.update((k+v).encode('utf-8'))
        self.append_parents()
        return self.hash

    def append_parents(self, h):
        if self.left:
            h.update(self.left.get_hash().encode('utf-8'))
        if self.right:
            h.update(self.right.get_hash().encode('utf-8'))
        return h

    @recurse
    def to_json(self, recurse=True):
        j = OrderedDict()
        j["id"] = self.id
        j["type"] = self.type
        j["created"] = self.created
        j["hash"] = self.get_hash()
        j["height"] = self.height
        j["right"] = ""
        j["left"] = ""
        j["parent"] = ""
        j["data"] = {}
        if self.get_child():
            j["parent"] = self.get_child().hash
        if self.right:
            j["right"] = self.right.get_hash()
        if self.left:
            j["left"] = self.left.get_hash()
        if self.data:
            j["data"] = self.data
        return j


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
        loose_leafs = loose_leafs - 2**int(math.log(loose_leafs, 2))
    subtrees.append(the_node)
    return subtrees


def append(data):
    if get_leafs().count() == 0:
        create_data_node(data)
        return
    subtrees = get_subtrees()
    new_node = create_data_node(data)
    for node in reversed(subtrees):
        new_parent = create_level_node(node, new_node)
        new_node = new_parent
        db.session.commit()
    return


def get_all_nodes_in_tree(self):
    nodes = []
    nodes.append(self.root_node.left)
    nodes.append(self.root_node.right)
    for v in reversed(self.table.values()):
        if v in nodes:
            nodes.append(v.left)
            nodes.append(v.right)
    return nodes


def create_level_node(left, right):
    if left is None:
        raise Exception("Left is None")
    if right is None:
        raise Exception("Right is None")
    return db.create(Node, type="level", right=right, left=left)


def create_data_node(data):
    return db.create(Node, type="data", data=data)

# def graphviz_tree(number, tree):
#     s = []
#     s.append("graph graphname {")
#     s.append("labelloc=\"t\";")
#     s.append(f"label=\"Nodes: {number}\";")
#     try:
#         s.append(f"\"{t.root_node.get_name()}\";")
#         s.append(f"\"{t.root_node.get_name()}\" -- \"{t.root_node.left.get_name()}\";")
#         s.append(f"\"{t.root_node.get_name()}\" -- \"{t.root_node.right.get_name()}\";")
#     except: pass
#     for v in tree:
#         if not v:
#             continue
#         if v:
#             s.append(f"\"{v.get_name()}\";")
#         if v.left:
#             s.append(f"\"{v.get_name()}\" -- \"{v.left.get_name()}\";")
#         if v.right:
#             s.append(f"\"{v.get_name()}\" -- \"{v.right.get_name()}\";")
#     s.append("}")
#     return "\n".join(s)

def validate_chain(root, chain):
    # Preload the requested node
    s = chain.pop(0)[1]["hash"]
    for node in chain:
        if node[0] == "LEFT":
            h = hashlib.sha512()
            h.update(("level"+node[1]["hash"]+s).encode('utf-8'))
            s = h.hexdigest()
        if node[0] == "RIGHT":
            h = hashlib.sha512()
            h.update(("level"+s+node[1]["hash"]).encode('utf-8'))
            s = h.hexdigest()
    return root.get_hash() == s


