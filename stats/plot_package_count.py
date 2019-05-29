import sys
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv(sys.argv[1], sep=" ")

f = plt.figure()

data["Leafs"].plot()
data["Level"].plot()
data["Total"].plot()
plt.margins(0)
plt.legend()
plt.show()
f.savefig("nodes_count_over_time.pdf", bbox_inches='tight')
