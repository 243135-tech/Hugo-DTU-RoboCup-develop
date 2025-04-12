import numpy as np
import cv2
import glob
import os

# Define checkerboard size (number of inner corners per row and column)
CHECKERBOARD = (11, 7)  # Adjust based on your checkerboard pattern

# Prepare object points (3D points in real-world space)
objp = np.zeros((CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

# Arrays to store object points and image points from all images
objpoints = []  # 3D points in real-world space
imgpoints = []  # 2D points in image plane

# Load all images
images = glob.glob("captured_images/*.jpg")  # Adjust extension if needed

# Create output folder for detected images
output_folder = "checkerboard_detected"
os.makedirs(output_folder, exist_ok=True)

# Clear folder
for filename in os.listdir(output_folder):
    file_path = os.path.join(output_folder, filename)
    if os.path.isfile(file_path):  
        os.remove(file_path)  # Delete only files

ok_counter = 0

for fname in images:
    print(f"[*] Image: {fname}")
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find checkerboard corners
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)

    if ret:
        print(f"    [+] Successfull")
        ok_counter += 1

        objpoints.append(objp)
        imgpoints.append(corners)

        # Draw detected corners
        img_with_corners = cv2.drawChessboardCorners(img, CHECKERBOARD, corners, ret)

        # Save the image with detected corners
        output_path = os.path.join(output_folder, os.path.basename(fname))
        cv2.imwrite(output_path, img_with_corners)

# Perform camera calibration
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# Save camera parameters
np.savez("camera_calibration_data.npz", mtx=mtx, dist=dist)

print("Camera Matrix:\n", mtx)
print("Distortion Coefficients:\n", dist)
print(f"Detected checkerboard images ({ok_counter}/{len(images)}) saved in: {output_folder}")
