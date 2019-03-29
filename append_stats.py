import requests



def write_leaf(data):
    r = requests.post("http://127.0.0.1:5000/api/log/tree/append", json=data)
    x = r.headers["X-Duration"]
    r = requests.get("http://127.0.0.1:5000/api/log/tree/stats")
    j = r.json()
    return x, j

with open("stats.txt", "w") as stats, open("roots.txt", "w") as roots:
    stats.write("Number Duration Size Leafs Level Total\n")
    roots.write("Number Root Signature Leafs\n")
    for i in range(1, 400000):
        data = {"name": f"Name-{i}",
                "data": f"Datablock-{i}"}
        duration, j = write_leaf(data)
        stats.write(f"{i} {duration} {j['bytes used']} {j['leaf nodes']} {j['level nodes']} {j['total nodes']}\n")
        stats.flush()

        root_node = j['root node']
        stats.write(f"{i} {root_node['hash']} {root_node['signature']} {j['leaf nodes']}")
        stats.flush()

