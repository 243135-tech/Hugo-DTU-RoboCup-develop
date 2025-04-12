from threading import Thread
from libs.services.mqtt_service import mqtt_service
from flask import Flask, Response
import cv2


class LiveView:
    def __init__(self, camera_service):
        self.app = Flask(__name__)
        self.camera_service = camera_service
        self.thread = Thread(target=self.run)
        self.thread.start()

    def __del__(self):
        self.thread.join()


    def generate_frames(self):
        while True:
            if self.camera_service.live_view_img is not None:
                ret, buffer = cv2.imencode('.jpg', self.camera_service.live_view_img)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


    def video_feed(self):
        return Response(self.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


    def run(self):
        self.app.add_url_rule('/', 'live_view', self.video_feed)
        self.app.run(host='0.0.0.0', port=1337)
