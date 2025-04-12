import os
import sys
sys.path.append(os.path.abspath("../.."))
from modules.camera.camera_service import camera_service
import time
import numpy as np
import cv2



script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
calibration_file = os.path.join(script_dir, "camera_calibration_data.npz")
if not os.path.exists(calibration_file):
    raise FileNotFoundError(f"Calibration file not found: {calibration_file}")

data = np.load(calibration_file)
mtx, dist = data["mtx"], data["dist"]


print(mtx)
print(dist)




input_checkboard_test = os.path.join(script_dir, "test_undistortion", "distorted_checkboard.jpg")
img = cv2.imread(input_checkboard_test)
h, w = img.shape[:2]
new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

# Undistort the image
undistorted_img = cv2.undistort(img, mtx, dist, None, new_camera_mtx)

# Save the undistorted image in the same directory
output_image_path = os.path.join(script_dir, "test_undistortion", "undistorted_checkboard_image.jpg")
cv2.imwrite(output_image_path, undistorted_img)
print(f"Undistorted checkboard image saved as: {output_image_path}")










# Initialize the camera
camera_service.setup(use_calibration=True)
time.sleep(3)  # Give it 3 seconds to start receiving frames

# Save the undistorted image in the same directory
output_image_path = os.path.join(script_dir, "test_undistortion", "undistorted_new_image.jpg")
cv2.imwrite(output_image_path, camera_service.last_frame)
print(f"Undistorted new image saved as: {output_image_path}")

exit()