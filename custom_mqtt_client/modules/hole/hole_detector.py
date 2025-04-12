import cv2
from time import time
from libs.logger import Logger
from libs.services.mqtt_service import mqtt_service


class HoleDetector:

    MIN_RADIUS_THRESHOLD = 15
    MAX_RADIUS_THRESHOLD = 60
    HOLE_DIAMETER_MM = 52
    MAX_THRESHOLD_BLACK = 60
    MIN_AREA_THRESH = 500

    def __init__(self, camera_matrix):

        self.f_x = camera_matrix[0, 0]
        self.f_y = camera_matrix[1, 1]

    def detected_to_real_distance(self, detected_z):
        #TODO change this params
        a, b = 0.8421456391462895, -48.58824500263063
        return a * detected_z + b


    def detect_golf_hole_contour(self, img):

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use a threshold to isolate dark regions (holes are usually dark)
        _, thresh = cv2.threshold(blurred, self.MAX_THRESHOLD_BLACK, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > self.MIN_AREA_THRESH:

                if len(cnt) >= 5:

                    ellipse = cv2.fitEllipse(cnt)
                    (x, y), (MA, ma), angle = ellipse  # MajorAxis, MinorAxis

                    # Estimate distance using the apparent diameter in pixels (average of MA and ma)
                    avg_diameter_px = (MA + ma) / 2
                    avg_radius_px = avg_diameter_px / 2

                    if self.MIN_RADIUS_THRESHOLD <= avg_radius_px <= self.MAX_RADIUS_THRESHOLD:
                        detected_z = (self.HOLE_DIAMETER_MM * self.f_x) / avg_diameter_px

                        return (True, x, y, detected_z, avg_radius_px, self.detected_to_real_distance(detected_z), MA, ma, angle)

        return (False, 0, 0, 0, 0, 0, 0, 0, 0)

        