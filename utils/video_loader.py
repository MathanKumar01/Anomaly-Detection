import cv2

class VideoLoader:

    def __init__(self, video_path):

        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise Exception("Unable to open video")

    def read(self):
        return self.cap.read()

    def release(self):
        self.cap.release()