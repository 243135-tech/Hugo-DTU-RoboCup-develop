from libs.camera import Camera
from libs.logger import Logger
from modules.golf_ball.golf_ball_detector import GolfBallDetector
from modules.hole.hole_detector import HoleDetector
from modules.camera.live_view import LiveView
import cv2
from datetime import datetime
import os
import numpy as np



class CameraService:
    SHOW_LIVE_VIEW = False

    live_view = None
    live_view_img = None
    setup_done = False
    ball = {'ok':False, 'x':0, 'y':0, 'z':0, 'radius':0, 'z_mm':0, 'is_ball_grabbed':False}
    hole = {'ok':False, 'x':0, 'y':0, 'z':0, 'radius':0, 'z_mm':0, 'MA':0, 'ma':0, 'angle':0}


    def __init__(self, uncalibrated=False):
        self.logger = Logger('camera_service')
        self.last_frame = None
        self.images_directory = "track_photos"
        self.aligned = False
        self.detecting_ball = False
        self.detecting_hole = False
        
        # Create directory for images if it doesn't exist
        if not os.path.exists(self.images_directory):
            os.makedirs(self.images_directory)

    
    def setup(self, use_calibration = True):
        self.use_calibration = use_calibration
        if self.use_calibration:
            # Ensure the file exists in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
            calibration_file = os.path.join(script_dir, "camera_calibration_data.npz")

            if not os.path.exists(calibration_file):
                raise FileNotFoundError(f"Calibration file not found: {calibration_file}")

            data = np.load(calibration_file)
            self.mtx, self.dist = data["mtx"], data["dist"]


        self.golf_ball_detector = GolfBallDetector(self.mtx)
        self.hole_detector = HoleDetector(self.mtx)
        self.camera = Camera(self.on_frame)

        if self.SHOW_LIVE_VIEW:
            self.live_view = LiveView(self)

        self.setup_done = True


    def set_golf_ball_detection(self, is_on=True):
        self.detecting_ball = is_on

    def set_hole_detection(self, is_on=True):
        self.detecting_hole = is_on

    def terminate(self):
        if self.live_view:
            del self.live_view

    
    def on_frame(self, frame):
        """
        This is called continuously in the __handle in a separate thread from libs/camera.py
        Stores the last frame
        """
        if not self.setup_done:
            return

        if self.use_calibration:
            h, w = frame.shape[:2]
            new_camera_mtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
            undistorted_img = cv2.undistort(frame, self.mtx, self.dist, None, new_camera_mtx) 
            x, y, w_roi, h_roi = roi
            undistorted_img_cropped = undistorted_img[y:y+h_roi, x:x+w_roi]
            self.last_frame = undistorted_img_cropped
        else:
            self.last_frame = frame

        if self.detecting_ball:
            
            self.ball['ok'], self.ball['x'], self.ball['y'], self.ball['z'], self.ball['radius'], self.ball['z_mm'] = self.golf_ball_detector.detect(self.last_frame)    
            self.ball['is_ball_grabbed'] = self.golf_ball_detector.is_ball_grabbed(self.last_frame)

            if self.SHOW_LIVE_VIEW:
                self.live_view_img = self.last_frame.copy()

                # Golf ball
                if self.ball['ok']:
                    cv2.circle(self.live_view_img, (int(self.ball['x']), int(self.ball['y'])), int(self.ball['radius']), (255, 0, 0), 2)
                    cv2.putText(self.live_view_img, f"z = {self.ball['z_mm']/10:.2f}cm", (int(self.ball['x']), int(self.ball['y']) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        if self.detecting_hole:

            self.hole['ok'], self.hole['x'], self.hole['y'], self.hole['z'], self.hole['radius'], self.hole['z_mm'], self.hole['MA'], self.hole['ma'], self.hole['angle'] = self.hole_detector.detect(self.last_frame)    
        
            if self.SHOW_LIVE_VIEW:
        
                self.live_view_img = self.last_frame.copy()

                # Golf ball
                if self.hole['ok']:
                    center = (int(self.hole['x']), int(self.hole['y']))
                    axes = (int(self.hole['MA'] / 2), int(self.hole['ma'] / 2))  # MA = major axis, ma = minor axis
                    angle = self.hole['angle']
                    cv2.ellipse(self.live_view_img, center, axes, angle, 0, 360, (0, 255, 0), 2)

                    # Optional: show distance info
                    cv2.putText(self.live_view_img, f"z = {self.hole['z_mm']/10:.2f}cm", 
                                (int(self.hole['x']), int(self.hole['y']) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)




    ###### UTILS #####

    def take_photo(self, filename=None):
        """
            Saves the last frame from the camera
            Images are saved with timestamp (or custom name) in the captured_images folder
            The function returns the path to the saved image.
        """

        if self.last_frame is None:
            self.logger.error("No frame available to capture")
            return None

        # Generate filename with timestamp if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"

        # Full path for the image
        image_path = os.path.join(self.images_directory, filename)
        
        # Save the image
        try:
            cv2.imwrite(image_path, self.last_frame)
            self.logger.info(f"Photo saved to {image_path}")
            return image_path
        except Exception as e:
            self.logger.error(f"Failed to save photo: {str(e)}")
            return None



camera_service = CameraService()