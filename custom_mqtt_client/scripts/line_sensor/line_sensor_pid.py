import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read the CSV file
# Get the directory of the current script (where the script is located)
script_dir = Path(__file__).resolve().parent
# Define the relative file path
relative_path = '../../logs/line_follower.csv'
# Resolve the absolute path based on the script's location
absolute_path = script_dir / relative_path
data = pd.read_csv(absolute_path)

# Plot error over time
plt.figure(figsize=(10, 15))

plt.subplot(5, 1, 1)
plt.plot(data['timestamp_sec'], data['error'], marker='o', linestyle='-', color='b')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Error')
plt.title('Error Over Time')

# Position
plt.subplot(5, 1, 2)
plt.plot(data['timestamp_sec'], data['position'], marker='o', linestyle='-', color='y')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Position')
plt.title('Position Over Time')

# Plot Integral component over time
plt.subplot(5, 1, 3)
plt.plot(data['timestamp_sec'], data['i'], marker='o', linestyle='-', color='g')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Integral')
plt.title('Integral Component Over Time')

# Plot Derivative component over time
plt.subplot(5, 1, 4)
plt.plot(data['timestamp_sec'], data['d'], marker='o', linestyle='-', color='r')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Derivative')
plt.title('Derivative Component Over Time')

# Plot Control Output over time
plt.subplot(5, 1, 5)
plt.plot(data['timestamp_sec'], data['u'], marker='o', linestyle='-', color='c')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Control Output')
plt.title('Control Output Over Time')

plt.tight_layout()
# plt.show()
plt.savefig(script_dir / '../../logs/line_follower.png')