import sys
import pandas as pd
import matplotlib.pyplot as plt
data = pd.read_csv(sys.argv[1], sep=" ")

f = plt.figure()

data["Duration"].plot(label="Response time")
data["Duration"].rolling(700, min_periods=0).mean().plot(label="Mean over time")
plt.title("Response time")
plt.ylabel("Seconds")
plt.xlabel("Number of Entries")

plt.margins(0)
plt.legend()
plt.show()
f.savefig("foo.pdf", bbox_inches='tight')
