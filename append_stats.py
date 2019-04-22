import requests

def write_leaf(data):
    r = requests.post("http://172.17.0.2:5000/api/log/tree/append", json=data)
    x = r.headers["X-Duration"]
    r = requests.get("http://172.17.0.2:5000/api/log/tree/stats")
    j = r.json()
    return x, j

with open("stats.txt", "w") as stats, open("roots.txt", "w") as roots:
    stats.write("Number Duration Size Leafs Level Total\n")
    roots.write("Number Root Signature Leafs\n")
    for i in range(62314, 400000):
        data = {"name": "Name-{}".format(i),
                "data": "Datablock-{}".format(i)}
        duration, j = write_leaf(data)
        #stats.write(f"{i} {duration} {j['bytes used']} {j['leaf nodes']} {j['level nodes']} {j['total nodes']}\n")
        stats.write("{} {} {} {} {} {}\n".format(i, duration, j['bytes used'], j['leaf nodes'], j['level nodes'], j['total nodes']))
        stats.flush()

        root_node = j['root node']
        #stats.write(f"{i} {root_node['hash']} {root_node['signature']} {j['leaf nodes']}")
        roots.write("{} {} {} {}\n".format(i, root_node['hash'], root_node['signature'], j['leaf nodes']))
        roots.flush()
