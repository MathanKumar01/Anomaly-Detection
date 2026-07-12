from ultralytics import YOLO


class PoseDetector:

    def __init__(self):

        # YOLO11 Pose Model
        self.model = YOLO("yolo11n-pose.pt")

    def detect(self, frame):

        results = self.model(
            frame,
            verbose=False
        )

        return results