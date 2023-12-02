"""evs_per_write.py
buffer write statistics from wavedump
"""

import sys
import statistics as st

ff = sys.argv[-1]

counts = []
with open(ff, "r") as f:
    for line in f:
        if "writing" in line:
            counts.append(int(line.split(" ")[1]))

print(f"{st.median(counts):.0f} ({st.mean(counts):.0f} +/- {st.stdev(counts):.2f})")

