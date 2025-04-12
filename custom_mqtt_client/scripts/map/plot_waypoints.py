
'''
Displays the map of waypoints
'''

import os
import sys
sys.path.append(os.path.abspath("../../"))
from modules.map.pure_pursuit import PurePursuit
import matplotlib.pyplot as plt
import matplotlib



pp = PurePursuit()
waypoints = pp.read_waypoints()


def is_headless():
    # Common way to detect headless environments
    return not os.environ.get("DISPLAY")

if is_headless():
    matplotlib.use('Agg')  # Non-interactive backend for headless
else:
    matplotlib.use('TkAgg')  # Interactive backend

plt.cla()

cx = []; cy = []
for point in waypoints:
    cx.append(float(point[0]))
    cy.append(float(point[1]))

plt.plot(cx, cy, "-r", label = "course")
plt.axis("equal")
plt.grid(True)
plt.title("Pure Pursuit Control")

if is_headless():
    plt.savefig("waypoints.png")
    print("Saved plot to plot.png (headless mode)")
else:
    plt.show()