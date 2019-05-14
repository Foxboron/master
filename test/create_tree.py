import os
import sys
import glob
import hashlib
import argparse

import requests

def get_stats():
    r = requests.get("http://127.0.0.1:5000/api/log/tree/stats")
    return r.json()

def write_raw_json(data):
    r = requests.post("http://127.0.0.1:5000/api/log/tree/append", json=data)
    return r.headers["X-Duration"], get_stats()

def submit_rebuild(buildinfo, metadata):
    files = {'metadata': open(metadata,'rb'),
            'buildinfo': open(buildinfo, 'rb')}
    r = requests.post("http://127.0.0.1:5000/api/rebuilder/submit", files=files)
    return r.headers["X-Duration"], get_stats()

def write_stats(i, duration, j):
    with open("stats.txt", "a") as stats:
        stats.write("{} {} {} {} {} {}\n".format(i, duration, j['bytes used'], j['leaf nodes'], j['level nodes'], j['total nodes']))
        stats.flush()

def write_roots(i, duration, j):
    with open("roots.txt", "a") as roots:
        root_node = j['root node']
        #stats.write(f"{i} {root_node['hash']} {root_node['signature']} {j['leaf nodes']}")
        roots.write("{} {} {} {}\n".format(i, root_node['hash'], root_node['signature'], j['leaf nodes']))
        roots.flush()

def write(i, duration, j):
    write_stats(i, duration, j)
    write_roots(i, duration, j)

# try:
#     requests.get("http://127.0.0.1:5000/", timeout=1)
# except:
#     print("No visualizer running")
#     sys.exit()

parser = argparse.ArgumentParser(description="My parser")
parser.add_argument('--append', metavar='N', type=int, help='an integer for the accumulator')
parser.add_argument('--buildinfo', type=str) 
parser.add_argument('--metadata', type=str) 
parser.add_argument('--pkgname', type=str) 
parser.add_argument('--version', type=str) 
parser.add_argument('--revoke', action='store_true')
parser.add_argument('--submit', action='store_true')
parser.add_argument('--submissions', action='store_true')
parser.add_argument('--new', action='store_true')
parser.add_argument('--test-consistency', action='store_true')
parser.add_argument('--test-inclusion', action='store_true')
parser.add_argument('--test-revoke', action='store_true')
args = parser.parse_args()

if args.submit and not (args.buildinfo and args.metadata):
    print("Missing files")
    sys.exit(1)

if args.submit:
    if not os.path.isfile(args.metadata):
        print("No such metadata file")
        sys.exit(1)
    if not os.path.isfile(args.buildinfo):
        print("No such buildinfo file")
        sys.exit(1)

if os.path.isfile('roots.txt') and os.path.isfile('stats.txt') and args.new:
    count = len(glob.glob1("./old_runs", "roots*"))+1
    if not os.path.isdir("old_runs"):
        os.mkdir("old_runs")
    os.rename('roots.txt', 'old_runs/roots_{}.txt'.format(count))
    os.rename('stats.txt', 'old_runs/stats_{}.txt'.format(count))

if not os.path.isfile('roots.txt') and not os.path.isfile('stats.txt'):
    with open("stats.txt", "w") as stats, open("roots.txt", "w") as roots:
        stats.write("Number Duration Size Leafs Level Total\n")
        roots.write("Number Root Signature Leafs\n")

if args.append:
    j = get_stats()
    num = j["leaf nodes"]
    append = num+args.append
    for i in range(num, append):
        data = {"name": "Name-{}".format(i),
                "data": "Datablock-{}".format(i)}
        duration, json = write_raw_json(data)
        write(i, duration, json)

if args.submit:
    duration, json = submit_rebuild(args.buildinfo, args.metadata) 
    i = json["leaf nodes"]-1
    write(i, duration, json)

if args.revoke:
    if not args.pkgname and not args.version:
        print("Missing pkgname and version")
        sys.exit(1)
    r = requests.get("http://127.0.0.1:5000/api/rebuilder/fetch/{}/{}".format(args.pkgname, args.version))
    j = r.json()
    if not j:
        print("No such rebuild")
        sys.exit(1)
    payload = {"hash": j[0]["hash"],
               "reason": "Testing"}
    r = requests.post("http://127.0.0.1:5000/api/rebuilder/revoke", json=payload)
    if r.status_code != 200:
        print(r.json())
        sys.exit(1)

if args.test_consistency:
    f = open("roots.txt", "r").read().split("\n")
    for line in f[1:]:
        if not line:
            continue
        _, hash, signature, count = line.split()
        print("Testing leaf count {}".format(count)) 
        r = requests.get("http://127.0.0.1:5000/api/log/tree/consistency/{}/{}".format(hash, count))
        if not r.json()["inclusion"]:
            print(count)
            print(r.json())
        if not r.json()["consistency"]:
            print(count)
            print(r.json())
        payload = {"hash": hash,
                   "signature": signature}
        r = requests.post("http://127.0.0.1:5000/api/crypto/verify", json=payload)
        if not r.json()["verified"]:
            print(count)
            print(r.json())

if args.test_inclusion:
    f = open("roots.txt", "r").read().split("\n")
    for line in f[1:]:
        if not line:
            continue
        _, hash, signature, count = line.split()
        print("Testing leaf count {}".format(count)) 
        r = requests.get("http://127.0.0.1:5000/api/log/tree/inclusion/{}/{}".format(hash, count))
        if not r.json()["inclusion"]:
            print(count)
            print(r)
        payload = {"hash": hash,
                   "signature": signature}
        r = requests.post("http://127.0.0.1:5000/api/crypto/verify", json=payload)
        if not r.json()["verified"]:
            print(count)
            print(r.json())

from os import walk
if args.submissions:
    packages = []
    for (dirpath, dirnames, filenames) in walk("submissions/"):
        if not dirpath.split("/")[-1]:
            continue
        metadata = dirpath+"/metadata"
        buildinfo = dirpath+"/buildinfo"
        duration, json = submit_rebuild(buildinfo, metadata) 
        i = json["leaf nodes"]-1
        write(i, duration, json)

if args.test_revoke:
    rebuilder = "http://127.0.0.1:5000"
    pkgname = "lostirc"
    version = "0.4.6-4.2"
    endpoint = "{}/api/rebuilder/fetch/{}/{}".format(rebuilder, pkgname, version)
    r = requests.get(endpoint)
    response = r.json()
    revoked = []
    for i in response:
        if i["hash"] in revoked:
            continue
        if i["data"]["type"] == "revoke":
            revoked.append(i["data"]["hash"])
            continue
        print(i["data"])
