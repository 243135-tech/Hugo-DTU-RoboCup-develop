import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file, skipping lines that start with '#'
data = pd.read_csv('../logs/data_log.csv', comment='#', skipinitialspace=True)

# Plot x and y positions
plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
plt.plot(data['x'], data['y'], marker='o', linestyle='-', color='b')
plt.xlabel('X Position')
plt.ylabel('Y Position')
plt.title('XY Position')

# Plot line_pos
plt.subplot(1, 2, 2)
plt.plot(data['timestamp_sec'], data['line_pos'], marker='o', linestyle='-', color='r')
plt.xlabel('Timestamp (sec)')
plt.ylabel('Line Position')
plt.title('Line Position Over Time')

plt.tight_layout()
plt.show()