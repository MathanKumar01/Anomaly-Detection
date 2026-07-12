from ultralytics import YOLO

class ObjectDetector:

    def __init__(self, model_path):

        self.model = YOLO(model_path)

    def detect(self, frame):

        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        return results