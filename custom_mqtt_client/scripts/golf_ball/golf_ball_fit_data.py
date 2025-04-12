import numpy as np

# Real distances in cm (photo_* where * is the real distance)
real_distances = [19.5, 35, 45, 60, 75]

# Corresponding calculated distances in mm (z values from your data)
calculated_distances = [308.1136290705761, 467.92579141380236, 586.6277865220104, 
                        737.3374411317103, 973.0282154371762]

# Convert real distances to mm (for comparison)
real_distances_mm = [d * 10 for d in real_distances]  # Convert cm to mm

# Perform linear regression (find a, b for y = ax + b)
a, b = np.polyfit(calculated_distances, real_distances_mm, 1)


print(a, b)