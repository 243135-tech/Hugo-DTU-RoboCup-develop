import cv2
import os
import matplotlib.pyplot as plt
from golf_ball_detect import detect


# Define the mapping function
def detected_to_real_distance(detected_distance_mm):
    a, b = 0.8421456391462895, -48.58824500263063
    return a * detected_distance_mm + b



if __name__ == "__main__":
    # Directory containing the images
    image_dir = "pictures/"

    # Loop through all files in the directory
    for filename in os.listdir(image_dir):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            img_path = os.path.join(image_dir, filename)
            img = cv2.imread(img_path)
            z, processed_img = detect(img, img_path)
            print(f"Processed {filename}: real z = {detected_to_real_distance(z):.2f}mm")