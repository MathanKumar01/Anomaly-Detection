from ultralytics import YOLO


class PoseDetector:

    def __init__(self, model_path="yolo11n-pose.pt"):

        self.model = YOLO(model_path)

    def detect(self, frame):

        results = self.model(
            frame,
            verbose=False
        )

        return results