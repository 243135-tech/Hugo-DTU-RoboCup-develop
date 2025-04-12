import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

data = np.load("camera_calibration_data.npz")
mtx, dist = data["mtx"], data["dist"]
f_x = mtx[0, 0]
f_y = mtx[1, 1]


MIN_AREA_THRESHOLD = 400
LOWER_ORANGE = np.array([5, 150, 150])
UPPER_ORANGE = np.array([15, 255, 255])
MIN_RADIUS_THRESHOLD = 10
MAX_RADIUS_THRESHOLD = 50
BALL_DIAMETER_MM = 43


def detect(img, img_name):
    ###############################
    result_img = img.copy()
    ###############################

    # Convert the image to HSV for better color segmentation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Create a mask that only includes orange color
    mask = cv2.inRange(hsv, LOWER_ORANGE, UPPER_ORANGE)

    ###############################
    # Display the mask
    plt.subplot(1, 2, 1)
    plt.imshow(mask, cmap='gray')
    plt.title('Mask')
    ###############################

    # Apply the mask to the image
    cv2.bitwise_and(img, img, mask=mask)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ###############################
    cv2.drawContours(result_img, contours, -1, (255, 0, 0), 2)
    ###############################

    # Initialize the diameter as None
    detected_z = None
    for contour in contours:
        # If the contour is large enough (area threshold), we assume it's the golf ball
        area = cv2.contourArea(contour)

        if area > MIN_AREA_THRESHOLD:  # Adjust this threshold based on expected size in pixels
            # Get the bounding circle around the contour
            (x, y), radius = cv2.minEnclosingCircle(contour)

            # If the radius is within a reasonable range for a 43mm ball, it might be the correct one
            if MIN_RADIUS_THRESHOLD < radius < MAX_RADIUS_THRESHOLD:  # Adjust based on expected size in pixels
                # Draw the detected ball
                cv2.circle(result_img, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                cv2.putText(result_img, "Golf Ball Detected", (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Calculate the distance to the ball (ball is 43mm, so do f*x/r)
                detected_z = (f_x * BALL_DIAMETER_MM) / (2 * radius)

    ############################################################################################
    # Display the processed image with contours and detected ball
    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Detected Ball (z={detected_z:.2f}mm)" if detected_z else "Ball Not Detected")
    plt.get_current_fig_manager().set_window_title(img_name)
    # plt.show()
    ############################################################################################

    return detected_z, img





if __name__ == "__main__":
    # Directory containing the images
    image_dir = "pictures/"

    # Loop through all files in the directory
    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img_path = os.path.join(image_dir, filename)
            img = cv2.imread(img_path)
            z, processed_img = detect(img, img_path)
            print(f"Processed {filename}: z = {z}")