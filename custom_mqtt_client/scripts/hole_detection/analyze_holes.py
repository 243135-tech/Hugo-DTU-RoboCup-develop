import os
import cv2
import sys
import numpy as np
from time import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service
from modules.camera.hole_detector import HoleDetector  # Adjust this import if needed

PICTURES_FOLDER = "pictures"

dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
calibration_file = os.path.join(dir, "camera_calibration_data.npz")
if not os.path.exists(calibration_file):
    raise FileNotFoundError(f"Calibration file not found: {calibration_file}")

data = np.load(calibration_file)
mtx, dist = data["mtx"], data["dist"]


# Initialize detector
detector = HoleDetector(mtx)

# Get all image files from the folder
image_files = sorted([
    f for f in os.listdir(PICTURES_FOLDER)
    if f.lower().endswith(('.png', '.jpg', '.jpeg'))
])

print(f"Found {len(image_files)} image(s) in '{PICTURES_FOLDER}'\n")

# Process each image
for i, filename in enumerate(image_files):
    image_path = os.path.join(PICTURES_FOLDER, filename)
    img = cv2.imread(image_path)

    if img is None:
        print(f"[{i+1}] ❌ Could not read image: {filename}")
        continue

    start_time = time()
    found, x, y, z, r, real_dist = detector.detect_golf_hole_contour(img)
    elapsed = time() - start_time

    print(f"[{i+1}] 📷 {filename}")
    if found:
        print(f"    ✅ Hole detected")
        print(f"    - Center (x, y): ({x:.2f}, {y:.2f})")
        print(f"    - Estimated distance z: {z:.2f} mm")
        print(f"    - Pixel radius: {r:.2f} px")
        print(f"    - Estimated real distance: {real_dist:.2f} mm")
    else:
        print(f"    ❌ No valid hole detected")
    print(f"    ⏱️ Processing time: {elapsed:.3f} s\n")
