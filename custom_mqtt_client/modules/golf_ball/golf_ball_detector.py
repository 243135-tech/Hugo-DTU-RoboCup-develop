import cv2
import numpy as np


class GolfBallDetector:
    # Orange
    LOWER_COLOR = np.array([5, 150, 150])
    UPPER_COLOR = np.array([15, 255, 255])
    # LOWER_COLOR = np.array([140, 100, 100])  # Lower bound for pink
    # UPPER_COLOR = np.array([170, 255, 255])  # Upper bound for pink

    MIN_AREA_THRESHOLD = 400
    MIN_RADIUS_THRESHOLD = 10
    MAX_RADIUS_THRESHOLD = 50
    BALL_DIAMETER_MM = 43


    def __init__(self, camera_matrix):
        self.f_x = camera_matrix[0, 0]
        self.f_y = camera_matrix[1, 1]


    def detected_to_real_distance(self, detected_distance_mm):
        """
        Linear mapping fitted with real-life measurements. See scripts/golf_ball
        """
        a, b = 0.8421456391462895, -48.58824500263063
        return a * detected_distance_mm + b


    def detect(self, img):
        """
        Detects the orange golf ball in the picture.
        Returns (result,x,y,z,radius,z_mm):
            - result:  whether the ball was detected or not
            - x,y:     position in pixel of the center of the ball in the picture
            - z:       distance of the ball from the robot (in pixel)
            - radius:  radius in pixel of the ball
            - z_mm:    distance of the ball from the robot (in mm)
        """

        # Convert the image to HSV for better color segmentation
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Create a mask that only includes orange color
        mask = cv2.inRange(hsv, self.LOWER_COLOR, self.UPPER_COLOR)

        # Apply the mask to the image
        cv2.bitwise_and(img, img, mask=mask)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Initialize the diameter as None
        for contour in contours:
            # If the contour is large enough (area threshold), we assume it's the golf ball
            area = cv2.contourArea(contour)

            if area > self.MIN_AREA_THRESHOLD:
                # Get the bounding circle around the contour
                (x, y), radius = cv2.minEnclosingCircle(contour)

                # If the radius is within a reasonable range for a 43mm ball, it might be the correct one
                if self.MIN_RADIUS_THRESHOLD < radius < self.MAX_RADIUS_THRESHOLD:  # Adjust based on expected size in pixels
                    # Calculate the distance to the ball (uses the focal length formula: f*x/d)
                    detected_z = (self.f_x * self.BALL_DIAMETER_MM) / (2 * radius)

                    return (True, x, y, detected_z, radius, self.detected_to_real_distance(detected_z))

        return (False,0,0,0,0,0)

    def is_ball_grabbed(self, image):
        """
        Checks if the ball is grabbed by detecting orange color in the region of interest.
        Returns 1 if at least 10% of the ROI contains the ball color, otherwise 0.
        """
    
        # Get the height and width of the image
        height, width = image.shape[:2]
    
        # Calculate the center point of the image
        center_x, center_y = width // 2, height // 2
    
        # Calculate the top-left and bottom-right corners of the rectangle
        rect_width, rect_height = 150, 75
        top_left = (center_x - rect_width // 2, center_y - rect_height // 2)
        bottom_right = (center_x + rect_width // 2, center_y + rect_height // 2)
    
        # Shift the rectangle down by 250 pixels and right by 15 pixels
        top_left = (top_left[0] + 15, top_left[1] + 250)
        bottom_right = (bottom_right[0] + 15, bottom_right[1] + 250)
    
        # Extract the region of interest using the coordinates
        roi = image[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        
        # Convert the ROI to HSV for color detection
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
        # Create a mask that only includes orange color
        mask = cv2.inRange(hsv_roi, self.LOWER_COLOR, self.UPPER_COLOR)
    
        # Calculate the percentage of orange pixels in the ROI
        total_pixels = (bottom_right[0] - top_left[0]) * (bottom_right[1] - top_left[1])
        orange_pixels = cv2.countNonZero(mask)
        orange_percentage = (orange_pixels / total_pixels) * 100
    
        # Return 1 if at least 10% of the ROI is orange
        return 1 if orange_percentage >= 10 else 0
        

    def draw_region_of_interest(image):
        """
        Draws a rectangle in the area that is grabbed by the robot arm.
        """
        # Get the height and width of the image
        height, width = image.shape[:2]

        # Calculate the center point of the image
        center_x, center_y = width // 2, height // 2

        # Calculate the top-left and bottom-right corners of the 200x200 rectangle
        # centered in the middle of the image
        rect_width, rect_height = 150, 75
        top_left = (center_x - rect_width // 2, center_y - rect_height // 2)
        bottom_right = (center_x + rect_width // 2, center_y + rect_height // 2)

        # Shift the rectangle down by 250 pixels and right by 50 pixels
        top_left = (top_left[0]+15, top_left[1] + 250)
        bottom_right = (bottom_right[0]+15, bottom_right[1] + 250)

        # Draw the rectangle
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

        # Add text indicating the rectangle size
        text = "Grabbed Region (100x75)"
        cv2.putText(image, text, 
                    (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return image, top_left[0], top_left[1], bottom_right[0], bottom_right[1]

        